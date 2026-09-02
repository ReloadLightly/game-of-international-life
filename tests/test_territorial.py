import numpy as np
import pytest

from international_life.hexgrid import labels_are_contiguous
from international_life.territorial import (
    TerritorialParameters,
    TerritorialWorld,
    border_edge_count,
    fragment_disconnected_polities,
    initialize_territorial_world,
    polity_production,
    run_territorial,
    territorial_metrics,
    territorial_step,
)


def _world(polities: np.ndarray, treasury: list[float]) -> TerritorialWorld:
    shape = polities.shape
    return TerritorialWorld(
        polities=polities.astype(np.int32),
        resources=np.ones(shape, dtype=np.float64),
        fortification=np.zeros(shape, dtype=np.float64),
        treasury=np.asarray(treasury, dtype=np.float64),
    )


def _decisive_params() -> TerritorialParameters:
    return TerritorialParameters(
        production_rate=0.0,
        reserve_decay=0.0,
        mobilization=1.0,
        offense_multiplier=1.0,
        defense_multiplier=1.0,
        support_bonus=0.0,
        garrison_strength=0.0,
        fortification_value=0.0,
        fortification_growth=0.0,
        fortification_cap=0.0,
        battle_damage=1.0,
        conquest_retention=1.0,
        attack_threshold=1.1,
        resource_attraction=0.0,
        attack_cost=0.0,
        defense_cost=0.0,
        battle_noise=0.0,
    )


def test_initial_world_is_reproducible_and_contiguous() -> None:
    first = initialize_territorial_world((12, 16), num_polities=7, seed=9)
    second = initialize_territorial_world((12, 16), num_polities=7, seed=9)
    assert np.array_equal(first.polities, second.polities)
    assert np.array_equal(first.resources, second.resources)
    assert np.array_equal(first.treasury, second.treasury)
    assert labels_are_contiguous(first.polities)
    assert len(np.unique(first.polities)) == 7


def test_cell_identity_is_stable_while_control_can_change() -> None:
    initial = _world(
        np.array(
            [
                [1, 1, 1],
                [1, 1, 2],
                [1, 1, 1],
            ]
        ),
        [0.0, 100.0, 1.0],
    )
    after = territorial_step(initial, _decisive_params())
    assert np.array_equal(initial.cell_ids, after.cell_ids)
    assert not np.array_equal(initial.polities, after.polities)
    assert after.extinctions == (2,)
    assert sum(event.conquered for event in after.battles) == 1


def test_local_resources_aggregate_to_polity_production() -> None:
    world = TerritorialWorld(
        polities=np.array([[1, 1], [2, 2]], dtype=np.int32),
        resources=np.array([[1.0, 2.0], [3.0, 4.0]]),
        fortification=np.zeros((2, 2)),
        treasury=np.zeros(3),
    )
    production = polity_production(world)
    assert production[1] == pytest.approx(3.0)
    assert production[2] == pytest.approx(7.0)


def test_disconnected_components_become_successor_polities() -> None:
    polities = np.array(
        [
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1],
        ],
        dtype=np.int32,
    )
    resources = np.ones((3, 3), dtype=np.float64)
    repaired, treasury, events = fragment_disconnected_polities(
        polities,
        resources,
        np.array([0.0, 9.0, 3.0]),
    )
    assert labels_are_contiguous(repaired)
    assert len(events) == 1
    assert events[0].parent_id == 1
    assert events[0].successor_id == 3
    assert treasury[1] == pytest.approx(4.5)
    assert treasury[3] == pytest.approx(4.5)


def test_metrics_measure_borders_and_capability_polarity() -> None:
    world = _world(np.array([[1, 2]]), [0.0, 1.0, 1.0])
    metrics = territorial_metrics(world)
    assert border_edge_count(world) == 1
    assert metrics["state_count"] == 2
    assert metrics["effective_powers"] == pytest.approx(2.0)
    assert metrics["largest_state_share"] == pytest.approx(0.5)


def test_fixed_seed_replays_the_same_territorial_history() -> None:
    params = TerritorialParameters(battle_seed=17)
    initial = initialize_territorial_world((10, 12), num_polities=5, seed=3)
    first = run_territorial(initial, params, steps=12)[-1]
    second = run_territorial(initial, params, steps=12)[-1]
    assert np.array_equal(first.polities, second.polities)
    assert np.array_equal(first.treasury, second.treasury)
    assert first.battles == second.battles


def test_invalid_world_rejects_missing_treasury_entry() -> None:
    with pytest.raises(ValueError, match="entry for every polity"):
        _world(np.array([[1, 2]]), [0.0, 1.0])


def test_territorial_parameters_reject_wrapped_transition_worlds() -> None:
    with pytest.raises(ValueError, match="fixed boundaries"):
        TerritorialParameters(boundary="wrap")
