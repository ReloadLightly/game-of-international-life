from dataclasses import replace

import numpy as np
import pytest

from international_life.alliances import (
    AllianceDoctrine,
    alliance_edges,
    alliance_metrics,
    alliance_step,
    alliance_world_fingerprint,
    doctrine_for,
    initialize_alliance_world,
    run_alliance,
)
from international_life.territorial import TerritorialParameters, polity_capabilities


def _params() -> TerritorialParameters:
    return TerritorialParameters(
        offense_multiplier=1.10,
        defense_multiplier=1.05,
        attack_threshold=0.82,
        battle_noise=0.0,
        battle_seed=17,
    )


def test_initial_alliance_world_is_reproducible_and_matched() -> None:
    first = initialize_alliance_world(seed=4, polarity="bipolar", threat_regime="diffuse")
    second = initialize_alliance_world(seed=4, polarity="bipolar", threat_regime="diffuse")
    assert alliance_world_fingerprint(first) == alliance_world_fingerprint(second)
    assert np.array_equal(first.commitments, second.commitments)
    assert len(alliance_edges(first)) == 12
    assert first.commitments.shape == (
        len(first.territorial.treasury),
        len(first.territorial.treasury),
    )


def test_default_polarity_topologies_hold_initial_edge_count_constant() -> None:
    bipolar = initialize_alliance_world(
        seed=3,
        polarity="bipolar",
        threat_regime="concentrated",
    )
    multipolar = initialize_alliance_world(
        seed=3,
        polarity="multipolar",
        threat_regime="concentrated",
    )
    assert len(alliance_edges(bipolar)) == len(alliance_edges(multipolar)) == 12


def test_active_allies_are_not_selected_as_primary_targets() -> None:
    initial = initialize_alliance_world(
        seed=2,
        polarity="multipolar",
        threat_regime="diffuse",
    )
    commitments = np.full_like(initial.commitments, 0.80)
    np.fill_diagonal(commitments, 0.0)
    fully_allied = replace(initial, commitments=commitments)
    after = alliance_step(fully_allied, _params(), doctrine_for("binding"))
    assert after.crises == ()
    assert after.territorial.orders == ()


def test_polarity_treatments_construct_exact_capability_shares() -> None:
    bipolar = initialize_alliance_world(seed=2, polarity="bipolar", threat_regime="diffuse")
    multipolar = initialize_alliance_world(
        seed=2,
        polarity="multipolar",
        threat_regime="diffuse",
    )
    bipolar_caps = polity_capabilities(bipolar.territorial)[1:]
    multipolar_caps = polity_capabilities(multipolar.territorial)[1:]
    assert np.sort(bipolar_caps / bipolar_caps.sum())[-2:] == pytest.approx([0.30, 0.30])
    assert np.sort(multipolar_caps / multipolar_caps.sum())[-4:] == pytest.approx(
        [0.20, 0.20, 0.20, 0.20]
    )


def test_binding_commitments_mobilize_both_sides_while_flexible_scope_does_not() -> None:
    initial = initialize_alliance_world(
        seed=0,
        polarity="bipolar",
        threat_regime="diffuse",
    )
    binding = alliance_step(initial, _params(), doctrine_for("binding"))
    flexible = alliance_step(initial, _params(), doctrine_for("flexible"))

    assert binding.crises[0].chain_ganging
    assert not flexible.crises[0].chain_ganging
    assert any(
        event.side == "attacker" and event.action != "withhold"
        for event in binding.support_events
    )
    assert all(
        event.side != "attacker" or event.action == "withhold"
        for event in flexible.support_events
    )
    assert alliance_metrics(binding)["third_party_participations"] > alliance_metrics(
        flexible
    )["third_party_participations"]


def test_repeated_flexible_withholding_generates_abandonment_and_turnover() -> None:
    initial = initialize_alliance_world(
        seed=0,
        polarity="multipolar",
        threat_regime="diffuse",
    )
    history = run_alliance(initial, _params(), doctrine_for("flexible"), steps=18)
    cumulative_abandonment = sum(
        int(alliance_metrics(world)["abandonment_events"]) for world in history[1:]
    )
    cumulative_dissolution = sum(
        int(alliance_metrics(world)["alliance_dissolutions"]) for world in history[1:]
    )
    assert cumulative_abandonment > 0
    assert cumulative_dissolution > 0


def test_binding_rule_exhibits_entrapment_in_diffuse_multipolar_world() -> None:
    initial = initialize_alliance_world(
        seed=1,
        polarity="multipolar",
        threat_regime="diffuse",
    )
    history = run_alliance(initial, _params(), doctrine_for("binding"), steps=20)
    entrapment = sum(
        int(alliance_metrics(world)["entrapment_events"]) for world in history[1:]
    )
    assert entrapment > 0


def test_alliance_history_replays_exactly_and_preserves_matrix_invariants() -> None:
    initial = initialize_alliance_world(
        seed=3,
        polarity="multipolar",
        threat_regime="concentrated",
    )
    doctrine = doctrine_for("flexible")
    first = run_alliance(initial, _params(), doctrine, steps=15)[-1]
    second = run_alliance(initial, _params(), doctrine, steps=15)[-1]
    assert np.array_equal(first.territorial.polities, second.territorial.polities)
    assert np.array_equal(first.territorial.treasury, second.territorial.treasury)
    assert np.array_equal(first.commitments, second.commitments)
    assert first.support_events == second.support_events
    for matrix in (first.commitments, first.reliability, first.threats):
        assert matrix.shape[0] >= len(first.territorial.treasury)
        assert np.all((matrix >= 0.0) & (matrix <= 1.0))
        assert np.all(np.diag(matrix) == 0.0)


def test_doctrine_validation_rejects_inverted_support_thresholds() -> None:
    with pytest.raises(ValueError, match="partial support threshold"):
        AllianceDoctrine(
            name="binding",
            defensive_scope=1.0,
            offensive_scope=1.0,
            full_support_threshold=0.4,
            partial_support_threshold=0.6,
            entrapment_aversion=0.1,
            relation_learning_rate=0.1,
        )


def test_binding_reduces_abandonment_but_increases_entrapment_in_one_matched_world() -> None:
    initial = initialize_alliance_world(
        seed=0,
        polarity="multipolar",
        threat_regime="diffuse",
    )
    binding = run_alliance(initial, _params(), doctrine_for("binding"), steps=12)
    flexible = run_alliance(initial, _params(), doctrine_for("flexible"), steps=12)

    binding_abandonment = sum(
        int(alliance_metrics(world)["abandonment_events"]) for world in binding[1:]
    )
    flexible_abandonment = sum(
        int(alliance_metrics(world)["abandonment_events"]) for world in flexible[1:]
    )
    binding_entrapment = sum(
        int(alliance_metrics(world)["entrapment_events"]) for world in binding[1:]
    )
    flexible_entrapment = sum(
        int(alliance_metrics(world)["entrapment_events"]) for world in flexible[1:]
    )

    assert binding_abandonment < flexible_abandonment
    assert binding_entrapment > flexible_entrapment
