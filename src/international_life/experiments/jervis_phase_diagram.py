"""Parameter sweep over offense advantage and distinguishability."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import fmean

import matplotlib.pyplot as plt
import numpy as np

from international_life.jervis import (
    JervisParameters,
    history_metrics,
    initialize_jervis_world,
    run_jervis,
)


def run_phase_diagram(
    output_dir: Path,
    *,
    steps: int = 60,
    seeds: int = 6,
    points: int = 9,
    shape: tuple[int, int] = (32, 32),
) -> Path:
    """Sweep both Jervis dimensions and save data plus one heatmap per metric."""
    if points < 2:
        raise ValueError("points must be at least 2")
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    output_dir.mkdir(parents=True, exist_ok=True)

    offense_values = np.linspace(-1.0, 1.0, points)
    distinguishability_values = np.linspace(0.0, 1.0, points)
    arms_surface = np.zeros((points, points), dtype=float)
    conflict_surface = np.zeros((points, points), dtype=float)
    rows: list[dict[str, float | int]] = []

    initials = [initialize_jervis_world(shape, seed=seed) for seed in range(seeds)]
    for row_index, distinguishability in enumerate(distinguishability_values):
        for col_index, offense_advantage in enumerate(offense_values):
            run_metrics = []
            for initial in initials:
                params = JervisParameters(
                    offense_advantage=float(offense_advantage),
                    distinguishability=float(distinguishability),
                )
                history = run_jervis(initial, params, steps=steps)
                run_metrics.append(history_metrics(history, params))
            final_arms = fmean(metric["final_mean_arms"] for metric in run_metrics)
            conflict_rate = fmean(metric["mean_conflict_rate"] for metric in run_metrics)
            arms_surface[row_index, col_index] = final_arms
            conflict_surface[row_index, col_index] = conflict_rate
            rows.append(
                {
                    "offense_advantage": float(offense_advantage),
                    "distinguishability": float(distinguishability),
                    "final_mean_arms": final_arms,
                    "mean_conflict_rate": conflict_rate,
                    "steps": steps,
                    "seeds": seeds,
                }
            )

    csv_path = output_dir / "jervis_phase_diagram.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    _save_heatmap(
        arms_surface,
        offense_values,
        distinguishability_values,
        output_dir / "jervis_phase_final_arms.png",
        title="Final mean arms",
    )
    _save_heatmap(
        conflict_surface,
        offense_values,
        distinguishability_values,
        output_dir / "jervis_phase_conflict.png",
        title="Mean conflict initiation rate",
    )
    return csv_path


def _save_heatmap(
    surface: np.ndarray,
    offense_values: np.ndarray,
    distinguishability_values: np.ndarray,
    path: Path,
    *,
    title: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(
        surface,
        origin="lower",
        aspect="auto",
        extent=(
            float(offense_values.min()),
            float(offense_values.max()),
            float(distinguishability_values.min()),
            float(distinguishability_values.max()),
        ),
    )
    axis.set_title(title)
    axis.set_xlabel("offense advantage (-1 defense, +1 offense)")
    axis.set_ylabel("offense-defense distinguishability")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
