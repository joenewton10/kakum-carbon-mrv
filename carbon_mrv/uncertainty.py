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
