"""Network and process observables for M4 alliance politics."""

from __future__ import annotations

from statistics import fmean

import numpy as np

from international_life._alliances.types import AllianceWorld
from international_life._territorial.measures import alive_polities, territorial_metrics


def alliance_edges(
    world: AllianceWorld,
    *,
    threshold: float = 0.50,
) -> tuple[tuple[int, int], ...]:
    """Return reciprocal alliance edges among currently represented polities."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    ids = [int(value) for value in alive_polities(world.territorial)]
    edges: list[tuple[int, int]] = []
    for index, first in enumerate(ids):
        for second in ids[index + 1 :]:
            strength = min(
                float(world.commitments[first, second]),
                float(world.commitments[second, first]),
            )
            if strength >= threshold:
                edges.append((first, second))
    return tuple(edges)


def _edge_values(
    world: AllianceWorld,
    edges: tuple[tuple[int, int], ...],
) -> tuple[list[float], list[float]]:
    commitments: list[float] = []
    reliability: list[float] = []
    for first, second in edges:
        commitments.append(
            min(
                float(world.commitments[first, second]),
                float(world.commitments[second, first]),
            )
        )
        reliability.append(
            0.5
            * (
                float(world.reliability[first, second])
                + float(world.reliability[second, first])
            )
        )
    return commitments, reliability


def alliance_metrics(world: AllianceWorld) -> dict[str, int | float | str]:
    """Return one-generation alliance and territorial process observables."""
    territorial = territorial_metrics(world.territorial)
    edges = alliance_edges(world)
    commitments, reliability = _edge_values(world, edges)
    support_cost = float(sum(event.cost for event in world.support_events))
    third_party_participations = int(
        sum(max(0, crisis.participant_count - 2) for crisis in world.crises)
    )
    chain_ganging = int(sum(crisis.chain_ganging for crisis in world.crises))
    conflict_diffusion = int(
        sum(crisis.participant_count > 2 for crisis in world.crises)
    )
    formations = int(sum(event.action == "formed" for event in world.alliance_changes))
    dissolutions = int(sum(event.action == "dissolved" for event in world.alliance_changes))
    war_cost = float(territorial["war_cost"])

    alive_count = len(alive_polities(world.territorial))
    possible_edges = alive_count * (alive_count - 1)
    density = float(2 * len(edges) / possible_edges) if possible_edges else 0.0

    result: dict[str, int | float | str] = {
        "generation": world.generation,
        "doctrine": world.doctrine_name,
        "polarity": world.polarity,
        "threat_regime": world.threat_regime,
        "alliance_edges": len(edges),
        "alliance_density": density,
        "mean_commitment": float(fmean(commitments)) if commitments else 0.0,
        "mean_reliability": float(fmean(reliability)) if reliability else 0.0,
        "support_requests": len(world.support_events),
        "full_support_events": sum(event.action == "full" for event in world.support_events),
        "partial_support_events": sum(event.action == "partial" for event in world.support_events),
        "withheld_support_events": sum(
            event.action == "withhold" for event in world.support_events
        ),
        "abandonment_events": sum(event.abandonment for event in world.support_events),
        "entrapment_events": sum(event.entrapment for event in world.support_events),
        "buck_passing_events": sum(event.buck_passing for event in world.support_events),
        "third_party_participations": third_party_participations,
        "chain_ganging_crises": chain_ganging,
        "conflict_diffusion": conflict_diffusion,
        "support_cost": support_cost,
        "war_cost": war_cost,
        "conflict_cost": war_cost + support_cost,
        "alliance_formations": formations,
        "alliance_dissolutions": dissolutions,
        "alliance_turnover": formations + dissolutions,
    }
    for key, value in territorial.items():
        if key not in result:
            result[key] = value
    return result
