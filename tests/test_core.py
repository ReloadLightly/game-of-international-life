import numpy as np
import pytest

from international_life.core import moore_neighbors, moore_sum


def test_moore_sum_wrap_counts_all_neighbors() -> None:
    grid = np.ones((3, 3), dtype=np.uint8)
    assert np.all(moore_sum(grid, boundary="wrap") == 8)


def test_moore_neighbors_fixed_uses_fill_value() -> None:
    grid = np.ones((2, 2), dtype=np.uint8)
    neighbors = moore_neighbors(grid, boundary="fixed", fill_value=0)
    assert neighbors[:, 0, 0].sum() == 3


def test_invalid_boundary_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported boundary"):
        moore_sum(np.ones((3, 3)), boundary="edge")  # type: ignore[arg-type]
