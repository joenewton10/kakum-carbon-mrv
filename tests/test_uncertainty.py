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
