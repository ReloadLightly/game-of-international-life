import numpy as np
import pytest

from international_life.jervis import (
    JervisParameters,
    JervisWorld,
    history_metrics,
    initialize_jervis_world,
    perceived_threat,
    run_jervis,
)


def test_defensive_arming_is_less_threatening_when_distinguishable() -> None:
    arms = np.full((5, 5), 4, dtype=np.uint8)
    defensive = np.zeros((5, 5), dtype=np.bool_)
    conflict = np.zeros((5, 5), dtype=np.bool_)
    world = JervisWorld(arms=arms, offensive_posture=defensive, conflict=conflict)

    ambiguous = perceived_threat(
        world,
        JervisParameters(distinguishability=0.0, max_arms=6),
    )
    clear = perceived_threat(
        world,
        JervisParameters(distinguishability=1.0, max_arms=6),
    )
    assert np.all(ambiguous > clear)
    assert np.all(clear == 0.0)


def test_simulation_is_reproducible() -> None:
    params = JervisParameters(offense_advantage=0.4, distinguishability=0.3)
    first = run_jervis(initialize_jervis_world(seed=11), params, steps=20)[-1]
    second = run_jervis(initialize_jervis_world(seed=11), params, steps=20)[-1]
    assert np.array_equal(first.arms, second.arms)
    assert np.array_equal(first.conflict, second.conflict)


def test_doubly_dangerous_world_arms_more_than_doubly_safe_world() -> None:
    initial = initialize_jervis_world((24, 24), seed=7, offensive_share=0.08)
    dangerous = JervisParameters(offense_advantage=0.8, distinguishability=0.1)
    safe = JervisParameters(offense_advantage=-0.8, distinguishability=0.9)
    dangerous_metrics = history_metrics(run_jervis(initial, dangerous, steps=50), dangerous)
    safe_metrics = history_metrics(run_jervis(initial, safe, steps=50), safe)
    assert dangerous_metrics["final_mean_arms"] > safe_metrics["final_mean_arms"]
    assert dangerous_metrics["mean_conflict_rate"] >= safe_metrics["mean_conflict_rate"]


def test_invalid_parameter_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="distinguishability"):
        JervisParameters(distinguishability=1.2)
