"""Shared lattice utilities.

The implementation keeps the update semantics deliberately explicit:
all cells read generation *t* and are written simultaneously to generation
*t + 1*. This is essential for standard cellular automata.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import NDArray

Boundary = Literal["wrap", "fixed"]

MOORE_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


def validate_2d(array: NDArray[np.generic], *, name: str = "array") -> None:
    """Raise a clear error when a lattice is not a non-empty 2-D array."""
    if array.ndim != 2:
        raise ValueError(f"{name} must be two-dimensional; got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty")


def moore_neighbors(
    values: NDArray[np.generic],
    *,
    boundary: Boundary = "wrap",
    fill_value: int | float | bool = 0,
) -> NDArray[np.generic]:
    """Return the eight Moore-neighborhood layers with shape ``(8, H, W)``.

    ``wrap`` produces a torus, avoiding privileged edges. ``fixed`` treats
    positions outside the grid as ``fill_value``.
    """
    validate_2d(values, name="values")
    if boundary not in {"wrap", "fixed"}:
        raise ValueError(f"unsupported boundary mode: {boundary!r}")

    if boundary == "wrap":
        layers = [np.roll(values, shift=(-dr, -dc), axis=(0, 1)) for dr, dc in MOORE_OFFSETS]
        return np.stack(layers, axis=0)

    padded = np.pad(values, pad_width=1, mode="constant", constant_values=fill_value)
    height, width = values.shape
    layers = [
        padded[1 + dr : 1 + dr + height, 1 + dc : 1 + dc + width]
        for dr, dc in MOORE_OFFSETS
    ]
    return np.stack(layers, axis=0)


def moore_sum(
    values: NDArray[np.generic],
    *,
    boundary: Boundary = "wrap",
    fill_value: int | float | bool = 0,
) -> NDArray[np.generic]:
    """Sum values in each cell's Moore neighborhood."""
    return moore_neighbors(values, boundary=boundary, fill_value=fill_value).sum(axis=0)
