"""Replaceable target-selection policy for the generic M2 baseline."""

from __future__ import annotations

from math import sqrt

import numpy as np

from international_life._territorial.measures import _available_treasury, _border_cells
from international_life._territorial.types import (
    AttackOrder,
    FloatVector,
    TerritorialParameters,
    TerritorialWorld,
)
from international_life.hexgrid import HexCoordinate, hex_neighbors


def propose_attacks(
    world: TerritorialWorld,
    params: TerritorialParameters,
    *,
    available_treasury: FloatVector | None = None,
) -> tuple[AttackOrder, ...]:
    """Choose at most one locally adjacent target for every polity.

    The generic M2 rule attacks only when predicted concentrated strength meets
    ``attack_threshold``. Target choice combines the expected attack/defense
    ratio with a small preference for productive territory.
    """
    available = (
        _available_treasury(world, params)
        if available_treasury is None
        else np.asarray(available_treasury, dtype=np.float64)
    )
    if available.shape != world.treasury.shape:
        raise ValueError("available_treasury must have the same shape as world.treasury")

    borders = _border_cells(world)
    field_strength = np.zeros_like(available)
    for polity_id, cells in borders.items():
        if cells:
            field_strength[polity_id] = (
                params.mobilization * available[polity_id] / sqrt(len(cells))
            )

    mean_resource = float(world.resources.mean())
    orders: list[AttackOrder] = []
    for attacker_id in sorted(borders):
        target_coordinates: set[HexCoordinate] = set()
        for source in borders[attacker_id]:
            for target in hex_neighbors(source, world.shape, boundary="fixed"):
                if int(world.polities[target]) != attacker_id:
                    target_coordinates.add(target)

        candidates: list[AttackOrder] = []
        for target in sorted(target_coordinates):
            defender_id = int(world.polities[target])
            neighbors = hex_neighbors(target, world.shape, boundary="fixed")
            attacker_support = sum(
                int(world.polities[neighbor]) == attacker_id for neighbor in neighbors
            )
            defender_support = sum(
                int(world.polities[neighbor]) == defender_id for neighbor in neighbors
            )
            attack_concentration = 1.0 + params.support_bonus * max(0, attacker_support - 1)
            defense_concentration = 1.0 + params.support_bonus * defender_support

            predicted_attack = (
                params.offense_multiplier
                * field_strength[attacker_id]
                * attack_concentration
            )
            predicted_defense = (
                params.defense_multiplier
                * field_strength[defender_id]
                * defense_concentration
                + params.garrison_strength * world.resources[target]
                + params.fortification_value * world.fortification[target]
            )
            expected_ratio = predicted_attack / max(predicted_defense, 1e-12)
            score = expected_ratio + params.resource_attraction * (
                world.resources[target] / mean_resource
            )
            if expected_ratio >= params.attack_threshold:
                candidates.append(
                    AttackOrder(
                        attacker_id=attacker_id,
                        defender_id=defender_id,
                        target=target,
                        predicted_attack=float(predicted_attack),
                        predicted_defense=float(predicted_defense),
                        expected_ratio=float(expected_ratio),
                        score=float(score),
                    )
                )

        if candidates:
            chosen = max(
                candidates,
                key=lambda order: (
                    order.score,
                    order.expected_ratio,
                    world.resources[order.target],
                    -order.target[0],
                    -order.target[1],
                ),
            )
            orders.append(chosen)
    return tuple(orders)
