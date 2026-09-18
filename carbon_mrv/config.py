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
