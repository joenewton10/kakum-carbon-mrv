# Kakum Forest Carbon MRV — Python workflow

## What this is
Porting the *analysis half* of a forest-carbon MRV project from Google Earth Engine
into a real Python geospatial workflow. GEE stays the pixel engine (classification done);
Python does area verification, carbon accounting, uncertainty, and charts.

## Where things stand
- GEE script is finished: 2023 Sentinel-2 → Random Forest forest/non-forest map,
  95.5% accuracy (seed 42), clipped to the official WDPA "Kakum" boundary.
- Exporting the classified raster from GEE as GeoTIFF in EPSG:32630 (UTM 30N),
  10m pixels, so area = (forest pixel count) x 100 m². File goes in ./data/.
- Python env built in .venv (Python 3.14). Installed: rasterio, numpy, pandas,
  matplotlib, pyyaml, tifffile. Pinned in requirements.txt.

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

## Known numbers to reproduce (from GEE)
- Forest area: ~18,800 ha (of 21,168 ha park)
- Above-ground stock: ~10.0 M tCO2e; incl. roots: ~12.5 M tCO2e
- IPCC Tier 1: AGB 310 t/ha (range 130–510), carbon fraction 0.47, C→CO2 44/12,
  root:shoot 0.24
- Combined uncertainty ~61.5% (area ~4.5% and biomass ~61% in quadrature)
- Conservative estimate (lower bound): ~4.8 M tCO2e

## Goal for the Python side
config.yaml (parameters) + a carbon_mrv module (rasterio/tifffile area calc +
carbon + uncertainty functions) + a runner that writes a results CSV and charts
(including a biomass sensitivity plot), + requirements.txt. Reproduce the GEE
numbers first, then extend.