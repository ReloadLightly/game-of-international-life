"""M4 matched comparison of binding and flexible alliance doctrines."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from statistics import fmean

import matplotlib.pyplot as plt
import numpy as np

from international_life._alliances.measures import alliance_edges, alliance_metrics
from international_life._alliances.types import (
    AllianceDoctrine,
    AllianceWorld,
    PolarityRegime,
    ThreatRegime,
)
from international_life._territorial.measures import alive_polities
from international_life._territorial.types import TerritorialParameters
from international_life.alliances import (
    alliance_world_fingerprint,
    doctrine_for,
    initialize_alliance_world,
    run_alliance,
)

_POLARITY_REGIMES: tuple[PolarityRegime, ...] = ("bipolar", "multipolar")
_THREAT_REGIMES: tuple[ThreatRegime, ...] = ("concentrated", "diffuse")
_DOCTRINE_NAMES = ("flexible", "binding")
_SUMMARY_METRICS = (
    "final_alliance_edges",
    "final_alliance_density",
    "final_mean_reliability",
    "final_state_count",
    "original_state_survival_rate",
    "cumulative_crises",
    "cumulative_abandonment_events",
    "cumulative_entrapment_events",
    "cumulative_buck_passing_events",
    "cumulative_chain_ganging",
    "cumulative_third_party_participations",
    "cumulative_conflict_diffusion",
    "cumulative_support_cost",
    "cumulative_war_cost",
    "cumulative_conflict_cost",
    "cumulative_alliance_turnover",
    "cumulative_conquests",
)


def _doctrines() -> tuple[AllianceDoctrine, ...]:
    return tuple(doctrine_for(name) for name in _DOCTRINE_NAMES)  # type: ignore[arg-type]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty experiment table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _run_rows(
    history: list[AllianceWorld],
    *,
    seed: int,
    polarity: PolarityRegime,
    threat_regime: ThreatRegime,
    doctrine: AllianceDoctrine,
    fingerprint: str,
    original_ids: set[int],
    run_context: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    cumulative = {
        "crises": 0,
        "abandonment_events": 0,
        "entrapment_events": 0,
        "buck_passing_events": 0,
        "chain_ganging": 0,
        "third_party_participations": 0,
        "conflict_diffusion": 0,
        "support_cost": 0.0,
        "war_cost": 0.0,
        "conflict_cost": 0.0,
        "alliance_turnover": 0,
        "conquests": 0,
    }
    rows: list[dict[str, object]] = []
    for world in history:
        metrics = alliance_metrics(world)
        if world.generation > 0:
            cumulative["crises"] += len(world.crises)
            cumulative["abandonment_events"] += int(metrics["abandonment_events"])
            cumulative["entrapment_events"] += int(metrics["entrapment_events"])
            cumulative["buck_passing_events"] += int(metrics["buck_passing_events"])
            cumulative["chain_ganging"] += int(metrics["chain_ganging_crises"])
            cumulative["third_party_participations"] += int(
                metrics["third_party_participations"]
            )
            cumulative["conflict_diffusion"] += int(metrics["conflict_diffusion"])
            cumulative["support_cost"] += float(metrics["support_cost"])
            cumulative["war_cost"] += float(metrics["war_cost"])
            cumulative["conflict_cost"] += float(metrics["conflict_cost"])
            cumulative["alliance_turnover"] += int(metrics["alliance_turnover"])
            cumulative["conquests"] += int(metrics["conquests"])

        current_ids = {int(value) for value in alive_polities(world.territorial)}
        survival = len(original_ids & current_ids) / len(original_ids)
        rows.append(
            {
                "seed": seed,
                "polarity": polarity,
                "threat_regime": threat_regime,
                "doctrine": doctrine.name,
                "initial_fingerprint": fingerprint,
                **run_context,
                **metrics,
                "original_state_survival_rate": survival,
                **{f"cumulative_{name}": value for name, value in cumulative.items()},
            }
        )

    final = rows[-1]
    summary = {
        "seed": seed,
        "polarity": polarity,
        "threat_regime": threat_regime,
        "doctrine": doctrine.name,
        "initial_fingerprint": fingerprint,
        **run_context,
        "initial_alliance_edges": rows[0]["alliance_edges"],
        "final_alliance_edges": final["alliance_edges"],
        "final_alliance_density": final["alliance_density"],
        "final_mean_reliability": final["mean_reliability"],
        "final_state_count": final["state_count"],
        "original_state_survival_rate": final["original_state_survival_rate"],
        **{f"cumulative_{name}": value for name, value in cumulative.items()},
    }
    return rows, summary


def _aggregate(run_rows: list[dict[str, object]], seeds: int) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in run_rows:
        key = (str(row["polarity"]), str(row["threat_regime"]), str(row["doctrine"]))
        grouped[key].append(row)

    result: list[dict[str, object]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        summary: dict[str, object] = {
            "polarity": key[0],
            "threat_regime": key[1],
            "doctrine": key[2],
            "seeds": seeds,
        }
        for metric in _SUMMARY_METRICS:
            summary[f"mean_{metric}"] = fmean(float(row[metric]) for row in rows)
        result.append(summary)
    return result


def _paired_differences(run_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[int, str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in run_rows:
        key = (int(row["seed"]), str(row["polarity"]), str(row["threat_regime"]))
        grouped[key][str(row["doctrine"])] = row

    result: list[dict[str, object]] = []
    for key in sorted(grouped):
        pair = grouped[key]
        if set(pair) != {"binding", "flexible"}:
            raise AssertionError("every M4 world must contain both doctrines")
        binding = pair["binding"]
        flexible = pair["flexible"]
        if binding["initial_fingerprint"] != flexible["initial_fingerprint"]:
            raise AssertionError("matched M4 doctrines received different initial worlds")
        row: dict[str, object] = {
            "seed": key[0],
            "polarity": key[1],
            "threat_regime": key[2],
            "initial_fingerprint": binding["initial_fingerprint"],
            "steps": binding["steps"],
            "height": binding["height"],
            "width": binding["width"],
            "initial_polities": binding["initial_polities"],
            "difference_definition": "binding minus flexible",
        }
        for metric in _SUMMARY_METRICS:
            row[f"delta_{metric}"] = float(binding[metric]) - float(flexible[metric])
        result.append(row)
    return result


def _write_manifest(
    path: Path,
    *,
    steps: int,
    seeds: int,
    shape: tuple[int, int],
    num_polities: int,
    params: TerritorialParameters,
    doctrines: tuple[AllianceDoctrine, ...],
) -> None:
    manifest = {
        "experiment": "M4 alliance security dilemma",
        "version": "0.4.0",
        "design": {
            "commitment_doctrines": [doctrine.name for doctrine in doctrines],
            "polarity_regimes": list(_POLARITY_REGIMES),
            "threat_regimes": list(_THREAT_REGIMES),
            "paired_seeds_per_condition": seeds,
            "steps": steps,
            "shape": list(shape),
            "initial_polities": num_polities,
        },
        "matching_contract": {
            "same_initial_world_within_doctrine_pair": True,
            "same_territorial_resolver_across_doctrines": True,
            "same_crisis_candidate_generator": True,
            "battle_noise_key": [
                "battle_seed",
                "generation",
                "attacker_id",
                "defender_id",
                "target_cell_id",
            ],
            "difference_definition": "binding minus flexible",
        },
        "territorial_parameters": asdict(params),
        "doctrine_parameters": {doctrine.name: asdict(doctrine) for doctrine in doctrines},
        "interpretive_status": (
            "matched generative mechanism experiment inspired by Snyderian alliance politics; "
            "not historical validation or a policy recommendation"
        ),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _condition_label(polarity: str, threat: str) -> str:
    return f"{polarity}\n{threat} threat"


def _save_grouped_metric_plot(
    aggregate_rows: list[dict[str, object]],
    path: Path,
    *,
    metric: str,
    title: str,
    ylabel: str,
) -> None:
    conditions = [
        (polarity, threat)
        for polarity in _POLARITY_REGIMES
        for threat in _THREAT_REGIMES
    ]
    lookup = {
        (str(row["polarity"]), str(row["threat_regime"]), str(row["doctrine"])): float(
            row[metric]
        )
        for row in aggregate_rows
    }
    x_values = np.arange(len(conditions), dtype=np.float64)
    width = 0.36
    figure, axis = plt.subplots(figsize=(9.2, 5.2))
    for index, doctrine in enumerate(("flexible", "binding")):
        values = [lookup[(polarity, threat, doctrine)] for polarity, threat in conditions]
        offset = (index - 0.5) * width
        axis.bar(x_values + offset, values, width=width, label=doctrine)
    axis.set_xticks(
        x_values,
        [_condition_label(polarity, threat) for polarity, threat in conditions],
    )
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _draw_network(axis: plt.Axes, world: AllianceWorld, title: str) -> None:
    ids = [int(value) for value in alive_polities(world.territorial)]
    angles = np.linspace(0.0, 2.0 * np.pi, len(ids), endpoint=False)
    positions = {
        polity_id: (float(np.cos(angle)), float(np.sin(angle)))
        for polity_id, angle in zip(ids, angles, strict=True)
    }
    for first, second in alliance_edges(world):
        x_values = [positions[first][0], positions[second][0]]
        y_values = [positions[first][1], positions[second][1]]
        axis.plot(x_values, y_values, linewidth=1.2, alpha=0.65)
    for polity_id in ids:
        x_value, y_value = positions[polity_id]
        axis.scatter([x_value], [y_value], s=320)
        axis.text(x_value, y_value, str(polity_id), ha="center", va="center", fontsize=9)
    axis.set_title(title)
    axis.set_aspect("equal")
    axis.set_xlim(-1.25, 1.25)
    axis.set_ylim(-1.25, 1.25)
    axis.axis("off")


def _save_matched_networks(
    path: Path,
    initial: AllianceWorld,
    finals: dict[str, AllianceWorld],
    *,
    steps: int,
) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.6))
    _draw_network(axes[0], initial, "same initial alliance graph")
    _draw_network(axes[1], finals["flexible"], f"flexible after {steps} crises")
    _draw_network(axes[2], finals["binding"], f"binding after {steps} crises")
    figure.suptitle("M4 matched alliance comparison: doctrine is the treatment", fontsize=14)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def run_alliance_comparison(
    output_dir: Path,
    *,
    steps: int = 24,
    seeds: int = 6,
    shape: tuple[int, int] = (12, 16),
    num_polities: int = 8,
    params: TerritorialParameters | None = None,
) -> tuple[Path, Path, Path, Path, Path]:
    """Run the frozen M4 2×2×2 matched design and save auditable outputs."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    base_params = params or TerritorialParameters(
        offense_multiplier=1.10,
        defense_multiplier=1.05,
        attack_threshold=0.82,
    )
    doctrines = _doctrines()

    timeseries_rows: list[dict[str, object]] = []
    run_summary_rows: list[dict[str, object]] = []
    selected_initial: AllianceWorld | None = None
    selected_finals: dict[str, AllianceWorld] = {}

    for polarity_index, polarity in enumerate(_POLARITY_REGIMES):
        for threat_index, threat_regime in enumerate(_THREAT_REGIMES):
            condition_offset = 10_000 * polarity_index + 1_000 * threat_index
            for seed in range(seeds):
                initial = initialize_alliance_world(
                    shape,
                    num_polities=num_polities,
                    seed=seed,
                    polarity=polarity,
                    threat_regime=threat_regime,
                )
                fingerprint = alliance_world_fingerprint(initial)
                original_ids = {int(value) for value in alive_polities(initial.territorial)}
                run_params = replace(
                    base_params,
                    battle_seed=base_params.battle_seed + condition_offset + seed,
                )
                run_context: dict[str, object] = {
                    "steps": steps,
                    "height": shape[0],
                    "width": shape[1],
                    "initial_polities": num_polities,
                    "attack_threshold": run_params.attack_threshold,
                    "battle_noise": run_params.battle_noise,
                    "battle_seed": run_params.battle_seed,
                }
                for doctrine in doctrines:
                    history = run_alliance(
                        initial,
                        run_params,
                        doctrine,
                        steps=steps,
                    )
                    rows, summary = _run_rows(
                        history,
                        seed=seed,
                        polarity=polarity,
                        threat_regime=threat_regime,
                        doctrine=doctrine,
                        fingerprint=fingerprint,
                        original_ids=original_ids,
                        run_context=run_context,
                    )
                    timeseries_rows.extend(rows)
                    run_summary_rows.append(summary)
                    if polarity == "multipolar" and threat_regime == "diffuse" and seed == 0:
                        selected_initial = initial.copy()
                        selected_finals[doctrine.name] = history[-1].copy()

    aggregate_rows = _aggregate(run_summary_rows, seeds)
    paired_rows = _paired_differences(run_summary_rows)

    manifest_path = output_dir / "m4_manifest.json"
    timeseries_path = output_dir / "m4_timeseries.csv"
    run_summary_path = output_dir / "m4_run_summary.csv"
    aggregate_path = output_dir / "m4_ensemble_summary.csv"
    paired_path = output_dir / "m4_paired_differences.csv"
    _write_manifest(
        manifest_path,
        steps=steps,
        seeds=seeds,
        shape=shape,
        num_polities=num_polities,
        params=base_params,
        doctrines=doctrines,
    )
    _write_csv(timeseries_path, timeseries_rows)
    _write_csv(run_summary_path, run_summary_rows)
    _write_csv(aggregate_path, aggregate_rows)
    _write_csv(paired_path, paired_rows)

    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m4_abandonment.png",
        metric="mean_cumulative_abandonment_events",
        title="M4: abandonment under matched alliance doctrines",
        ylabel="mean cumulative abandonment events",
    )
    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m4_entrapment.png",
        metric="mean_cumulative_entrapment_events",
        title="M4: entrapment under matched alliance doctrines",
        ylabel="mean cumulative entrapment events",
    )
    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m4_chain_ganging.png",
        metric="mean_cumulative_chain_ganging",
        title="M4: chain-ganging crises",
        ylabel="mean cumulative chain-ganging crises",
    )
    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m4_conflict_cost.png",
        metric="mean_cumulative_conflict_cost",
        title="M4: alliance support plus territorial war cost",
        ylabel="mean cumulative conflict cost",
    )
    if selected_initial is None or set(selected_finals) != {"binding", "flexible"}:
        raise AssertionError("failed to capture the selected M4 matched-network illustration")
    _save_matched_networks(
        output_dir / "m4_matched_networks.png",
        selected_initial,
        selected_finals,
        steps=steps,
    )
    return manifest_path, timeseries_path, run_summary_path, aggregate_path, paired_path
