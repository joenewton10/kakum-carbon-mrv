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
