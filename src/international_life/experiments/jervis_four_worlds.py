"""Matched-seed experiment for Jervis's four strategic worlds."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

import matplotlib.pyplot as plt

from international_life.jervis import (
    JervisParameters,
    history_metrics,
    initialize_jervis_world,
    run_jervis,
)


@dataclass(frozen=True, slots=True)
class StrategicWorld:
    slug: str
    label: str
    offense_advantage: float
    distinguishability: float


FOUR_WORLDS: tuple[StrategicWorld, ...] = (
    StrategicWorld(
        slug="offense_indistinguishable",
        label="Offense dominant / indistinguishable",
        offense_advantage=0.75,
        distinguishability=0.15,
    ),
    StrategicWorld(
        slug="defense_indistinguishable",
        label="Defense dominant / indistinguishable",
        offense_advantage=-0.75,
        distinguishability=0.15,
    ),
    StrategicWorld(
        slug="offense_distinguishable",
        label="Offense dominant / distinguishable",
        offense_advantage=0.75,
        distinguishability=0.85,
    ),
    StrategicWorld(
        slug="defense_distinguishable",
        label="Defense dominant / distinguishable",
        offense_advantage=-0.75,
        distinguishability=0.85,
    ),
)


def run_four_worlds(
    output_dir: Path,
    *,
    steps: int = 80,
    seeds: int = 12,
    shape: tuple[int, int] = (40, 40),
    offensive_share: float = 0.08,
) -> tuple[Path, Path]:
    """Run matched initial worlds and write run-level plus summary CSV files."""
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str | int | float]] = []

    for seed in range(seeds):
        initial = initialize_jervis_world(
            shape,
            seed=seed,
            offensive_share=offensive_share,
        )
        for strategic_world in FOUR_WORLDS:
            params = JervisParameters(
                offense_advantage=strategic_world.offense_advantage,
                distinguishability=strategic_world.distinguishability,
            )
            history = run_jervis(initial, params, steps=steps)
            metrics = history_metrics(history, params)
            rows.append(
                {
                    "world": strategic_world.slug,
                    "label": strategic_world.label,
                    "seed": seed,
                    "steps": steps,
                    "height": shape[0],
                    "width": shape[1],
                    "offense_advantage": strategic_world.offense_advantage,
                    "distinguishability": strategic_world.distinguishability,
                    **metrics,
                }
            )

    run_path = output_dir / "jervis_four_worlds_runs.csv"
    with run_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_world: dict[str, list[dict[str, str | int | float]]] = defaultdict(list)
    for row in rows:
        by_world[str(row["world"])].append(row)

    summary_rows: list[dict[str, str | float]] = []
    for strategic_world in FOUR_WORLDS:
        world_rows = by_world[strategic_world.slug]
        summary_rows.append(
            {
                "world": strategic_world.slug,
                "label": strategic_world.label,
                "final_mean_arms": fmean(float(row["final_mean_arms"]) for row in world_rows),
                "spiral_delta": fmean(float(row["spiral_delta"]) for row in world_rows),
                "mean_conflict_rate": fmean(
                    float(row["mean_conflict_rate"]) for row in world_rows
                ),
                "peak_conflict_rate": fmean(
                    float(row["peak_conflict_rate"]) for row in world_rows
                ),
            }
        )

    summary_path = output_dir / "jervis_four_worlds_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    _save_metric_plot(
        summary_rows,
        output_dir / "jervis_final_mean_arms.png",
        metric="final_mean_arms",
        title="Jervis four worlds: final mean arms",
        ylabel="mean arms / maximum arms",
    )
    _save_metric_plot(
        summary_rows,
        output_dir / "jervis_mean_conflict_rate.png",
        metric="mean_conflict_rate",
        title="Jervis four worlds: mean conflict initiation rate",
        ylabel="fraction of cells per generation",
    )
    return run_path, summary_path


def _save_metric_plot(
    rows: list[dict[str, str | float]],
    path: Path,
    *,
    metric: str,
    title: str,
    ylabel: str,
) -> None:
    labels = [str(row["label"]) for row in rows]
    values = [float(row[metric]) for row in rows]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(labels, values)
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", labelrotation=20)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)
