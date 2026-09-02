import numpy as np
import pytest

from international_life.conway import conway_step, run_conway, seed_pattern


def test_block_is_still_life() -> None:
    block = seed_pattern((8, 8), "block")
    assert np.array_equal(conway_step(block, boundary="fixed"), block)


def test_blinker_has_period_two() -> None:
    blinker = seed_pattern((9, 9), "blinker")
    after_two = run_conway(blinker, steps=2, boundary="fixed")[-1]
    assert np.array_equal(after_two, blinker)


def test_glider_translates_after_four_generations() -> None:
    glider = seed_pattern((12, 12), "glider", origin=(2, 2))
    after_four = run_conway(glider, steps=4, boundary="fixed")[-1]
    expected = seed_pattern((12, 12), "glider", origin=(3, 3))
    assert np.array_equal(after_four, expected)


def test_non_binary_grid_is_rejected() -> None:
    with pytest.raises(ValueError, match="only 0 and 1"):
        conway_step(np.array([[0, 2], [1, 0]], dtype=np.uint8))
