from pathlib import Path

import numpy as np
import pytest

from international_life._territorial.dynamics import _resolve_battles
from international_life._territorial.types import AttackOrder
from international_life.experiments.structural_comparison import run_structural_comparison
from international_life.structural import (
    PowerMaximizingPolicy,
    SecuritySeekingPolicy,
    initialize_structural_world,
    world_fingerprint,
)
from international_life.territorial import (
    TerritorialParameters,
    TerritorialWorld,
    polity_capabilities,
    territorial_step,
)


def _two_state_world(treasury_one: float, treasury_two: float) -> TerritorialWorld:
    return TerritorialWorld(
        polities=np.array([[1, 2]], dtype=np.int32),
        resources=np.ones((1, 2), dtype=np.float64),
        fortification=np.zeros((1, 2), dtype=np.float64),
        treasury=np.array([0.0, treasury_one, treasury_two], dtype=np.float64),
    )


def _transparent_params(*, threshold: float = 1.0, noise: float = 0.0) -> TerritorialParameters:
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
        attack_threshold=threshold,
        resource_attraction=0.0,
        attack_cost=0.0,
        defense_cost=0.0,
        battle_noise=noise,
        battle_seed=11,
    )


def test_capability_regimes_hold_geography_fixed_and_set_exact_shares() -> None:
    balanced = initialize_structural_world(
        (8, 10),
        num_polities=4,
        seed=5,
        resource_regime="clustered",
        capability_regime="balanced",
    )
    dominant = initialize_structural_world(
        (8, 10),
        num_polities=4,
        seed=5,
        resource_regime="clustered",
        capability_regime="dominant-power",
        dominant_share=0.40,
    )
    assert np.array_equal(balanced.polities, dominant.polities)
    assert np.array_equal(balanced.resources, dominant.resources)
    balanced_capabilities = polity_capabilities(balanced)[1:]
    dominant_capabilities = polity_capabilities(dominant)[1:]
    assert balanced_capabilities / balanced_capabilities.sum() == pytest.approx(
        np.full(4, 0.25)
    )
    assert dominant_capabilities[0] / dominant_capabilities.sum() == pytest.approx(0.40)
    assert balanced_capabilities.sum() == pytest.approx(dominant_capabilities.sum())


def test_resource_regimes_change_resource_concentration_without_changing_borders() -> None:
    diffuse = initialize_structural_world(
        (8, 10),
        num_polities=4,
        seed=7,
        resource_regime="diffuse",
        capability_regime="balanced",
    )
    clustered = initialize_structural_world(
        (8, 10),
        num_polities=4,
        seed=7,
        resource_regime="clustered",
        capability_regime="balanced",
    )
    assert np.array_equal(diffuse.polities, clustered.polities)
    diffuse_cv = float(diffuse.resources.std() / diffuse.resources.mean())
    clustered_cv = float(clustered.resources.std() / clustered.resources.mean())
    assert clustered_cv > 3.0 * diffuse_cv


def test_security_seeker_abstains_but_power_maximizer_attacks_when_secure() -> None:
    world = _two_state_world(100.0, 1.0)
    params = _transparent_params(threshold=1.1)
    security = territorial_step(world, params, policy=SecuritySeekingPolicy())
    power = territorial_step(world, params, policy=PowerMaximizingPolicy())
    assert security.orders == ()
    assert len(power.orders) == 1
    assert power.orders[0].attacker_id == 1
    assert power.orders[0].secure_at_attack
    assert power.orders[0].motive == "relative-power-gain"


def test_security_seeker_can_attack_to_repair_a_security_deficit() -> None:
    world = _two_state_world(1.0, 3.0)
    params = _transparent_params(threshold=0.25)
    orders = SecuritySeekingPolicy().propose_attacks(world, params)
    order = next(order for order in orders if order.attacker_id == 1)
    assert order.security_ratio < order.security_target
    assert not order.secure_at_attack
    assert order.motive == "security-repair"


def test_battle_shock_is_keyed_to_encounter_not_order_list_position() -> None:
    world = _two_state_world(10.0, 10.0)
    params = _transparent_params(noise=0.2)
    available = world.treasury.copy()
    focal = AttackOrder(1, 2, (0, 1), 5.0, 4.0, 1.25, 1.25)
    extra = AttackOrder(2, 1, (0, 0), 4.0, 5.0, 0.8, 0.8)
    _, _, one_event = _resolve_battles(world, params, (focal,), available)
    _, _, two_events = _resolve_battles(world, params, (focal, extra), available)
    matching = next(event for event in two_events if event.attacker_id == 1)
    assert one_event[0].attack_strength == matching.attack_strength
    assert one_event[0].defense_strength == matching.defense_strength


def test_policy_runs_leave_the_matched_initial_world_unchanged() -> None:
    initial = initialize_structural_world((8, 10), num_polities=4, seed=1)
    before = world_fingerprint(initial)
    territorial_step(initial, TerritorialParameters(), policy=PowerMaximizingPolicy())
    territorial_step(initial, TerritorialParameters(), policy=SecuritySeekingPolicy())
    assert world_fingerprint(initial) == before


def test_m3_experiment_writes_paired_auditable_outputs(tmp_path: Path) -> None:
    paths = run_structural_comparison(
        tmp_path,
        steps=2,
        seeds=1,
        shape=(6, 8),
        num_polities=4,
        dominant_share=0.40,
    )
    assert all(path.is_file() for path in paths)
    assert (tmp_path / "m3_manifest.json").is_file()
    assert (tmp_path / "m3_war_cost.png").is_file()
    assert (tmp_path / "m3_attacks_while_secure.png").is_file()
    assert (tmp_path / "m3_power_concentration.png").is_file()
    assert (tmp_path / "m3_matched_worlds.png").is_file()
    manifest = (tmp_path / "m3_manifest.json").read_text(encoding="utf-8")
    assert "same_initial_world_within_policy_pair" in manifest
    assert "power-maximizing minus security-seeking" in manifest
    paired_lines = (tmp_path / "m3_paired_differences.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(paired_lines) == 5
