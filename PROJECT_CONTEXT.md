# Kakum Forest Carbon MRV — Python workflow

## What this is
Porting the *analysis half* of a forest-carbon MRV project from Google Earth Engine
into a real Python geospatial workflow. GEE stays the pixel engine (classification
done); Python does area verification, carbon accounting, uncertainty, and charts.

## Where things stand
- GEE script is finished: 2023 Sentinel-2 → Random Forest forest/non-forest map,
  95.5% accuracy (seed 42), clipped to the official WDPA "Kakum" boundary.
- Exporting the classified raster from GEE as GeoTIFF in EPSG:32630 (UTM 30N),
  10 m pixels, so area = (forest pixel count) × 100 m². File goes in ./data/.
- Python env built in .venv (Python 3.14). Installed: rasterio, numpy, pandas,
  matplotlib, pyyaml, tifffile, pytest. Pinned in requirements.txt.

## Blocker hit (resolved)
`import rasterio` failed with "An Application Control policy has blocked this file".
Root cause turned out broader than first thought: Windows Smart App Control (SAC)
was blocking unsigned/low-reputation compiled binaries in general — confirmed via
the CodeIntegrity Operational event log, which showed it also blocking numpy's own
`numpy.random._generator.pyd`, not just rasterio's bundled GDAL DLLs. SAC was in
"Evaluation" state (registry: HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy\
VerifiedAndReputablePolicyState = 1), not the irreversible "On" state, so disabling
it via Settings > Privacy & security > Windows Security > App & browser control >
Smart App Control settings was a normal, reversible toggle — not the irreversible
step originally assumed. Toggled off, took effect without a reboot. All imports
(rasterio, numpy, pandas, matplotlib, pyyaml, tifffile) now confirmed working.
Kept tifffile installed too since it's a useful pure-Python fallback for reading
the GeoTIFF if needed.

## Known numbers to reproduce (from GEE, Tier 1)
- Forest area: ~18,800 ha (of 21,168 ha park)
- Above-ground stock: ~10.0 M tCO2e; incl. roots: ~12.5 M tCO2e
- IPCC Tier 1: AGB 310 t/ha (range 130–510), carbon fraction 0.47, C→CO2 44/12,
  root:shoot 0.24
- Combined uncertainty ~61.5% (area ~4.5% and biomass ~61% in quadrature)
- Conservative estimate (lower bound): ~4.8 M tCO2e

## Goal for the Python side (Tier 1, done)
config.yaml + carbon_mrv module (raster/carbon/uncertainty) + run.py + tests
are all in place. Running `run.py` reproduces the known GEE
numbers: forest area ~18,817 ha, stock incl. roots ~12.47M tCO2e, combined
uncertainty ~61.5%, conservative estimate ~4.80M tCO2e. Outputs land in
outputs/results_summary.csv (one row of headline metrics),
outputs/biomass_sensitivity.csv (the AGB sweep table), and
outputs/sensitivity_plot.png.

`run.py` loads `config.yaml` via a bare relative path, so it must be run
from the project root, using the venv's Python: `.venv\Scripts\python.exe run.py`
(Windows).

---

## Phase 2 — Tier 2 biomass (GEDI), planned upgrade

Do this *after* the Tier 1 Python pipeline reproduces the GEE numbers end to end.
Rationale: the uncertainty analysis showed biomass is ~61% of the error budget and
the classification only ~4.5%, so replacing the single Tier 1 default (310 t/ha)
with site-specific biomass is the highest-value improvement — far more than any
tweak to the classifier.

Narrative this creates (strong for a CV / interview):
"Started with IPCC Tier 1 defaults, used an uncertainty analysis to show biomass
dominated the error, then upgraded to GEDI-derived Tier 2 biomass specific to the
park." It shows diagnosis, not just tool-running.

### What GEDI gives you
GEDI is NASA spaceborne lidar. Two products matter:
- **L4A — footprint above-ground biomass density (AGBD), in Mg/ha (= t/ha)**, per
  ~25 m footprint. Site-specific but sparse: scattered shots with gaps, not a
  wall-to-wall map. This is the genuine Tier 2 input.
- **L4B — gridded mean AGBD at 1 km.** Coarser, already modelled/gap-filled.
  Simpler if you just want a park-mean biomass to swap in for the 310 default.

Both are in the Earth Engine catalog. Confirm the current asset IDs in the EE Data
Catalog before using (IDs get versioned) — as of last check they were roughly:
- L4A: `LARSE/GEDI/GEDI04_A_002_MONTHLY` (band `agbd`; quality bands too)
- L4B: `LARSE/GEDI/GEDI04_B_002`

### How it slots into the carbon calc
The clean approach for a first Tier 2 pass:
1. Load GEDI L4A over the park boundary.
2. Filter to good shots: keep `l4_quality_flag == 1` and `degrade_flag == 0`
   (drop low-quality / degraded-orbit footprints). This step matters — unfiltered
   GEDI is noisy.
3. Reduce the surviving `agbd` values to a **mean (and standard deviation)** inside
   the forest area of the park. That mean AGBD replaces the 310 t/ha default.
4. Feed that measured AGBD through the *same* chain you already built:
   AGBD → ×(1+root:shoot) → ×0.47 → ×44/12 → × forest hectares.
5. For uncertainty, swap the ±61% Tier 1 biomass range for GEDI's own spread
   (e.g. standard error of the mean AGBD, or the footprint SD). This is what
   *narrows* the error bar — the whole point.

Reality checks to keep honest:
- The GEDI mean may come back **higher or lower than 310**, so the headline carbon
  number can move in either direction. That's expected; it's a finding, not a bug.
- GEDI has its own uncertainty, so Tier 2 gives a **narrower but still real** range,
  not a precise point. "Narrower and measured" beats "wide and defaulted."
- GEDI coverage over one small park can be thin. If shot count is low, note it as a
  limitation, or consider L4B (1 km gridded) as the simpler park-mean route.

### Suggested files when you get here
- Add a `gedi_biomass.js` GEE snippet (or a Python `ee` call) that exports the
  filtered mean/SD AGBD for the park.
- Extend `config.yaml` with a `biomass_source: tier1 | tier2` switch so both
  versions run from the same code and can be compared side by side.