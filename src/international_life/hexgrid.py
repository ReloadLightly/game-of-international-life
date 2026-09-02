"""Hexagonal-lattice utilities using an odd-row offset layout.

The territorial model stores cells in an ordinary ``(row, column)`` NumPy
array, while adjacency follows a six-neighbor hexagonal lattice. Odd-numbered
rows are shifted half a cell to the right. Fixed boundaries are the M2 default;
a toroidal option is provided for controlled topology experiments and requires
an even number of rows so the odd-row seam closes consistently.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator

import numpy as np
from numpy.typing import NDArray

from international_life.core import Boundary, validate_2d

HexCoordinate = tuple[int, int]

_EVEN_ROW_OFFSETS: tuple[HexCoordinate, ...] = (
    (-1, -1),
    (-1, 0),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
)
_ODD_ROW_OFFSETS: tuple[HexCoordinate, ...] = (
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, 0),
    (1, 1),
)


def validate_hex_shape(shape: tuple[int, int], *, boundary: Boundary = "fixed") -> None:
    """Validate dimensions and topology assumptions for an odd-row grid."""
    height, width = shape
    if height <= 0 or width <= 0:
        raise ValueError("shape dimensions must be positive")
    if boundary not in {"fixed", "wrap"}:
        raise ValueError(f"unsupported boundary mode: {boundary!r}")
    if boundary == "wrap" and height % 2:
        raise ValueError("a wrapped odd-row hex grid requires an even number of rows")


def hex_neighbors(
    coordinate: HexCoordinate,
    shape: tuple[int, int],
    *,
    boundary: Boundary = "fixed",
) -> tuple[HexCoordinate, ...]:
    """Return the six (or fewer at fixed edges) adjacent hex coordinates."""
    validate_hex_shape(shape, boundary=boundary)
    row, col = coordinate
    height, width = shape
    if not (0 <= row < height and 0 <= col < width):
        raise ValueError(f"coordinate {coordinate!r} lies outside shape {shape!r}")

    offsets = _ODD_ROW_OFFSETS if row % 2 else _EVEN_ROW_OFFSETS
    neighbors: list[HexCoordinate] = []
    for delta_row, delta_col in offsets:
        target_row = row + delta_row
        target_col = col + delta_col
        if boundary == "wrap":
            neighbors.append((target_row % height, target_col % width))
        elif 0 <= target_row < height and 0 <= target_col < width:
            neighbors.append((target_row, target_col))
    return tuple(neighbors)


def iter_hex_edges(
    shape: tuple[int, int],
    *,
    boundary: Boundary = "fixed",
) -> Iterator[tuple[HexCoordinate, HexCoordinate]]:
    """Yield each undirected adjacency edge exactly once."""
    validate_hex_shape(shape, boundary=boundary)
    seen: set[tuple[HexCoordinate, HexCoordinate]] = set()
    for row in range(shape[0]):
        for col in range(shape[1]):
            source = (row, col)
            for target in hex_neighbors(source, shape, boundary=boundary):
                edge = tuple(sorted((source, target)))
                if edge not in seen:
                    seen.add(edge)
                    yield edge


def odd_r_to_cube(coordinate: HexCoordinate) -> tuple[int, int, int]:
    """Convert odd-row offset coordinates to integer cube coordinates."""
    row, col = coordinate
    x_coord = col - (row - (row & 1)) // 2
    z_coord = row
    y_coord = -x_coord - z_coord
    return x_coord, y_coord, z_coord


def hex_distance(first: HexCoordinate, second: HexCoordinate) -> int:
    """Return shortest-path distance on an unbounded odd-row hex lattice."""
    first_cube = odd_r_to_cube(first)
    second_cube = odd_r_to_cube(second)
    return max(abs(left - right) for left, right in zip(first_cube, second_cube, strict=True))


def connected_components(
    labels: NDArray[np.integer],
    label: int,
    *,
    boundary: Boundary = "fixed",
) -> tuple[tuple[HexCoordinate, ...], ...]:
    """Return all six-neighbor connected components carrying ``label``."""
    validate_2d(labels, name="labels")
    validate_hex_shape(labels.shape, boundary=boundary)
    cells = {tuple(index) for index in np.argwhere(labels == label)}
    components: list[tuple[HexCoordinate, ...]] = []

    while cells:
        start = min(cells)
        cells.remove(start)
        queue: deque[HexCoordinate] = deque([start])
        component: list[HexCoordinate] = []
        while queue:
            coordinate = queue.popleft()
            component.append(coordinate)
            for neighbor in hex_neighbors(coordinate, labels.shape, boundary=boundary):
                if neighbor in cells:
                    cells.remove(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(component)))

    components.sort(
        key=lambda component: (-len(component), component[0] if component else (-1, -1))
    )
    return tuple(components)


def labels_are_contiguous(
    labels: NDArray[np.integer],
    *,
    boundary: Boundary = "fixed",
    ignore_label: int | None = None,
) -> bool:
    """Return whether every represented label occupies one connected component."""
    validate_2d(labels, name="labels")
    for label in np.unique(labels):
        value = int(label)
        if ignore_label is not None and value == ignore_label:
            continue
        if len(connected_components(labels, value, boundary=boundary)) != 1:
            return False
    return True
