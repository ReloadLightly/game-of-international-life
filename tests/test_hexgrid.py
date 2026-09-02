import numpy as np
import pytest

from international_life.hexgrid import (
    connected_components,
    hex_distance,
    hex_neighbors,
    iter_hex_edges,
    labels_are_contiguous,
)


def test_odd_row_hex_neighborhood_has_six_interior_cells() -> None:
    neighbors = hex_neighbors((2, 2), (5, 5))
    assert len(neighbors) == 6
    assert len(set(neighbors)) == 6


def test_fixed_corner_has_only_valid_neighbors() -> None:
    assert set(hex_neighbors((0, 0), (4, 4))) == {(0, 1), (1, 0)}


def test_hex_distance_matches_neighbor_and_two_step_paths() -> None:
    assert hex_distance((2, 2), (2, 3)) == 1
    assert hex_distance((2, 2), (4, 3)) == 2


def test_iter_hex_edges_yields_each_edge_once() -> None:
    edges = list(iter_hex_edges((2, 2)))
    assert len(edges) == len(set(edges))
    assert len(edges) == 5


def test_connected_components_and_contiguity_are_hex_aware() -> None:
    labels = np.array(
        [
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1],
        ],
        dtype=np.int32,
    )
    assert len(connected_components(labels, 1)) == 2
    assert not labels_are_contiguous(labels)
    assert labels_are_contiguous(np.ones((3, 3), dtype=np.int32))


def test_wrapped_hex_grid_requires_even_height() -> None:
    with pytest.raises(ValueError, match="even number of rows"):
        hex_neighbors((0, 0), (3, 4), boundary="wrap")
