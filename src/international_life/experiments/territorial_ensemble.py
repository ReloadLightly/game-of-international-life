"""Reproducible ensemble experiment for the M2 territorial substrate."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from statistics import fmean

import matplotlib.pyplot as plt

from international_life.territorial import (
    TerritorialParameters,
    initialize_territorial_world,
    run_territorial,
    territorial_metrics,
)
from international_life.visualization import save_territorial_map


def run_territorial_ensemble(
    output_dir: Path,
    *,
    steps: int = 60,
    seeds: int = 6,
    shape: tuple[int, int] = (24, 32),
    num_polities: int = 10,
    params: TerritorialParameters | None = None,
) -> tuple[Path, Path]:
    """Run matched M2 baselines and write full trajectories plus ensemble means."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    base_params = params or TerritorialParameters()

    rows: list[dict[str, int | float | str]] = []
    for seed in range(seeds):
        initial = initialize_territorial_world(
            shape,
            num_polities=num_polities,
            seed=seed,
        )
        run_params = replace(base_params, battle_seed=base_params.battle_seed + seed)
        history = run_territorial(initial, run_params, steps=steps)
        parameter_record = {
            f"param_{name}": value for name, value in asdict(run_params).items()
        }
        if seed == 0:
            save_territorial_map(
                history[0],
                output_dir / "territorial_initial_seed0.png",
                title="M2 territorial baseline: initial world",
            )
            save_territorial_map(
                history[-1],
                output_dir / "territorial_final_seed0.png",
                title=f"M2 territorial baseline: generation {steps}",
            )

        for world in history:
            rows.append(
                {
                    "seed": seed,
                    "steps": steps,
                    "height": shape[0],
                    "width": shape[1],
                    "initial_polities": num_polities,
                    **parameter_record,
                    **territorial_metrics(world),
                }
            )

    timeseries_path = output_dir / "territorial_timeseries.csv"
    with timeseries_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_generation: dict[int, list[dict[str, int | float | str]]] = defaultdict(list)
    for row in rows:
        by_generation[int(row["generation"])].append(row)

    metrics = (
        "state_count",
        "effective_powers",
        "largest_state_share",
        "largest_power_share",
        "border_edges",
        "battle_count",
        "conquests",
        "extinctions",
        "fragmentations",
    )
    summary_rows: list[dict[str, int | float]] = []
    for generation in sorted(by_generation):
        generation_rows = by_generation[generation]
        summary: dict[str, int | float] = {
            "generation": generation,
            "seeds": seeds,
        }
        for metric in metrics:
            summary[metric] = fmean(float(row[metric]) for row in generation_rows)
        summary_rows.append(summary)

    summary_path = output_dir / "territorial_ensemble_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    _save_line_plot(
        summary_rows,
        output_dir / "territorial_state_count.png",
        metric="state_count",
        title="M2 ensemble: mean number of territorial states",
        ylabel="states",
    )
    _save_line_plot(
        summary_rows,
        output_dir / "territorial_effective_powers.png",
        metric="effective_powers",
        title="M2 ensemble: capability-based effective number of powers",
        ylabel="effective powers (1 / HHI)",
    )
    _save_line_plot(
        summary_rows,
        output_dir / "territorial_conquests.png",
        metric="conquests",
        title="M2 ensemble: mean territorial transfers per generation",
        ylabel="conquered cells",
    )
    return timeseries_path, summary_path


def _save_line_plot(
    rows: list[dict[str, int | float]],
    path: Path,
    *,
    metric: str,
    title: str,
    ylabel: str,
) -> None:
    generations = [int(row["generation"]) for row in rows]
    values = [float(row[metric]) for row in rows]
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(generations, values)
    axis.set_title(title)
    axis.set_xlabel("generation")
    axis.set_ylabel(ylabel)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
