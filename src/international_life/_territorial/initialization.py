"""Connected territorial-map and resource-field initialization."""

from __future__ import annotations

from collections import deque

import numpy as np

from international_life._territorial.types import FloatGrid, PolityGrid, TerritorialWorld
from international_life.hexgrid import (
    HexCoordinate,
    hex_distance,
    hex_neighbors,
    labels_are_contiguous,
    validate_hex_shape,
)


def _well_spaced_seeds(
    shape: tuple[int, int],
    count: int,
    *,
    rng: np.random.Generator,
) -> tuple[HexCoordinate, ...]:
    coordinates = [(row, col) for row in range(shape[0]) for col in range(shape[1])]
    first = coordinates[int(rng.integers(len(coordinates)))]
    seeds = [first]
    remaining = set(coordinates)
    remaining.remove(first)

    while len(seeds) < count:
        distances = {
            coordinate: min(hex_distance(coordinate, seed) for seed in seeds)
            for coordinate in remaining
        }
        farthest = max(distances.values())
        candidates = sorted(
            coordinate for coordinate, distance in distances.items() if distance == farthest
        )
        selected = candidates[int(rng.integers(len(candidates)))]
        seeds.append(selected)
        remaining.remove(selected)
    return tuple(seeds)


def _grow_polities(
    shape: tuple[int, int],
    seeds: tuple[HexCoordinate, ...],
) -> PolityGrid:
    """Grow connected territories by deterministic multi-source local expansion."""
    polities = np.zeros(shape, dtype=np.int32)
    queue: deque[HexCoordinate] = deque()
    for polity_id, coordinate in enumerate(seeds, start=1):
        polities[coordinate] = polity_id
        queue.append(coordinate)

    while queue:
        coordinate = queue.popleft()
        polity_id = int(polities[coordinate])
        for neighbor in hex_neighbors(coordinate, shape, boundary="fixed"):
            if polities[neighbor] == 0:
                polities[neighbor] = polity_id
                queue.append(neighbor)
    return polities


def _resource_field(
    shape: tuple[int, int],
    *,
    rng: np.random.Generator,
    dispersion: float,
    smoothing: float,
) -> FloatGrid:
    resources = rng.lognormal(mean=0.0, sigma=dispersion, size=shape).astype(np.float64)
    if smoothing:
        neighbor_mean = np.empty(shape, dtype=np.float64)
        for row in range(shape[0]):
            for col in range(shape[1]):
                neighbors = hex_neighbors((row, col), shape, boundary="fixed")
                values = [resources[neighbor] for neighbor in neighbors]
                neighbor_mean[row, col] = float(np.mean(values)) if values else resources[row, col]
        resources = (1.0 - smoothing) * resources + smoothing * neighbor_mean
    return resources / resources.mean()


def initialize_territorial_world(
    shape: tuple[int, int] = (24, 32),
    *,
    num_polities: int = 10,
    seed: int = 0,
    resource_dispersion: float = 0.45,
    resource_smoothing: float = 0.55,
    initial_fortification: float = 0.35,
    initial_reserve_turns: float = 1.75,
) -> TerritorialWorld:
    """Create a reproducible connected-state map and local resource field."""
    validate_hex_shape(shape, boundary="fixed")
    cell_count = shape[0] * shape[1]
    if not 1 <= num_polities <= cell_count:
        raise ValueError("num_polities must lie in [1, number of cells]")
    if resource_dispersion < 0.0:
        raise ValueError("resource_dispersion must be non-negative")
    if not 0.0 <= resource_smoothing <= 1.0:
        raise ValueError("resource_smoothing must lie in [0, 1]")
    if initial_fortification < 0.0:
        raise ValueError("initial_fortification must be non-negative")
    if initial_reserve_turns < 0.0:
        raise ValueError("initial_reserve_turns must be non-negative")

    rng = np.random.default_rng(seed)
    seeds = _well_spaced_seeds(shape, num_polities, rng=rng)
    polities = _grow_polities(shape, seeds)
    resources = _resource_field(
        shape,
        rng=rng,
        dispersion=resource_dispersion,
        smoothing=resource_smoothing,
    )
    fortification = np.full(shape, initial_fortification, dtype=np.float64)
    production = np.bincount(
        polities.ravel(),
        weights=resources.ravel(),
        minlength=num_polities + 1,
    ).astype(np.float64)
    treasury = initial_reserve_turns * production
    treasury[0] = 0.0

    world = TerritorialWorld(
        polities=polities,
        resources=resources,
        fortification=fortification,
        treasury=treasury,
    )
    if not labels_are_contiguous(world.polities):
        raise AssertionError("multi-source growth produced a disconnected initial polity")
    return world
