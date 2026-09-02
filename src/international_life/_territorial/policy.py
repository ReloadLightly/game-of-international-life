"""Replaceable territorial policies and their shared candidate generator.

M3 keeps geography, resources, capability aggregation, battle resolution, and
stochastic shocks fixed. Rival rules differ only in which feasible border
attack they select—or whether they abstain.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import sqrt
from typing import Protocol

import numpy as np

from international_life._territorial.measures import (
    _available_treasury,
    _border_cells,
    polity_capabilities,
)
from international_life._territorial.types import (
    AttackOrder,
    FloatVector,
    TerritorialParameters,
    TerritorialWorld,
)
from international_life.hexgrid import HexCoordinate, hex_neighbors, iter_hex_edges


class TerritorialPolicy(Protocol):
    """Minimal policy interface used by the shared territorial transition engine."""

    name: str

    def propose_attacks(
        self,
        world: TerritorialWorld,
        params: TerritorialParameters,
        *,
        available_treasury: FloatVector | None = None,
    ) -> tuple[AttackOrder, ...]:
        """Return at most one adjacent attack order per currently alive polity."""
        ...


def _validate_available(
    world: TerritorialWorld,
    params: TerritorialParameters,
    available_treasury: FloatVector | None,
) -> FloatVector:
    available = (
        _available_treasury(world, params)
        if available_treasury is None
        else np.asarray(available_treasury, dtype=np.float64)
    )
    if available.shape != world.treasury.shape:
        raise ValueError("available_treasury must have the same shape as world.treasury")
    return available


def _polity_adjacency(world: TerritorialWorld) -> dict[int, set[int]]:
    adjacency = {int(polity_id): set() for polity_id in np.unique(world.polities)}
    for first, second in iter_hex_edges(world.shape, boundary="fixed"):
        first_id = int(world.polities[first])
        second_id = int(world.polities[second])
        if first_id != second_id:
            adjacency[first_id].add(second_id)
            adjacency[second_id].add(first_id)
    return adjacency


def attack_candidates(
    world: TerritorialWorld,
    params: TerritorialParameters,
    *,
    available_treasury: FloatVector | None = None,
) -> dict[int, tuple[AttackOrder, ...]]:
    """Build the common, theory-neutral set of locally feasible border options.

    Candidate construction is shared by every M3 policy. It exposes current
    aggregate capabilities and the full present control map, but actions remain
    spatially local: a polity may target only a directly adjacent foreign cell
    and may issue at most one order per generation.
    """
    available = _validate_available(world, params, available_treasury)
    borders = _border_cells(world)
    field_strength = np.zeros_like(available)
    for polity_id, cells in borders.items():
        if cells:
            field_strength[polity_id] = (
                params.mobilization * available[polity_id] / sqrt(len(cells))
            )

    capabilities = polity_capabilities(world)
    alive_ids = np.unique(world.polities).astype(np.int32)
    total_capability = float(capabilities[alive_ids].sum())
    power_shares = np.zeros_like(capabilities)
    if total_capability > 0.0:
        power_shares[alive_ids] = capabilities[alive_ids] / total_capability

    adjacency = _polity_adjacency(world)
    strongest_rival = np.zeros_like(capabilities)
    for polity_id, rivals in adjacency.items():
        if rivals:
            strongest_rival[polity_id] = max(capabilities[rival] for rival in rivals)

    mean_resource = float(world.resources.mean())
    result: dict[int, tuple[AttackOrder, ...]] = {}
    for attacker_id in sorted(borders):
        target_coordinates: set[HexCoordinate] = set()
        for source in borders[attacker_id]:
            for target in hex_neighbors(source, world.shape, boundary="fixed"):
                if int(world.polities[target]) != attacker_id:
                    target_coordinates.add(target)

        security_ratio = float(
            capabilities[attacker_id] / max(strongest_rival[attacker_id], 1e-12)
        )
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
            target_resource_ratio = float(world.resources[target] / mean_resource)
            expected_relative_gain = float(
                world.resources[target] / max(total_capability, 1e-12)
            )
            border_relief = 2 * attacker_support - len(neighbors)
            candidates.append(
                AttackOrder(
                    attacker_id=attacker_id,
                    defender_id=defender_id,
                    target=target,
                    predicted_attack=float(predicted_attack),
                    predicted_defense=float(predicted_defense),
                    expected_ratio=float(expected_ratio),
                    score=float(
                        expected_ratio + params.resource_attraction * target_resource_ratio
                    ),
                    security_ratio=security_ratio,
                    secure_at_attack=security_ratio >= 1.0,
                    attacker_power_share=float(power_shares[attacker_id]),
                    defender_power_share=float(power_shares[defender_id]),
                    expected_relative_gain=expected_relative_gain,
                    border_relief=border_relief,
                    target_resource_ratio=target_resource_ratio,
                )
            )
        result[attacker_id] = tuple(candidates)
    return result


def _choose_best(candidates: list[AttackOrder]) -> AttackOrder:
    return max(
        candidates,
        key=lambda order: (
            order.score,
            order.expected_ratio,
            order.target_resource_ratio,
            -order.target[0],
            -order.target[1],
        ),
    )


@dataclass(frozen=True, slots=True)
class OpportunisticPolicy:
    """The M2 baseline: take any feasible local opportunity."""

    name: str = "opportunistic"

    def propose_attacks(
        self,
        world: TerritorialWorld,
        params: TerritorialParameters,
        *,
        available_treasury: FloatVector | None = None,
    ) -> tuple[AttackOrder, ...]:
        candidate_map = attack_candidates(
            world,
            params,
            available_treasury=available_treasury,
        )
        orders: list[AttackOrder] = []
        for attacker_id in sorted(candidate_map):
            feasible = [
                replace(candidate, policy=self.name, motive="opportunity")
                for candidate in candidate_map[attacker_id]
                if candidate.expected_ratio >= params.attack_threshold
            ]
            if feasible:
                orders.append(_choose_best(feasible))
        return tuple(orders)


@dataclass(frozen=True, slots=True)
class SecuritySeekingPolicy:
    """Stop expanding once capability is sufficient against the strongest neighbor.

    This is a deliberately minimal defensive structural-realist proxy. A polity
    below ``sufficiency_ratio`` may use a favorable local conquest to repair its
    security position. A polity at or above that ratio abstains even when an
    attractive conquest remains available.
    """

    sufficiency_ratio: float = 1.10
    threat_weight: float = 0.90
    frontier_weight: float = 0.10
    resource_weight: float = 0.08
    name: str = "security-seeking"

    def __post_init__(self) -> None:
        if self.sufficiency_ratio <= 0.0:
            raise ValueError("sufficiency_ratio must be positive")
        for value in (self.threat_weight, self.frontier_weight, self.resource_weight):
            if value < 0.0:
                raise ValueError("policy weights must be non-negative")

    def propose_attacks(
        self,
        world: TerritorialWorld,
        params: TerritorialParameters,
        *,
        available_treasury: FloatVector | None = None,
    ) -> tuple[AttackOrder, ...]:
        candidate_map = attack_candidates(
            world,
            params,
            available_treasury=available_treasury,
        )
        orders: list[AttackOrder] = []
        for attacker_id in sorted(candidate_map):
            candidates = candidate_map[attacker_id]
            if not candidates or candidates[0].security_ratio >= self.sufficiency_ratio:
                continue
            rescored: list[AttackOrder] = []
            for candidate in candidates:
                if candidate.expected_ratio < params.attack_threshold:
                    continue
                relative_threat = candidate.defender_power_share / max(
                    candidate.attacker_power_share,
                    1e-12,
                )
                score = (
                    candidate.expected_ratio
                    + self.threat_weight * relative_threat
                    + self.frontier_weight * candidate.border_relief / 6.0
                    + self.resource_weight * candidate.target_resource_ratio
                )
                rescored.append(
                    replace(
                        candidate,
                        score=float(score),
                        policy=self.name,
                        motive="security-repair",
                        security_target=self.sufficiency_ratio,
                        secure_at_attack=False,
                    )
                )
            if rescored:
                orders.append(_choose_best(rescored))
        return tuple(orders)


@dataclass(frozen=True, slots=True)
class PowerMaximizingPolicy:
    """Exploit feasible gains even after immediate security sufficiency is reached.

    The rule values prospective relative capability, productive territory, and
    weakening a powerful rival. It shares the security policy's feasibility
    threshold and every world mechanic; only the objective and stopping rule
    differ.
    """

    security_reference: float = 1.10
    relative_gain_weight: float = 80.0
    rival_power_weight: float = 1.00
    resource_weight: float = 0.12
    frontier_weight: float = 0.05
    name: str = "power-maximizing"

    def __post_init__(self) -> None:
        if self.security_reference <= 0.0:
            raise ValueError("security_reference must be positive")
        for value in (
            self.relative_gain_weight,
            self.rival_power_weight,
            self.resource_weight,
            self.frontier_weight,
        ):
            if value < 0.0:
                raise ValueError("policy weights must be non-negative")

    def propose_attacks(
        self,
        world: TerritorialWorld,
        params: TerritorialParameters,
        *,
        available_treasury: FloatVector | None = None,
    ) -> tuple[AttackOrder, ...]:
        candidate_map = attack_candidates(
            world,
            params,
            available_treasury=available_treasury,
        )
        orders: list[AttackOrder] = []
        for attacker_id in sorted(candidate_map):
            rescored: list[AttackOrder] = []
            for candidate in candidate_map[attacker_id]:
                if candidate.expected_ratio < params.attack_threshold:
                    continue
                score = (
                    candidate.expected_ratio
                    + self.relative_gain_weight * candidate.expected_relative_gain
                    + self.rival_power_weight * candidate.defender_power_share
                    + self.resource_weight * candidate.target_resource_ratio
                    + self.frontier_weight * candidate.border_relief / 6.0
                )
                rescored.append(
                    replace(
                        candidate,
                        score=float(score),
                        policy=self.name,
                        motive="relative-power-gain",
                        security_target=self.security_reference,
                        secure_at_attack=(
                            candidate.security_ratio >= self.security_reference
                        ),
                    )
                )
            if rescored:
                orders.append(_choose_best(rescored))
        return tuple(orders)


DEFAULT_POLICY = OpportunisticPolicy()


def propose_attacks(
    world: TerritorialWorld,
    params: TerritorialParameters,
    *,
    available_treasury: FloatVector | None = None,
) -> tuple[AttackOrder, ...]:
    """Backward-compatible entry point for the M2 opportunistic baseline."""
    return DEFAULT_POLICY.propose_attacks(
        world,
        params,
        available_treasury=available_treasury,
    )
