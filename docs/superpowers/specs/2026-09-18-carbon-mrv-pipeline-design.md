# Kakum Forest Carbon MRV — Python Pipeline Design

## Purpose

Port the analysis half of the Kakum forest-carbon MRV workflow from Google Earth
Engine into Python. GEE already produced the classified raster (2023 Sentinel-2,
Random Forest forest/non-forest, 95.5% accuracy, clipped to the WDPA "Kakum"
boundary, exported as GeoTIFF). This pipeline reads that raster and reproduces
the area, carbon stock, and uncertainty numbers that were computed in GEE, then
writes them to a results CSV plus a biomass sensitivity chart.

This is a personal analysis tool, not a service: correctness of the numbers
matters, operational robustness (retries, graceful degradation) does not.

## Success criteria

Running the pipeline against `data/kakum_classified.tif` reproduces, within
rounding tolerance, the numbers already known from the GEE run:

- Forest area: ~18,800 ha (of 21,168 ha park) — computed value from the actual
  raster is 18,817.45 ha (1,881,745 forest pixels × 100 m²)
- Above-ground carbon stock: ~10.0 M tCO2e (computed: ~10.05M)
- Stock including roots: ~12.5 M tCO2e (computed: ~12.47M)
- Area uncertainty: 4.5% (= 100 − classification accuracy)
- Biomass uncertainty: ~61.3% (= half the AGB range ÷ mean AGB)
- Combined uncertainty: ~61.5% (= area and biomass combined in quadrature)
- Conservative (lower-bound) estimate: ~4.8 M tCO2e (= stock incl. roots ×
  (1 − combined uncertainty))

## Input data

`data/kakum_classified.tif`: single-band `uint8` GeoTIFF, EPSG:32630 (UTM 30N),
10m pixels (1841×1865), values `{0, 1}` where `1 = forest`. No explicit nodata
value — pixels outside the WDPA park boundary were exported as `0`, so the
raster's rectangular extent (34,335 ha) is larger than the true park area
(21,168 ha). The park's true area is a known external constant (from the WDPA
boundary used in GEE), not something derivable from the raster, and must live
in config.

## Environment note

`rasterio` was initially blocked by Windows Smart App Control (evaluation
mode blocking unsigned/low-reputation compiled binaries broadly — it hit
numpy's own `numpy.random._generator.pyd` too, not just rasterio's GDAL DLLs).
Resolved by disabling Smart App Control (was in reversible "Evaluation" state).
`tifffile` remains installed as a documented emergency fallback in
`PROJECT_CONTEXT.md` but is not used by any code in this pipeline — with the
real blocker gone, a second raster-reading code path would be unnecessary
complexity.

## Architecture

```
kakum-carbon-mrv/
  config.yaml
  requirements.txt
  carbon_mrv/
    __init__.py
    config.py        # load + validate config.yaml -> dataclass
    raster.py         # read GeoTIFF, count forest pixels -> forest_area_ha (I/O)
    carbon.py          # pure functions: AGB -> carbon -> CO2e, incl. roots
    uncertainty.py      # pure functions: area/biomass/combined %, conservative bound
  run.py               # orchestrates the pipeline end to end
  tests/
    test_carbon.py
    test_uncertainty.py
  outputs/
    results.csv
    sensitivity_plot.png
```

`carbon.py` and `uncertainty.py` contain only pure functions (numbers in,
numbers out) — no file I/O — so they can be unit tested directly against the
known GEE numbers above. `raster.py` and `run.py` handle I/O and orchestration
and are not unit tested; correctness there is checked by running the pipeline
and comparing output numbers against the known figures.

## config.yaml schema

```yaml
raster:
  path: data/kakum_classified.tif
  forest_value: 1          # pixel value meaning "forest"

park:
  total_area_ha: 21168     # WDPA polygon area (external constant, not from raster)

biomass:
  agb_mean_t_ha: 310
  agb_min_t_ha: 130
  agb_max_t_ha: 510
  carbon_fraction: 0.47    # AGB -> carbon
  co2_to_c_ratio: 3.6667   # 44/12
  root_shoot_ratio: 0.24   # applied to AGB to get below-ground biomass

classification:
  accuracy_pct: 95.5       # area uncertainty = 100 - this

sensitivity:
  step_t_ha: 10             # AGB sweep resolution for the sensitivity table/chart

output:
  dir: outputs
```

All science parameters are required fields with no defaults — a missing key
raises at config-load time rather than silently using a wrong assumption.

## Data flow

1. `config.py` loads and validates `config.yaml` into a `Config` dataclass.
2. `raster.forest_area_ha(config)` opens the GeoTIFF with `rasterio`, reads
   band 1, counts pixels equal to `forest_value`, multiplies by pixel area
   (from the raster's own transform, not hardcoded) to get hectares.
3. `carbon.carbon_stock_tco2e(...)` computes above-ground and incl.-roots
   stock for the mean AGB, and again for each AGB value in the sensitivity
   sweep (`agb_min` to `agb_max` step `sensitivity.step_t_ha`).
4. `uncertainty.py` computes area uncertainty, biomass uncertainty, combined
   uncertainty (quadrature), and the conservative lower-bound estimate.
5. `run.py` assembles all of the above into the results table and:
   - writes `outputs/results.csv`
   - writes `outputs/sensitivity_plot.png`

## Key function signatures

```python
# carbon.py
def carbon_stock_tco2e(
    forest_area_ha: float,
    agb_t_ha: float,
    carbon_fraction: float,
    co2_to_c_ratio: float,
    root_shoot_ratio: float,
    include_roots: bool,
) -> float:
    """Biomass (AGB, plus below-ground biomass via root_shoot_ratio if
    include_roots) -> carbon (via carbon_fraction) -> CO2e (via co2_to_c_ratio)."""

# uncertainty.py
def area_uncertainty_pct(classification_accuracy_pct: float) -> float: ...
def biomass_uncertainty_pct(agb_min_t_ha: float, agb_max_t_ha: float, agb_mean_t_ha: float) -> float: ...
def combined_uncertainty_pct(area_pct: float, biomass_pct: float) -> float: ...  # sqrt(a^2 + b^2)
def conservative_estimate_tco2e(total_stock_tco2e: float, combined_uncertainty_pct: float) -> float: ...
```

`raster.py`:
```python
def forest_area_ha(raster_path: str, forest_value: int) -> float:
    """Opens the raster with rasterio, counts forest_value pixels, multiplies
    by the raster's own pixel area (from its transform)."""
```

## Error handling

No silent fallbacks or defensive defaults for science parameters. A missing
config key, an unreadable or missing GeoTIFF, or a raster with unexpected
pixel values (e.g. no pixels equal to `forest_value`) should raise with a
clear message rather than produce a plausible-looking wrong number.

## Testing

`tests/test_carbon.py` and `tests/test_uncertainty.py`, written test-first
(TDD), asserting against the known values in "Success criteria" above with a
small rounding tolerance. `raster.py` and `run.py` are not unit tested;
verified manually by running the pipeline and checking `outputs/results.csv`
against the same known values.

## Outputs

`outputs/results.csv`: rows with a `row_type` column distinguishing:
- `summary` (one row): forest_area_ha, park_total_area_ha, pct_of_park_forested,
  agb_used_t_ha, carbon stock above-ground (tC and tCO2e), carbon stock incl.
  roots (tC and tCO2e), area_uncertainty_pct, biomass_uncertainty_pct,
  combined_uncertainty_pct, conservative_estimate_tco2e
- `sensitivity` (one row per AGB step from `agb_min_t_ha` to `agb_max_t_ha`):
  agb_t_ha, total_co2e_t

`outputs/sensitivity_plot.png`: AGB (t/ha) on the x-axis, total CO2e (incl.
roots) on the y-axis, with a vertical line marking the mean AGB (310 t/ha)
used for the headline numbers.

## Out of scope (for this pass)

Per the stated goal ("reproduce the GEE numbers first, then extend"): no
additional charts beyond the sensitivity plot, no CLI argument parsing beyond
running `run.py` directly, no packaging/distribution concerns.
