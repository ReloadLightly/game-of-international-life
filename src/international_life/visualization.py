"""Small plotting helpers kept separate from model logic."""

from __future__ import annotations

from math import sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import RegularPolygon
from numpy.typing import NDArray

from international_life.jervis import JervisParameters, JervisWorld
from international_life.territorial import TerritorialWorld, territorial_metrics


def save_binary_grid(grid: NDArray[np.generic], path: Path, *, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.imshow(grid, interpolation="nearest", vmin=0, vmax=1)
    axis.set_title(title)
    axis.set_xticks([])
    axis.set_yticks([])
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def save_jervis_arms(
    world: JervisWorld,
    params: JervisParameters,
    path: Path,
    *,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(
        world.arms,
        interpolation="nearest",
        vmin=0,
        vmax=params.max_arms,
    )
    axis.set_title(title)
    axis.set_xticks([])
    axis.set_yticks([])
    figure.colorbar(image, ax=axis, label="arms level")
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _hex_center(row: int, col: int) -> tuple[float, float]:
    return sqrt(3.0) * (col + 0.5 * (row % 2)), 1.5 * row


def save_territorial_map(
    world: TerritorialWorld,
    path: Path,
    *,
    title: str,
) -> None:
    """Render the odd-row M2 array as an actual six-neighbor hex map."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure_width = max(7.0, world.shape[1] * 0.28)
    figure_height = max(5.0, world.shape[0] * 0.26)
    figure, axis = plt.subplots(figsize=(figure_width, figure_height))

    patches = []
    values = []
    for row in range(world.shape[0]):
        for col in range(world.shape[1]):
            patches.append(
                RegularPolygon(
                    _hex_center(row, col),
                    numVertices=6,
                    radius=1.0,
                    orientation=0.0,
                )
            )
            values.append(float((int(world.polities[row, col]) - 1) % 20))

    collection = PatchCollection(
        patches,
        array=np.asarray(values),
        cmap="tab20",
        edgecolor="black",
        linewidth=0.18,
    )
    collection.set_clim(-0.5, 19.5)
    axis.add_collection(collection)
    axis.autoscale_view()
    axis.set_aspect("equal")
    axis.invert_yaxis()
    axis.set_xticks([])
    axis.set_yticks([])

    metrics = territorial_metrics(world)
    axis.set_title(
        f"{title}\n"
        f"states={metrics['state_count']}, effective powers={metrics['effective_powers']:.2f}, "
        f"conquests={metrics['conquests']}"
    )
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
