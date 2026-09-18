import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from carbon_mrv.carbon import carbon_stock_tco2e
from carbon_mrv.config import load_config
from carbon_mrv.raster import forest_area_ha
from carbon_mrv.uncertainty import (
    area_uncertainty_pct,
    biomass_uncertainty_pct,
    combined_uncertainty_pct,
    conservative_estimate_tco2e,
)

SUMMARY_CSV_COLUMNS = [
    "forest_area_ha", "park_total_area_ha", "pct_of_park_forested",
    "agb_used_t_ha", "carbon_aboveground_tC", "carbon_aboveground_tCO2e",
    "carbon_incl_roots_tC", "carbon_incl_roots_tCO2e",
    "area_uncertainty_pct", "biomass_uncertainty_pct", "combined_uncertainty_pct",
    "conservative_estimate_tCO2e",
]

SENSITIVITY_CSV_COLUMNS = ["agb_t_ha", "total_co2e_t"]


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


def write_summary_csv(config, summary):
    path = os.path.join(config.output_dir, "results_summary.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SUMMARY_CSV_COLUMNS)
        writer.writerow([summary[column] for column in SUMMARY_CSV_COLUMNS])
    return path


def write_sensitivity_csv(config, sensitivity_rows):
    path = os.path.join(config.output_dir, "biomass_sensitivity.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SENSITIVITY_CSV_COLUMNS)
        for agb, co2e in sensitivity_rows:
            writer.writerow([agb, co2e])
    return path


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
    ax.set_title("Kakum Forest Carbon Stock: Biomass Sensitivity")
    ax.legend()
    fig.tight_layout()

    path = os.path.join(config.output_dir, "sensitivity_plot.png")
    fig.savefig(path)
    plt.close(fig)
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

    summary_csv_path = write_summary_csv(config, summary)
    sensitivity_csv_path = write_sensitivity_csv(config, sensitivity_rows)
    chart_path = write_sensitivity_chart(config, sensitivity_rows)
    print(f"Wrote {summary_csv_path}")
    print(f"Wrote {sensitivity_csv_path}")
    print(f"Wrote {chart_path}")
    print(f"Forest area: {summary['forest_area_ha']:.2f} ha "
          f"({summary['pct_of_park_forested']:.1f}% of park)")
    print(f"Stock incl. roots: {summary['carbon_incl_roots_tCO2e']:,.0f} tCO2e")
    print(f"Conservative estimate: {summary['conservative_estimate_tCO2e']:,.0f} tCO2e")

    return summary, sensitivity_rows


if __name__ == "__main__":
    main()
