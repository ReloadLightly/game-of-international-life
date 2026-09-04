"""Battle resolution, territorial transition, succession, and simulation runner."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from numpy.typing import NDArray

from international_life._territorial.measures import _available_treasury, alive_polities
from international_life._territorial.policy import DEFAULT_POLICY, TerritorialPolicy
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


def _order_rng(
    world: TerritorialWorld,
    params: TerritorialParameters,
    order: AttackOrder,
) -> np.random.Generator:
    """Key battle noise to the encounter rather than the policy's order count."""
    target_id = order.target[0] * world.shape[1] + order.target[1]
    seed_sequence = np.random.SeedSequence(
        [
            params.battle_seed,
            world.generation,
            order.attacker_id,
            order.defender_id,
            target_id,
        ]
    )
    return np.random.default_rng(seed_sequence)


def _resolve_battles(
    world: TerritorialWorld,
    params: TerritorialParameters,
    orders: tuple[AttackOrder, ...],
    available_treasury: FloatVector,
) -> tuple[PolityGrid, FloatVector, tuple[BattleEvent, ...]]:
    events: list[BattleEvent] = []
    next_treasury = available_treasury.copy()

    for order in sorted(orders, key=lambda candidate: candidate.attacker_id):
        rng = _order_rng(world, params, order)
        attack_shock = 1.0 + rng.uniform(-params.battle_noise, params.battle_noise)
        defense_shock = 1.0 + rng.uniform(-params.battle_noise, params.battle_noise)
        attack_strength = order.predicted_attack * attack_shock
        defense_strength = order.predicted_defense * defense_shock
        success = attack_strength > defense_strength
        attacker_cost = params.attack_cost * attack_strength
        defender_cost = params.defense_cost * defense_strength
        events.append(
            BattleEvent(
                attacker_id=order.attacker_id,
                defender_id=order.defender_id,
                target=order.target,
                attack_strength=float(attack_strength),
                defense_strength=float(defense_strength),
                success=bool(success),
                attacker_cost=float(attacker_cost),
                defender_cost=float(defender_cost),
            )
        )
        next_treasury[order.attacker_id] -= attacker_cost
        next_treasury[order.defender_id] -= defender_cost

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
    """Turn every detached component into a new contiguous successor polity."""
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


def _advance_from_orders(
    world: TerritorialWorld,
    params: TerritorialParameters,
    orders: tuple[AttackOrder, ...],
    available: FloatVector,
    *,
    policy_name: str,
) -> TerritorialWorld:
    """Apply an already-chosen order set using the shared territorial resolver."""
    previous_ids = {int(value) for value in alive_polities(world)}
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
        orders=orders,
        battles=events,
        fragmentations=fragmentations,
        extinctions=extinctions,
        policy_name=policy_name,
        generation=world.generation + 1,
    )


def territorial_step_from_orders(
    world: TerritorialWorld,
    params: TerritorialParameters,
    *,
    orders: tuple[AttackOrder, ...],
    policy_name: str = "external-orders",
) -> TerritorialWorld:
    """Advance once from explicit orders while preserving all M2/M3 world mechanics.

    M4 uses this narrow seam after its alliance layer has selected one primary
    crisis and calculated third-party contributions. Production, battle noise,
    war costs, fortification, conquest, extinction, and fragmentation remain
    owned by the territorial engine.
    """
    validate_hex_shape(world.shape, boundary=params.boundary)
    if not policy_name:
        raise ValueError("policy_name must not be empty")
    available = _available_treasury(world, params)
    return _advance_from_orders(
        world,
        params,
        orders,
        available,
        policy_name=policy_name,
    )


def territorial_step(
    world: TerritorialWorld,
    params: TerritorialParameters,
    *,
    policy: TerritorialPolicy | None = None,
) -> TerritorialWorld:
    """Advance resources, conflict, territorial control, and fragmentation once."""
    validate_hex_shape(world.shape, boundary=params.boundary)
    selected_policy = policy or DEFAULT_POLICY
    available = _available_treasury(world, params)
    orders = selected_policy.propose_attacks(
        world,
        params,
        available_treasury=available,
    )
    return _advance_from_orders(
        world,
        params,
        orders,
        available,
        policy_name=selected_policy.name,
    )


def run_territorial(
    initial: TerritorialWorld,
    params: TerritorialParameters,
    *,
    steps: int,
    include_initial: bool = True,
    policy: TerritorialPolicy | None = None,
) -> list[TerritorialWorld]:
    """Run a territorial model and return independent generation snapshots."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    selected_policy = policy or DEFAULT_POLICY
    current = replace(initial.copy(), policy_name=selected_policy.name)
    history = [current.copy()] if include_initial else []
    for _ in range(steps):
        current = territorial_step(current, params, policy=policy)
        history.append(current.copy())
    return history
