"""Battle resolution, territorial transition, succession, and simulation runner."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from numpy.typing import NDArray

from international_life._territorial.measures import _available_treasury, alive_polities
from international_life._territorial.policy import propose_attacks
from international_life._territorial.types import (
    AttackOrder,
    BattleEvent,
    FloatVector,
    FragmentationEvent,
    PolityGrid,
    TerritorialParameters,
    TerritorialWorld,
)
from international_life.core import Boundary, validate_2d
from international_life.hexgrid import (
    HexCoordinate,
    connected_components,
    labels_are_contiguous,
    validate_hex_shape,
)


def _resolve_battles(
    world: TerritorialWorld,
    params: TerritorialParameters,
    orders: tuple[AttackOrder, ...],
    available_treasury: FloatVector,
) -> tuple[PolityGrid, FloatVector, tuple[BattleEvent, ...]]:
    seed_sequence = np.random.SeedSequence([params.battle_seed, world.generation])
    rng = np.random.default_rng(seed_sequence)
    events: list[BattleEvent] = []
    next_treasury = available_treasury.copy()

    for order in sorted(orders, key=lambda candidate: candidate.attacker_id):
        attack_shock = 1.0 + rng.uniform(-params.battle_noise, params.battle_noise)
        defense_shock = 1.0 + rng.uniform(-params.battle_noise, params.battle_noise)
        attack_strength = order.predicted_attack * attack_shock
        defense_strength = order.predicted_defense * defense_shock
        success = attack_strength > defense_strength
        events.append(
            BattleEvent(
                attacker_id=order.attacker_id,
                defender_id=order.defender_id,
                target=order.target,
                attack_strength=float(attack_strength),
                defense_strength=float(defense_strength),
                success=bool(success),
            )
        )
        next_treasury[order.attacker_id] -= params.attack_cost * attack_strength
        next_treasury[order.defender_id] -= params.defense_cost * defense_strength

    next_treasury = np.clip(next_treasury, 0.0, None)
    successful_by_target: dict[HexCoordinate, list[int]] = {}
    for index, event in enumerate(events):
        if event.success:
            successful_by_target.setdefault(event.target, []).append(index)

    next_polities = world.polities.copy()
    for target, indices in sorted(successful_by_target.items()):
        winner_index = max(
            indices,
            key=lambda index: (
                events[index].attack_strength / max(events[index].defense_strength, 1e-12),
                events[index].attack_strength,
                -events[index].attacker_id,
            ),
        )
        winner = events[winner_index]
        next_polities[target] = winner.attacker_id
        events[winner_index] = replace(winner, conquered=True)

    return next_polities, next_treasury, tuple(events)


def fragment_disconnected_polities(
    polities: NDArray[np.integer],
    resources: NDArray[np.floating],
    treasury: NDArray[np.floating],
    *,
    boundary: Boundary = "fixed",
) -> tuple[PolityGrid, FloatVector, tuple[FragmentationEvent, ...]]:
    """Turn every detached component into a new contiguous successor polity.

    The largest component retains the parent ID. The parent's treasury is split
    in proportion to component resource production; new IDs are appended and
    never reuse extinct historical IDs.
    """
    validate_2d(polities, name="polities")
    validate_2d(resources, name="resources")
    if polities.shape != resources.shape:
        raise ValueError("polities and resources must have the same shape")
    if treasury.ndim != 1 or int(np.max(polities)) >= len(treasury):
        raise ValueError("treasury must contain every represented polity ID")

    next_polities = np.asarray(polities, dtype=np.int32).copy()
    treasury_values = np.asarray(treasury, dtype=np.float64).tolist()
    events: list[FragmentationEvent] = []

    for parent_id in sorted(int(value) for value in np.unique(next_polities)):
        components = connected_components(next_polities, parent_id, boundary=boundary)
        if len(components) <= 1:
            continue
        ranked = sorted(
            components,
            key=lambda component: (
                -len(component),
                -sum(float(resources[coordinate]) for coordinate in component),
                component[0],
            ),
        )
        weights = np.array(
            [sum(float(resources[coordinate]) for coordinate in component) for component in ranked],
            dtype=np.float64,
        )
        weights = weights / weights.sum()
        parent_treasury = float(treasury_values[parent_id])
        treasury_values[parent_id] = parent_treasury * float(weights[0])

        for component, weight in zip(ranked[1:], weights[1:], strict=True):
            successor_id = len(treasury_values)
            inherited = parent_treasury * float(weight)
            treasury_values.append(inherited)
            for coordinate in component:
                next_polities[coordinate] = successor_id
            events.append(
                FragmentationEvent(
                    parent_id=parent_id,
                    successor_id=successor_id,
                    cells=len(component),
                    inherited_treasury=inherited,
                )
            )

    return next_polities, np.asarray(treasury_values, dtype=np.float64), tuple(events)


def territorial_step(
    world: TerritorialWorld,
    params: TerritorialParameters,
) -> TerritorialWorld:
    """Advance resources, conflict, territorial control, and fragmentation once."""
    validate_hex_shape(world.shape, boundary=params.boundary)

    previous_ids = {int(value) for value in alive_polities(world)}
    available = _available_treasury(world, params)
    orders = propose_attacks(world, params, available_treasury=available)
    next_polities, next_treasury, events = _resolve_battles(
        world,
        params,
        orders,
        available,
    )

    next_fortification = np.minimum(
        world.fortification + params.fortification_growth,
        params.fortification_cap,
    )
    for event in events:
        next_fortification[event.target] *= params.battle_damage
        if event.conquered:
            next_fortification[event.target] *= params.conquest_retention

    represented_after_conquest = {int(value) for value in np.unique(next_polities)}
    extinctions = tuple(sorted(previous_ids - represented_after_conquest))
    for polity_id in extinctions:
        next_treasury[polity_id] = 0.0

    next_polities, next_treasury, fragmentations = fragment_disconnected_polities(
        next_polities,
        world.resources,
        next_treasury,
        boundary=params.boundary,
    )
    if not labels_are_contiguous(next_polities, boundary=params.boundary):
        raise AssertionError("fragmentation repair failed to restore contiguous polities")

    return TerritorialWorld(
        polities=next_polities,
        resources=world.resources.copy(),
        fortification=next_fortification,
        treasury=next_treasury,
        battles=events,
        fragmentations=fragmentations,
        extinctions=extinctions,
        generation=world.generation + 1,
    )


def run_territorial(
    initial: TerritorialWorld,
    params: TerritorialParameters,
    *,
    steps: int,
    include_initial: bool = True,
) -> list[TerritorialWorld]:
    """Run M2 and return independent generation snapshots."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    current = initial.copy()
    history = [current.copy()] if include_initial else []
    for _ in range(steps):
        current = territorial_step(current, params)
        history.append(current.copy())
    return history
