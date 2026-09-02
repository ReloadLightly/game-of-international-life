"""M3 matched comparison of security-seeking and power-maximizing policies."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from statistics import fmean

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import RegularPolygon

from international_life._territorial.measures import alive_polities, territorial_metrics
from international_life._territorial.policy import (
    PowerMaximizingPolicy,
    SecuritySeekingPolicy,
    TerritorialPolicy,
)
from international_life._territorial.types import TerritorialParameters, TerritorialWorld
from international_life.structural import (
    CapabilityRegime,
    ResourceRegime,
    initialize_structural_world,
    world_fingerprint,
)
from international_life.territorial import run_territorial

_CAPABILITY_REGIMES: tuple[CapabilityRegime, ...] = ("balanced", "dominant-power")
_RESOURCE_REGIMES: tuple[ResourceRegime, ...] = ("diffuse", "clustered")
_SUMMARY_METRICS = (
    "final_state_count",
    "final_power_hhi",
    "final_effective_powers",
    "final_largest_power_share",
    "original_state_survival_rate",
    "cumulative_attack_orders",
    "cumulative_battles",
    "cumulative_conquests",
    "cumulative_war_cost",
    "cumulative_attacks_while_secure",
    "cumulative_extinctions",
    "cumulative_fragmentations",
)


def _policies() -> tuple[TerritorialPolicy, ...]:
    return (SecuritySeekingPolicy(), PowerMaximizingPolicy())


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty experiment table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(
    path: Path,
    *,
    steps: int,
    seeds: int,
    shape: tuple[int, int],
    num_polities: int,
    dominant_share: float,
    params: TerritorialParameters,
    policies: tuple[TerritorialPolicy, ...],
) -> None:
    manifest = {
        "experiment": "M3 structural comparison",
        "version": "0.3.0",
        "design": {
            "capability_regimes": list(_CAPABILITY_REGIMES),
            "resource_regimes": list(_RESOURCE_REGIMES),
            "policies": [policy.name for policy in policies],
            "paired_seeds_per_condition": seeds,
            "steps": steps,
            "shape": list(shape),
            "initial_polities": num_polities,
            "dominant_power_share": dominant_share,
        },
        "matching_contract": {
            "same_initial_world_within_policy_pair": True,
            "same_world_mechanics_across_policies": True,
            "battle_noise_key": [
                "battle_seed",
                "generation",
                "attacker_id",
                "defender_id",
                "target_cell_id",
            ],
            "difference_definition": "power-maximizing minus security-seeking",
        },
        "shared_world_parameters": asdict(params),
        "policy_parameters": {
            policy.name: asdict(policy) for policy in policies
        },
        "interpretive_status": (
            "computational mechanism comparison; not historical validation and not a complete "
            "formalization of Waltz or Mearsheimer"
        ),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_rows(
    history: list[TerritorialWorld],
    *,
    policy_name: str,
    seed: int,
    capability_regime: CapabilityRegime,
    resource_regime: ResourceRegime,
    fingerprint: str,
    original_ids: set[int],
    run_context: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    cumulative = {
        "attack_orders": 0,
        "battles": 0,
        "conquests": 0,
        "war_cost": 0.0,
        "attacks_while_secure": 0,
        "extinctions": 0,
        "fragmentations": 0,
    }
    rows: list[dict[str, object]] = []
    for world in history:
        metrics = territorial_metrics(world)
        if world.generation > 0:
            cumulative["attack_orders"] += int(metrics["attack_orders"])
            cumulative["battles"] += int(metrics["battle_count"])
            cumulative["conquests"] += int(metrics["conquests"])
            cumulative["war_cost"] += float(metrics["war_cost"])
            cumulative["attacks_while_secure"] += int(metrics["attacks_while_secure"])
            cumulative["extinctions"] += int(metrics["extinctions"])
            cumulative["fragmentations"] += int(metrics["fragmentations"])

        current_ids = {int(value) for value in alive_polities(world)}
        survival = len(original_ids & current_ids) / len(original_ids)
        rows.append(
            {
                "seed": seed,
                "capability_regime": capability_regime,
                "resource_regime": resource_regime,
                "policy": policy_name,
                "initial_fingerprint": fingerprint,
                **run_context,
                **metrics,
                "original_state_survival_rate": survival,
                "cumulative_attack_orders": cumulative["attack_orders"],
                "cumulative_battles": cumulative["battles"],
                "cumulative_conquests": cumulative["conquests"],
                "cumulative_war_cost": cumulative["war_cost"],
                "cumulative_attacks_while_secure": cumulative["attacks_while_secure"],
                "cumulative_extinctions": cumulative["extinctions"],
                "cumulative_fragmentations": cumulative["fragmentations"],
            }
        )

    final = rows[-1]
    summary = {
        "seed": seed,
        "capability_regime": capability_regime,
        "resource_regime": resource_regime,
        "policy": policy_name,
        "initial_fingerprint": fingerprint,
        **run_context,
        "initial_power_hhi": rows[0]["power_hhi"],
        "initial_resource_cv": rows[0]["resource_cv"],
        "final_state_count": final["state_count"],
        "final_power_hhi": final["power_hhi"],
        "final_effective_powers": final["effective_powers"],
        "final_largest_power_share": final["largest_power_share"],
        "original_state_survival_rate": final["original_state_survival_rate"],
        "cumulative_attack_orders": final["cumulative_attack_orders"],
        "cumulative_battles": final["cumulative_battles"],
        "cumulative_conquests": final["cumulative_conquests"],
        "cumulative_war_cost": final["cumulative_war_cost"],
        "cumulative_attacks_while_secure": final["cumulative_attacks_while_secure"],
        "cumulative_extinctions": final["cumulative_extinctions"],
        "cumulative_fragmentations": final["cumulative_fragmentations"],
    }
    return rows, summary


def _aggregate(run_rows: list[dict[str, object]], seeds: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in run_rows:
        key = (
            str(row["capability_regime"]),
            str(row["resource_regime"]),
            str(row["policy"]),
        )
        groups[key].append(row)

    summaries: list[dict[str, object]] = []
    for key in sorted(groups):
        rows = groups[key]
        summary: dict[str, object] = {
            "capability_regime": key[0],
            "resource_regime": key[1],
            "policy": key[2],
            "seeds": seeds,
            "mean_initial_power_hhi": fmean(float(row["initial_power_hhi"]) for row in rows),
            "mean_initial_resource_cv": fmean(
                float(row["initial_resource_cv"]) for row in rows
            ),
        }
        for metric in _SUMMARY_METRICS:
            summary[f"mean_{metric}"] = fmean(float(row[metric]) for row in rows)
        summaries.append(summary)
    return summaries


def _paired_differences(run_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[int, str, str], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in run_rows:
        key = (
            int(row["seed"]),
            str(row["capability_regime"]),
            str(row["resource_regime"]),
        )
        groups[key][str(row["policy"])] = row

    differences: list[dict[str, object]] = []
    for key in sorted(groups):
        paired = groups[key]
        if set(paired) != {"security-seeking", "power-maximizing"}:
            raise AssertionError("every structural world must contain both policy runs")
        security = paired["security-seeking"]
        power = paired["power-maximizing"]
        if security["initial_fingerprint"] != power["initial_fingerprint"]:
            raise AssertionError("matched policy runs did not receive the same initial world")
        row: dict[str, object] = {
            "seed": key[0],
            "capability_regime": key[1],
            "resource_regime": key[2],
            "initial_fingerprint": security["initial_fingerprint"],
            "steps": security["steps"],
            "height": security["height"],
            "width": security["width"],
            "initial_polities": security["initial_polities"],
            "dominant_share": security["dominant_share"],
            "difference_definition": "power-maximizing minus security-seeking",
        }
        for metric in _SUMMARY_METRICS:
            row[f"delta_{metric}"] = float(power[metric]) - float(security[metric])
        differences.append(row)
    return differences


def _condition_label(capability: str, resource: str) -> str:
    capability_label = "balanced" if capability == "balanced" else "dominant"
    return f"{capability_label}\n{resource} resources"


def _save_grouped_metric_plot(
    aggregate_rows: list[dict[str, object]],
    path: Path,
    *,
    metric: str,
    title: str,
    ylabel: str,
) -> None:
    conditions = [
        (capability, resource)
        for capability in _CAPABILITY_REGIMES
        for resource in _RESOURCE_REGIMES
    ]
    policies = ("security-seeking", "power-maximizing")
    lookup = {
        (
            str(row["capability_regime"]),
            str(row["resource_regime"]),
            str(row["policy"]),
        ): float(row[metric])
        for row in aggregate_rows
    }
    x_values = np.arange(len(conditions), dtype=np.float64)
    width = 0.36
    figure, axis = plt.subplots(figsize=(10, 5.5))
    for index, policy in enumerate(policies):
        offset = (index - 0.5) * width
        values = [lookup[(capability, resource, policy)] for capability, resource in conditions]
        axis.bar(x_values + offset, values, width=width, label=policy)
    axis.set_xticks(
        x_values,
        [_condition_label(capability, resource) for capability, resource in conditions],
    )
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=190)
    plt.close(figure)


def _hex_center(row: int, col: int) -> tuple[float, float]:
    return np.sqrt(3.0) * (col + 0.5 * (row % 2)), 1.5 * row


def _draw_hex_world(axis: plt.Axes, world: TerritorialWorld, title: str) -> None:
    patches = []
    values = []
    for row in range(world.shape[0]):
        for col in range(world.shape[1]):
            patches.append(
                RegularPolygon(
                    _hex_center(row, col),
                    numVertices=6,
                    radius=1.0,
                    orientation=0.0,
                )
            )
            values.append(float((int(world.polities[row, col]) - 1) % 20))
    collection = PatchCollection(
        patches,
        array=np.asarray(values),
        cmap="tab20",
        edgecolor="black",
        linewidth=0.12,
    )
    collection.set_clim(-0.5, 19.5)
    axis.add_collection(collection)
    axis.autoscale_view()
    axis.set_aspect("equal")
    axis.invert_yaxis()
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(title)


def _save_matched_worlds(
    path: Path,
    initial: TerritorialWorld,
    final_worlds: dict[str, TerritorialWorld],
    *,
    steps: int,
) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 5.2))
    _draw_hex_world(axes[0], initial, "Same initial world")
    _draw_hex_world(
        axes[1],
        final_worlds["security-seeking"],
        f"Security-seeking after {steps} generations",
    )
    _draw_hex_world(
        axes[2],
        final_worlds["power-maximizing"],
        f"Power-maximizing after {steps} generations",
    )
    figure.suptitle(
        "M3 matched comparison: only the policy rule changes",
        fontsize=15,
    )
    figure.tight_layout()
    figure.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(figure)


def run_structural_comparison(
    output_dir: Path,
    *,
    steps: int = 40,
    seeds: int = 6,
    shape: tuple[int, int] = (12, 16),
    num_polities: int = 8,
    dominant_share: float = 0.35,
    params: TerritorialParameters | None = None,
) -> tuple[Path, Path, Path, Path, Path]:
    """Run the frozen M3 2×2×2 matched design and save auditable outputs."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    base_params = params or TerritorialParameters()
    policies = _policies()

    timeseries_rows: list[dict[str, object]] = []
    run_summary_rows: list[dict[str, object]] = []
    selected_initial: TerritorialWorld | None = None
    selected_finals: dict[str, TerritorialWorld] = {}

    for capability_index, capability_regime in enumerate(_CAPABILITY_REGIMES):
        for resource_index, resource_regime in enumerate(_RESOURCE_REGIMES):
            condition_offset = 10_000 * capability_index + 1_000 * resource_index
            for seed in range(seeds):
                initial = initialize_structural_world(
                    shape,
                    num_polities=num_polities,
                    seed=seed,
                    capability_regime=capability_regime,
                    resource_regime=resource_regime,
                    dominant_share=dominant_share,
                )
                fingerprint = world_fingerprint(initial)
                original_ids = {int(value) for value in alive_polities(initial)}
                run_params = replace(
                    base_params,
                    battle_seed=base_params.battle_seed + condition_offset + seed,
                )
                run_context: dict[str, object] = {
                    "steps": steps,
                    "height": shape[0],
                    "width": shape[1],
                    "initial_polities": num_polities,
                    "dominant_share": dominant_share,
                    "attack_threshold": run_params.attack_threshold,
                    "battle_noise": run_params.battle_noise,
                    "battle_seed": run_params.battle_seed,
                }

                for policy in policies:
                    history = run_territorial(
                        initial,
                        run_params,
                        steps=steps,
                        policy=policy,
                    )
                    rows, summary = _run_rows(
                        history,
                        policy_name=policy.name,
                        seed=seed,
                        capability_regime=capability_regime,
                        resource_regime=resource_regime,
                        fingerprint=fingerprint,
                        original_ids=original_ids,
                        run_context=run_context,
                    )
                    timeseries_rows.extend(rows)
                    run_summary_rows.append(summary)

                    if (
                        capability_regime == "dominant-power"
                        and resource_regime == "clustered"
                        and seed == 0
                    ):
                        selected_initial = initial.copy()
                        selected_finals[policy.name] = history[-1].copy()

    paired_rows = _paired_differences(run_summary_rows)
    aggregate_rows = _aggregate(run_summary_rows, seeds)

    manifest_path = output_dir / "m3_manifest.json"
    timeseries_path = output_dir / "m3_timeseries.csv"
    run_summary_path = output_dir / "m3_run_summary.csv"
    aggregate_path = output_dir / "m3_ensemble_summary.csv"
    paired_path = output_dir / "m3_paired_differences.csv"
    _write_manifest(
        manifest_path,
        steps=steps,
        seeds=seeds,
        shape=shape,
        num_polities=num_polities,
        dominant_share=dominant_share,
        params=base_params,
        policies=policies,
    )
    _write_csv(timeseries_path, timeseries_rows)
    _write_csv(run_summary_path, run_summary_rows)
    _write_csv(aggregate_path, aggregate_rows)
    _write_csv(paired_path, paired_rows)

    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m3_war_cost.png",
        metric="mean_cumulative_war_cost",
        title="M3: systemic mobilization cost under matched policy rules",
        ylabel="mean cumulative war cost",
    )
    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m3_attacks_while_secure.png",
        metric="mean_cumulative_attacks_while_secure",
        title="M3 mechanism check: attacks launched after security sufficiency",
        ylabel="mean cumulative attacks while secure",
    )
    _save_grouped_metric_plot(
        aggregate_rows,
        output_dir / "m3_power_concentration.png",
        metric="mean_final_power_hhi",
        title="M3: final capability concentration",
        ylabel="mean final power HHI",
    )
    if selected_initial is None or set(selected_finals) != {
        "security-seeking",
        "power-maximizing",
    }:
        raise AssertionError("failed to capture the selected matched-world illustration")
    _save_matched_worlds(
        output_dir / "m3_matched_worlds.png",
        selected_initial,
        selected_finals,
        steps=steps,
    )
    return manifest_path, timeseries_path, run_summary_path, aggregate_path, paired_path
