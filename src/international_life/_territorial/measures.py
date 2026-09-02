"""Polity aggregation, borders, and system-level territorial observables."""

from __future__ import annotations

from statistics import fmean

import numpy as np
from numpy.typing import NDArray

from international_life._territorial.types import (
    FloatVector,
    TerritorialParameters,
    TerritorialWorld,
)
from international_life.hexgrid import HexCoordinate, iter_hex_edges


def alive_polities(world: TerritorialWorld) -> NDArray[np.int32]:
    """Return sorted currently represented polity IDs."""
    return np.unique(world.polities).astype(np.int32)


def polity_cell_counts(world: TerritorialWorld) -> NDArray[np.int64]:
    """Count controlled cells for every historical polity ID."""
    return np.bincount(world.polities.ravel(), minlength=len(world.treasury)).astype(np.int64)


def polity_production(world: TerritorialWorld) -> FloatVector:
    """Aggregate fixed local resource production by current polity control."""
    return np.bincount(
        world.polities.ravel(),
        weights=world.resources.ravel(),
        minlength=len(world.treasury),
    ).astype(np.float64)


def polity_capabilities(world: TerritorialWorld) -> FloatVector:
    """Return treasury plus one turn of gross production for each polity."""
    return world.treasury + polity_production(world)


def _border_cells(world: TerritorialWorld) -> dict[int, set[HexCoordinate]]:
    borders: dict[int, set[HexCoordinate]] = {
        int(polity_id): set() for polity_id in alive_polities(world)
    }
    for first, second in iter_hex_edges(world.shape, boundary="fixed"):
        first_id = int(world.polities[first])
        second_id = int(world.polities[second])
        if first_id != second_id:
            borders[first_id].add(first)
            borders[second_id].add(second)
    return borders


def _available_treasury(world: TerritorialWorld, params: TerritorialParameters) -> FloatVector:
    production = polity_production(world)
    available = world.treasury * (1.0 - params.reserve_decay)
    available = available + params.production_rate * production
    available[0] = 0.0
    return available


def border_edge_count(world: TerritorialWorld) -> int:
    """Count undirected hex edges crossing a polity boundary."""
    return sum(
        int(world.polities[first]) != int(world.polities[second])
        for first, second in iter_hex_edges(world.shape, boundary="fixed")
    )


def resource_coefficient_of_variation(world: TerritorialWorld) -> float:
    """Return a scale-free measure of spatial resource inequality."""
    return float(world.resources.std() / world.resources.mean())


def territorial_metrics(world: TerritorialWorld) -> dict[str, int | float | str]:
    """Compute state-size, polarity, border, war, and policy-process observables."""
    counts = polity_cell_counts(world)
    ids = alive_polities(world)
    sizes = counts[ids].astype(np.float64)
    capabilities = polity_capabilities(world)[ids]
    capability_total = float(capabilities.sum())
    if capability_total > 0.0:
        shares = capabilities / capability_total
        power_hhi = float(np.square(shares).sum())
        largest_power_share = float(shares.max())
        effective_powers = float(1.0 / power_hhi)
    else:
        power_hhi = 0.0
        largest_power_share = 0.0
        effective_powers = 0.0

    conquests = sum(event.conquered for event in world.battles)
    security_ratios = [order.security_ratio for order in world.orders]
    return {
        "generation": world.generation,
        "policy": world.policy_name,
        "state_count": int(len(ids)),
        "mean_state_size": float(sizes.mean()),
        "largest_state_size": int(sizes.max()),
        "largest_state_share": float(sizes.max() / world.polities.size),
        "power_hhi": power_hhi,
        "effective_powers": effective_powers,
        "largest_power_share": largest_power_share,
        "resource_cv": resource_coefficient_of_variation(world),
        "border_edges": border_edge_count(world),
        "attack_orders": len(world.orders),
        "battle_count": len(world.battles),
        "successful_battles": sum(event.success for event in world.battles),
        "conquests": conquests,
        "territorial_turnover": float(conquests / world.polities.size),
        "war_cost": float(
            sum(event.attacker_cost + event.defender_cost for event in world.battles)
        ),
        "attacks_while_secure": sum(order.secure_at_attack for order in world.orders),
        "security_repair_attacks": sum(
            order.motive == "security-repair" for order in world.orders
        ),
        "relative_power_attacks": sum(
            order.motive == "relative-power-gain" for order in world.orders
        ),
        "mean_attacker_security_ratio": (
            float(fmean(security_ratios)) if security_ratios else 0.0
        ),
        "extinctions": len(world.extinctions),
        "fragmentations": len(world.fragmentations),
    }
