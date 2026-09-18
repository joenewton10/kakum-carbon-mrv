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
