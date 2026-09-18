# Kakum Carbon MRV Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python pipeline that reads the classified Kakum forest GeoTIFF, computes forest area, carbon stock, and uncertainty, and writes a results CSV plus a biomass sensitivity chart — reproducing the known GEE numbers.

**Architecture:** A `carbon_mrv` package with pure, unit-tested math (`carbon.py`, `uncertainty.py`) separated from untested I/O (`raster.py`, `config.py`, `run.py`). `run.py` orchestrates: load config → read raster → compute stock/uncertainty → sweep AGB sensitivity → write CSV + chart.

**Tech Stack:** Python 3.14, rasterio 1.5.1, numpy 2.5.3, matplotlib 3.11.2, pyyaml 6.0.3, pytest (dev dependency, added in Task 1).

**Spec:** [docs/superpowers/specs/2026-09-18-carbon-mrv-pipeline-design.md](../specs/2026-09-18-carbon-mrv-pipeline-design.md)

## Global Constraints

- All commands run from the `kakum-carbon-mrv/` project root, using the project venv: `.venv\Scripts\python.exe` (Windows) — do not use a bare `python`/`pip`, always the venv's executable, to keep the environment isolated (established earlier in this project to avoid polluting the global Python install).
- `carbon.py` and `uncertainty.py` contain ONLY pure functions (numbers in, numbers out) — no file I/O, no config objects as parameters. This is what makes them unit-testable per the spec.
- No defensive defaults for science parameters. A missing config key must raise (a bare `KeyError` from dict access is sufficient — no custom validation layer).
- `raster.py`, `config.py`, and `run.py` are not unit tested (per spec) — verified by manual runs against the real data.
- Pixel area for the area calculation comes from the raster's own transform (`src.transform`), never hardcoded, so the code isn't silently wrong if a different-resolution raster is substituted later.
- CO2e → tC conversion in `run.py` is done by dividing by `config.co2_to_c_ratio` (algebraically equivalent to computing tC directly) rather than adding a second function to `carbon.py` — keeps `carbon.py`'s public surface to the one function defined in the spec.

---

### Task 1: Package scaffold + pytest

**Files:**
- Create: `carbon_mrv/__init__.py`
- Create: `tests/__init__.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: the `carbon_mrv` package (importable, empty) and a working `pytest` invocation, which every later task's test steps depend on.

- [ ] **Step 1: Create the package directories and empty `__init__.py` files**

Create `carbon_mrv/__init__.py`:
```python
```
(empty file — just marks `carbon_mrv` as a package)

Create `tests/__init__.py`:
```python
```
(empty file)

- [ ] **Step 2: Install pytest into the venv**

Run: `.venv\Scripts\python.exe -m pip install pytest`

- [ ] **Step 3: Pin the installed pytest version in requirements.txt**

Run: `.venv\Scripts\python.exe -m pip show pytest` and note the `Version:` line, then add a line `pytest==<that version>` to `requirements.txt` (append after the existing 6 lines).

- [ ] **Step 4: Verify pytest runs (with zero tests collected, since none exist yet)**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: `collected 0 items` and exit with no errors (not a failure — zero tests is expected at this point).

- [ ] **Step 5: Commit**

```bash
git add carbon_mrv/__init__.py tests/__init__.py requirements.txt
git commit -m "Scaffold carbon_mrv package and add pytest"
```

---

### Task 2: `carbon.py` — carbon stock calculation (TDD)

**Files:**
- Create: `carbon_mrv/carbon.py`
- Test: `tests/test_carbon.py`

**Interfaces:**
- Produces: `carbon_stock_tco2e(forest_area_ha, agb_t_ha, carbon_fraction, co2_to_c_ratio, root_shoot_ratio, include_roots) -> float`, used by Task 6 (`run.py`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_carbon.py`:
```python
import pytest

from carbon_mrv.carbon import carbon_stock_tco2e

# Reference scenario: the actual Kakum raster has 1,881,745 forest pixels at
# 10m resolution -> 18,817.45 ha. These expected values were computed
# independently from the same formula chain used to validate the design
# against the known GEE output (~10.0M tCO2e above-ground, ~12.5M incl. roots).
FOREST_AREA_HA = 18817.45
AGB_T_HA = 310
CARBON_FRACTION = 0.47
CO2_TO_C_RATIO = 44 / 12
ROOT_SHOOT_RATIO = 0.24


def test_carbon_stock_above_ground_only():
    result = carbon_stock_tco2e(
        forest_area_ha=FOREST_AREA_HA,
        agb_t_ha=AGB_T_HA,
        carbon_fraction=CARBON_FRACTION,
        co2_to_c_ratio=CO2_TO_C_RATIO,
        root_shoot_ratio=ROOT_SHOOT_RATIO,
        include_roots=False,
    )
    assert result == pytest.approx(10_052_909.04, rel=1e-6)


def test_carbon_stock_including_roots():
    result = carbon_stock_tco2e(
        forest_area_ha=FOREST_AREA_HA,
        agb_t_ha=AGB_T_HA,
        carbon_fraction=CARBON_FRACTION,
        co2_to_c_ratio=CO2_TO_C_RATIO,
        root_shoot_ratio=ROOT_SHOOT_RATIO,
        include_roots=True,
    )
    assert result == pytest.approx(12_465_607.21, rel=1e-6)


def test_including_roots_is_greater_than_above_ground_only():
    above_ground = carbon_stock_tco2e(
        forest_area_ha=FOREST_AREA_HA, agb_t_ha=AGB_T_HA,
        carbon_fraction=CARBON_FRACTION, co2_to_c_ratio=CO2_TO_C_RATIO,
        root_shoot_ratio=ROOT_SHOOT_RATIO, include_roots=False,
    )
    incl_roots = carbon_stock_tco2e(
        forest_area_ha=FOREST_AREA_HA, agb_t_ha=AGB_T_HA,
        carbon_fraction=CARBON_FRACTION, co2_to_c_ratio=CO2_TO_C_RATIO,
        root_shoot_ratio=ROOT_SHOOT_RATIO, include_roots=True,
    )
    assert incl_roots > above_ground


def test_zero_area_gives_zero_stock():
    result = carbon_stock_tco2e(
        forest_area_ha=0, agb_t_ha=AGB_T_HA,
        carbon_fraction=CARBON_FRACTION, co2_to_c_ratio=CO2_TO_C_RATIO,
        root_shoot_ratio=ROOT_SHOOT_RATIO, include_roots=True,
    )
    assert result == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_carbon.py -v`
Expected: FAIL / ERROR — `ModuleNotFoundError: No module named 'carbon_mrv.carbon'`

- [ ] **Step 3: Write the implementation**

Create `carbon_mrv/carbon.py`:
```python
def carbon_stock_tco2e(
    forest_area_ha: float,
    agb_t_ha: float,
    carbon_fraction: float,
    co2_to_c_ratio: float,
    root_shoot_ratio: float,
    include_roots: bool,
) -> float:
    """Total carbon stock in tCO2e for the given forest area and AGB.

    Above-ground biomass (AGB) totals forest_area_ha * agb_t_ha. When
    include_roots is True, below-ground biomass (AGB * root_shoot_ratio) is
    added before applying the carbon fraction. The result is converted from
    tonnes of carbon to tonnes of CO2-equivalent via co2_to_c_ratio (44/12).
    """
    agb_total_t = forest_area_ha * agb_t_ha
    if include_roots:
        biomass_total_t = agb_total_t * (1 + root_shoot_ratio)
    else:
        biomass_total_t = agb_total_t
    carbon_t = biomass_total_t * carbon_fraction
    return carbon_t * co2_to_c_ratio
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_carbon.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add carbon_mrv/carbon.py tests/test_carbon.py
git commit -m "Add carbon stock calculation with tests"
```

---

### Task 3: `uncertainty.py` — uncertainty calculations (TDD)

**Files:**
- Create: `carbon_mrv/uncertainty.py`
- Test: `tests/test_uncertainty.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `area_uncertainty_pct(classification_accuracy_pct) -> float`, `biomass_uncertainty_pct(agb_min_t_ha, agb_max_t_ha, agb_mean_t_ha) -> float`, `combined_uncertainty_pct(area_pct, biomass_pct) -> float`, `conservative_estimate_tco2e(total_stock_tco2e, combined_uncertainty_pct) -> float`. All used by Task 6 (`run.py`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_uncertainty.py`:
```python
import pytest

from carbon_mrv.uncertainty import (
    area_uncertainty_pct,
    biomass_uncertainty_pct,
    combined_uncertainty_pct,
    conservative_estimate_tco2e,
)


def test_area_uncertainty_is_100_minus_accuracy():
    assert area_uncertainty_pct(95.5) == pytest.approx(4.5)


def test_biomass_uncertainty_is_half_range_over_mean():
    # Kakum AGB range 130-510, mean 310 -> known GEE figure ~61.3%
    result = biomass_uncertainty_pct(agb_min_t_ha=130, agb_max_t_ha=510, agb_mean_t_ha=310)
    assert result == pytest.approx(61.29032258064516, rel=1e-6)


def test_combined_uncertainty_is_quadrature_sum():
    # Kakum figures: area 4.5%, biomass ~61.29% -> known GEE figure ~61.5%
    result = combined_uncertainty_pct(area_pct=4.5, biomass_pct=61.29032258064516)
    assert result == pytest.approx(61.455297916774775, rel=1e-6)


def test_combined_uncertainty_exceeds_either_component():
    result = combined_uncertainty_pct(area_pct=4.5, biomass_pct=61.29032258064516)
    assert result > 4.5
    assert result > 61.29032258064516


def test_conservative_estimate_reduces_stock_by_uncertainty():
    # Kakum figures: 12,465,607.21 tCO2e incl. roots, 61.455... % combined
    # uncertainty -> known GEE conservative estimate ~4.8M tCO2e
    result = conservative_estimate_tco2e(
        total_stock_tco2e=12_465_607.207533332,
        combined_uncertainty_pct=61.455297916774775,
    )
    assert result == pytest.approx(4_804_831.16, rel=1e-6)


def test_conservative_estimate_is_less_than_total():
    result = conservative_estimate_tco2e(total_stock_tco2e=1000, combined_uncertainty_pct=10)
    assert result < 1000
    assert result == pytest.approx(900)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_uncertainty.py -v`
Expected: FAIL / ERROR — `ModuleNotFoundError: No module named 'carbon_mrv.uncertainty'`

- [ ] **Step 3: Write the implementation**

Create `carbon_mrv/uncertainty.py`:
```python
import math


def area_uncertainty_pct(classification_accuracy_pct: float) -> float:
    """Area uncertainty as the classification error rate."""
    return 100.0 - classification_accuracy_pct


def biomass_uncertainty_pct(agb_min_t_ha: float, agb_max_t_ha: float, agb_mean_t_ha: float) -> float:
    """Biomass uncertainty as half the AGB range, relative to the mean AGB."""
    half_range = (agb_max_t_ha - agb_min_t_ha) / 2.0
    return half_range / agb_mean_t_ha * 100.0


def combined_uncertainty_pct(area_pct: float, biomass_pct: float) -> float:
    """Area and biomass uncertainty combined in quadrature."""
    return math.sqrt(area_pct ** 2 + biomass_pct ** 2)


def conservative_estimate_tco2e(total_stock_tco2e: float, combined_uncertainty_pct: float) -> float:
    """Lower-bound stock estimate: total stock reduced by the combined uncertainty."""
    return total_stock_tco2e * (1 - combined_uncertainty_pct / 100.0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_uncertainty.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add carbon_mrv/uncertainty.py tests/test_uncertainty.py
git commit -m "Add uncertainty calculations with tests"
```

---

### Task 4: `config.yaml` + `config.py` — configuration loading

**Files:**
- Create: `config.yaml`
- Create: `carbon_mrv/config.py`

**Interfaces:**
- Produces: `Config` dataclass with fields `raster_path, forest_value, park_total_area_ha, agb_mean_t_ha, agb_min_t_ha, agb_max_t_ha, carbon_fraction, co2_to_c_ratio, root_shoot_ratio, classification_accuracy_pct, sensitivity_step_t_ha, output_dir`, and `load_config(path: str) -> Config`. Used by Task 6 (`run.py`).

- [ ] **Step 1: Create `config.yaml`**

Create `config.yaml` (project root):
```yaml
raster:
  path: data/kakum_classified.tif
  forest_value: 1

park:
  total_area_ha: 21168

biomass:
  agb_mean_t_ha: 310
  agb_min_t_ha: 130
  agb_max_t_ha: 510
  carbon_fraction: 0.47
  co2_to_c_ratio: 3.6667
  root_shoot_ratio: 0.24

classification:
  accuracy_pct: 95.5

sensitivity:
  step_t_ha: 10

output:
  dir: outputs
```

- [ ] **Step 2: Write `config.py`**

Create `carbon_mrv/config.py`:
```python
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class Config:
    raster_path: str
    forest_value: int
    park_total_area_ha: float
    agb_mean_t_ha: float
    agb_min_t_ha: float
    agb_max_t_ha: float
    carbon_fraction: float
    co2_to_c_ratio: float
    root_shoot_ratio: float
    classification_accuracy_pct: float
    sensitivity_step_t_ha: float
    output_dir: str


def load_config(path: str) -> Config:
    """Load and validate config.yaml. Raises KeyError if a required field is
    missing -- there are no defaults for science parameters."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    return Config(
        raster_path=raw["raster"]["path"],
        forest_value=raw["raster"]["forest_value"],
        park_total_area_ha=raw["park"]["total_area_ha"],
        agb_mean_t_ha=raw["biomass"]["agb_mean_t_ha"],
        agb_min_t_ha=raw["biomass"]["agb_min_t_ha"],
        agb_max_t_ha=raw["biomass"]["agb_max_t_ha"],
        carbon_fraction=raw["biomass"]["carbon_fraction"],
        co2_to_c_ratio=raw["biomass"]["co2_to_c_ratio"],
        root_shoot_ratio=raw["biomass"]["root_shoot_ratio"],
        classification_accuracy_pct=raw["classification"]["accuracy_pct"],
        sensitivity_step_t_ha=raw["sensitivity"]["step_t_ha"],
        output_dir=raw["output"]["dir"],
    )
```

- [ ] **Step 3: Manually verify config loads correctly**

Run: `.venv\Scripts\python.exe -c "from carbon_mrv.config import load_config; c = load_config('config.yaml'); print(c)"`
Expected: prints a `Config(...)` with `agb_mean_t_ha=310`, `park_total_area_ha=21168`, etc. matching `config.yaml`.

- [ ] **Step 4: Manually verify a missing key raises**

Run: `.venv\Scripts\python.exe -c "
import yaml
with open('config.yaml') as f:
    raw = yaml.safe_load(f)
del raw['biomass']['agb_mean_t_ha']
with open('bad_config.yaml', 'w') as f:
    yaml.safe_dump(raw, f)
from carbon_mrv.config import load_config
load_config('bad_config.yaml')
"`
Expected: `KeyError: 'agb_mean_t_ha'` (confirms missing fields raise rather than silently defaulting). Then delete the temp file: `Remove-Item bad_config.yaml` (PowerShell) or `rm bad_config.yaml` (bash).

- [ ] **Step 5: Commit**

```bash
git add config.yaml carbon_mrv/config.py
git commit -m "Add config.yaml and config loader"
```

---

### Task 5: `raster.py` — forest area from the GeoTIFF

**Files:**
- Create: `carbon_mrv/raster.py`

**Interfaces:**
- Produces: `forest_area_ha(raster_path: str, forest_value: int) -> float`. Used by Task 6 (`run.py`).

- [ ] **Step 1: Write the implementation**

Create `carbon_mrv/raster.py`:
```python
import rasterio


def forest_area_ha(raster_path: str, forest_value: int) -> float:
    """Count pixels equal to forest_value and convert to hectares using the
    raster's own pixel size (from its transform) -- never hardcoded, so this
    stays correct if a different-resolution raster is substituted later."""
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        pixel_area_m2 = abs(src.transform.a * src.transform.e)
        forest_pixel_count = int((band == forest_value).sum())

    return forest_pixel_count * pixel_area_m2 / 10_000.0
```

- [ ] **Step 2: Manually verify against the real Kakum raster**

Run: `.venv\Scripts\python.exe -c "from carbon_mrv.raster import forest_area_ha; print(forest_area_ha('data/kakum_classified.tif', 1))"`
Expected: `18817.45` (matches the known ~18,800 ha GEE figure, and the exact value computed earlier from the raster's pixel counts).

- [ ] **Step 3: Commit**

```bash
git add carbon_mrv/raster.py
git commit -m "Add forest area calculation from GeoTIFF"
```

---

### Task 6: `run.py` — orchestration and results CSV

**Files:**
- Create: `run.py`

**Interfaces:**
- Consumes: `load_config` (Task 4), `forest_area_ha` (Task 5), `carbon_stock_tco2e` (Task 2), `area_uncertainty_pct`/`biomass_uncertainty_pct`/`combined_uncertainty_pct`/`conservative_estimate_tco2e` (Task 3).
- Produces: `outputs/results.csv`. `main()` also becomes the base that Task 7 extends with chart output.

- [ ] **Step 1: Write `run.py`**

Create `run.py` (project root):
```python
import csv
import os

from carbon_mrv.carbon import carbon_stock_tco2e
from carbon_mrv.config import load_config
from carbon_mrv.raster import forest_area_ha
from carbon_mrv.uncertainty import (
    area_uncertainty_pct,
    biomass_uncertainty_pct,
    combined_uncertainty_pct,
    conservative_estimate_tco2e,
)

CSV_COLUMNS = [
    "row_type", "forest_area_ha", "park_total_area_ha", "pct_of_park_forested",
    "agb_used_t_ha", "carbon_aboveground_tC", "carbon_aboveground_tCO2e",
    "carbon_incl_roots_tC", "carbon_incl_roots_tCO2e",
    "area_uncertainty_pct", "biomass_uncertainty_pct", "combined_uncertainty_pct",
    "conservative_estimate_tCO2e", "agb_t_ha", "total_co2e_t",
]


def compute_sensitivity_rows(config, area_ha):
    rows = []
    agb = config.agb_min_t_ha
    while agb <= config.agb_max_t_ha + 1e-9:
        co2e = carbon_stock_tco2e(
            area_ha, agb, config.carbon_fraction,
            config.co2_to_c_ratio, config.root_shoot_ratio, include_roots=True,
        )
        rows.append((agb, co2e))
        agb += config.sensitivity_step_t_ha
    return rows


def write_results_csv(config, summary, sensitivity_rows):
    path = os.path.join(config.output_dir, "results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerow([
            "summary", summary["forest_area_ha"], summary["park_total_area_ha"],
            summary["pct_of_park_forested"], summary["agb_used_t_ha"],
            summary["carbon_aboveground_tC"], summary["carbon_aboveground_tCO2e"],
            summary["carbon_incl_roots_tC"], summary["carbon_incl_roots_tCO2e"],
            summary["area_uncertainty_pct"], summary["biomass_uncertainty_pct"],
            summary["combined_uncertainty_pct"], summary["conservative_estimate_tCO2e"],
            "", "",
        ])
        for agb, co2e in sensitivity_rows:
            writer.writerow([
                "sensitivity", "", "", "", "", "", "", "", "", "", "", "", "",
                agb, co2e,
            ])
    return path


def build_summary(config, area_ha):
    co2e_aboveground = carbon_stock_tco2e(
        area_ha, config.agb_mean_t_ha, config.carbon_fraction,
        config.co2_to_c_ratio, config.root_shoot_ratio, include_roots=False,
    )
    co2e_incl_roots = carbon_stock_tco2e(
        area_ha, config.agb_mean_t_ha, config.carbon_fraction,
        config.co2_to_c_ratio, config.root_shoot_ratio, include_roots=True,
    )
    area_pct = area_uncertainty_pct(config.classification_accuracy_pct)
    biomass_pct = biomass_uncertainty_pct(
        config.agb_min_t_ha, config.agb_max_t_ha, config.agb_mean_t_ha
    )
    combined_pct = combined_uncertainty_pct(area_pct, biomass_pct)

    return {
        "forest_area_ha": area_ha,
        "park_total_area_ha": config.park_total_area_ha,
        "pct_of_park_forested": area_ha / config.park_total_area_ha * 100.0,
        "agb_used_t_ha": config.agb_mean_t_ha,
        "carbon_aboveground_tC": co2e_aboveground / config.co2_to_c_ratio,
        "carbon_aboveground_tCO2e": co2e_aboveground,
        "carbon_incl_roots_tC": co2e_incl_roots / config.co2_to_c_ratio,
        "carbon_incl_roots_tCO2e": co2e_incl_roots,
        "area_uncertainty_pct": area_pct,
        "biomass_uncertainty_pct": biomass_pct,
        "combined_uncertainty_pct": combined_pct,
        "conservative_estimate_tCO2e": conservative_estimate_tco2e(co2e_incl_roots, combined_pct),
    }


def main():
    config = load_config("config.yaml")
    os.makedirs(config.output_dir, exist_ok=True)

    area_ha = forest_area_ha(config.raster_path, config.forest_value)
    summary = build_summary(config, area_ha)
    sensitivity_rows = compute_sensitivity_rows(config, area_ha)

    csv_path = write_results_csv(config, summary, sensitivity_rows)
    print(f"Wrote {csv_path}")
    print(f"Forest area: {summary['forest_area_ha']:.2f} ha "
          f"({summary['pct_of_park_forested']:.1f}% of park)")
    print(f"Stock incl. roots: {summary['carbon_incl_roots_tCO2e']:,.0f} tCO2e")
    print(f"Conservative estimate: {summary['conservative_estimate_tCO2e']:,.0f} tCO2e")

    return summary, sensitivity_rows


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and verify the CSV against the known GEE numbers**

Run: `.venv\Scripts\python.exe run.py`
Expected console output: forest area ≈ 18817.45 ha (88.9% of park), stock incl. roots ≈ 12,465,607 tCO2e, conservative estimate ≈ 4,804,831 tCO2e.

Run: `.venv\Scripts\python.exe -c "
import csv
with open('outputs/results.csv') as f:
    rows = list(csv.DictReader(f))
summary = rows[0]
print('row_type:', summary['row_type'])
print('forest_area_ha:', summary['forest_area_ha'])
print('carbon_aboveground_tCO2e:', summary['carbon_aboveground_tCO2e'])
print('carbon_incl_roots_tCO2e:', summary['carbon_incl_roots_tCO2e'])
print('combined_uncertainty_pct:', summary['combined_uncertainty_pct'])
print('conservative_estimate_tCO2e:', summary['conservative_estimate_tCO2e'])
print('sensitivity rows:', sum(1 for r in rows if r['row_type'] == 'sensitivity'))
"`
Expected: `forest_area_ha` ≈ 18817.45, `carbon_aboveground_tCO2e` ≈ 10052909 (matches known ~10.0M), `carbon_incl_roots_tCO2e` ≈ 12465607 (matches known ~12.5M), `combined_uncertainty_pct` ≈ 61.46 (matches known ~61.5%), `conservative_estimate_tCO2e` ≈ 4804831 (matches known ~4.8M), sensitivity rows: 39.

- [ ] **Step 3: Commit**

```bash
git add run.py outputs/results.csv
git commit -m "Add run.py orchestration and results CSV output"
```

---

### Task 7: Sensitivity chart

**Files:**
- Modify: `run.py`

**Interfaces:**
- Consumes: `sensitivity_rows` and `config` from `main()` (Task 6).
- Produces: `outputs/sensitivity_plot.png`.

- [ ] **Step 1: Add the chart-writing function and wire it into `main()`**

In `run.py`, add near the top (after the existing imports):
```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

Add this function (after `write_results_csv`, before `build_summary`):
```python
def write_sensitivity_chart(config, sensitivity_rows):
    agb_values = [row[0] for row in sensitivity_rows]
    co2e_values = [row[1] for row in sensitivity_rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(agb_values, co2e_values, marker="o")
    ax.axvline(
        config.agb_mean_t_ha, color="red", linestyle="--",
        label=f"Mean AGB ({config.agb_mean_t_ha} t/ha)",
    )
    ax.set_xlabel("AGB (t/ha)")
    ax.set_ylabel("Total carbon stock incl. roots (tCO2e)")
    ax.set_title("Kakum Forest Carbon Stock — Biomass Sensitivity")
    ax.legend()
    fig.tight_layout()

    path = os.path.join(config.output_dir, "sensitivity_plot.png")
    fig.savefig(path)
    plt.close(fig)
    return path
```

In `main()`, replace:
```python
    csv_path = write_results_csv(config, summary, sensitivity_rows)
    print(f"Wrote {csv_path}")
```
with:
```python
    csv_path = write_results_csv(config, summary, sensitivity_rows)
    chart_path = write_sensitivity_chart(config, sensitivity_rows)
    print(f"Wrote {csv_path}")
    print(f"Wrote {chart_path}")
```

- [ ] **Step 2: Run it and verify the chart was produced**

Run: `.venv\Scripts\python.exe run.py`
Expected: console prints `Wrote outputs/sensitivity_plot.png` in addition to the CSV line.

Run: `.venv\Scripts\python.exe -c "import os; print(os.path.getsize('outputs/sensitivity_plot.png'))"`
Expected: a nonzero byte count (a real PNG was written, e.g. tens of KB).

- [ ] **Step 3: Commit**

```bash
git add run.py outputs/sensitivity_plot.png
git commit -m "Add biomass sensitivity chart"
```

---

### Task 8: Final verification and PROJECT_CONTEXT.md update

**Files:**
- Modify: `PROJECT_CONTEXT.md`

**Interfaces:**
- Consumes: the full pipeline (Tasks 1-7).
- Produces: nothing new — this task confirms the whole pipeline together and records that in the project's running context doc.

- [ ] **Step 1: Run the full test suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 10 passed (4 from `test_carbon.py`, 6 from `test_uncertainty.py`), 0 failed.

- [ ] **Step 2: Run the full pipeline end to end from a clean `outputs/`**

Run: `Remove-Item outputs\* -Force` (clear any prior run's outputs)
Run: `.venv\Scripts\python.exe run.py`
Expected: both `outputs/results.csv` and `outputs/sensitivity_plot.png` exist afterward, with the same figures verified in Task 6/7 (forest area ≈ 18,817 ha, stock incl. roots ≈ 12.47M tCO2e, conservative estimate ≈ 4.80M tCO2e).

- [ ] **Step 3: Update `PROJECT_CONTEXT.md`**

Add a new section after "## Goal for the Python side" (replacing it, since the goal is now met):
```markdown
## Goal for the Python side (done)
config.yaml + carbon_mrv module (raster/carbon/uncertainty) + run.py + tests
are all in place (see docs/superpowers/plans/2026-09-18-carbon-mrv-pipeline.md
for the implementation plan). Running `run.py` reproduces the known GEE
numbers: forest area ~18,817 ha, stock incl. roots ~12.47M tCO2e, combined
uncertainty ~61.5%, conservative estimate ~4.80M tCO2e. Outputs land in
outputs/results.csv and outputs/sensitivity_plot.png.

Next: extend beyond reproducing the GEE numbers (scope TBD with the user).
```

- [ ] **Step 4: Commit**

```bash
git add PROJECT_CONTEXT.md
git commit -m "Update PROJECT_CONTEXT.md: pipeline reproduces known GEE numbers"
```
