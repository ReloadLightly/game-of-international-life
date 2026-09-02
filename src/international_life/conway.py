"""A faithful Conway's Game of Life baseline (B3/S23)."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

from international_life.core import Boundary, moore_sum, validate_2d

BinaryGrid = NDArray[np.uint8]

PATTERNS: dict[str, tuple[tuple[int, int], ...]] = {
    "block": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "blinker": ((0, 0), (0, 1), (0, 2)),
    "glider": ((0, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    "r_pentomino": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
}


def _as_binary(grid: NDArray[np.generic]) -> BinaryGrid:
    validate_2d(grid, name="grid")
    unique = np.unique(grid)
    if not np.isin(unique, (0, 1)).all():
        raise ValueError(f"Conway grid must contain only 0 and 1; got values {unique.tolist()}")
    return grid.astype(np.uint8, copy=False)


def conway_step(grid: NDArray[np.generic], *, boundary: Boundary = "wrap") -> BinaryGrid:
    """Advance Conway's Life by one simultaneous B3/S23 update."""
    current = _as_binary(grid)
    neighbors = moore_sum(current, boundary=boundary)
    survives = (current == 1) & ((neighbors == 2) | (neighbors == 3))
    born = (current == 0) & (neighbors == 3)
    return (survives | born).astype(np.uint8)


def run_conway(
    initial: NDArray[np.generic],
    *,
    steps: int,
    boundary: Boundary = "wrap",
    include_initial: bool = True,
) -> list[BinaryGrid]:
    """Run Life and return independent snapshots."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    current = _as_binary(initial).copy()
    history: list[BinaryGrid] = [current.copy()] if include_initial else []
    for _ in range(steps):
        current = conway_step(current, boundary=boundary)
        history.append(current.copy())
    return history


def seed_pattern(
    shape: tuple[int, int],
    pattern: str | Iterable[tuple[int, int]],
    *,
    origin: tuple[int, int] | None = None,
) -> BinaryGrid:
    """Place a named or explicit pattern on an otherwise empty lattice."""
    height, width = shape
    if height <= 0 or width <= 0:
        raise ValueError("shape dimensions must be positive")
    cells = PATTERNS.get(pattern) if isinstance(pattern, str) else tuple(pattern)
    if cells is None:
        available = ", ".join(sorted(PATTERNS))
        raise ValueError(f"unknown pattern {pattern!r}; choose one of: {available}")

    max_row = max(row for row, _ in cells)
    max_col = max(col for _, col in cells)
    if origin is None:
        origin = ((height - max_row - 1) // 2, (width - max_col - 1) // 2)

    grid = np.zeros(shape, dtype=np.uint8)
    for row, col in cells:
        target_row = origin[0] + row
        target_col = origin[1] + col
        if not (0 <= target_row < height and 0 <= target_col < width):
            raise ValueError("pattern does not fit inside the requested lattice")
        grid[target_row, target_col] = 1
    return grid
