"""Alliance crisis transition and M4 simulation runner."""

from __future__ import annotations

from dataclasses import replace

from international_life._alliances.relations import (
    inherit_successor_relations,
    update_relations,
)
from international_life._alliances.support import primary_order, support_events
from international_life._alliances.types import (
    AllianceCrisisEvent,
    AllianceDoctrine,
    AllianceWorld,
    SupportEvent,
)
from international_life._territorial.types import AttackOrder, TerritorialParameters
from international_life.territorial import territorial_step_from_orders


def alliance_step(
    world: AllianceWorld,
    params: TerritorialParameters,
    doctrine: AllianceDoctrine,
) -> AllianceWorld:
    """Advance one alliance crisis through the shared territorial resolver."""
    primary = primary_order(world, params, doctrine)
    events: tuple[SupportEvent, ...] = ()
    orders: tuple[AttackOrder, ...] = ()
    treasury = world.territorial.treasury.copy()

    if primary is not None:
        events = support_events(world, doctrine, primary)
        attack_support = sum(
            event.contribution
            for event in events
            if event.side == "attacker" and event.action != "withhold"
        )
        defense_support = sum(
            event.contribution
            for event in events
            if event.side == "defender" and event.action != "withhold"
        )
        for event in events:
            treasury[event.supporter_id] = max(
                0.0,
                treasury[event.supporter_id] - event.cost,
            )
        primary = replace(
            primary,
            predicted_attack=float(primary.predicted_attack + attack_support),
            predicted_defense=float(primary.predicted_defense + defense_support),
            expected_ratio=float(
                (primary.predicted_attack + attack_support)
                / max(primary.predicted_defense + defense_support, 1e-12)
            ),
            policy=f"alliance-{doctrine.name}",
            motive="alliance-crisis",
        )
        orders = (primary,)

    territorial = territorial_step_from_orders(
        replace(world.territorial, treasury=treasury),
        params,
        orders=orders,
        policy_name=f"alliance-{doctrine.name}",
    )
    commitments, reliability, changes = update_relations(world, doctrine, events)
    commitments, reliability, threats = inherit_successor_relations(
        commitments,
        reliability,
        world.threats,
        world.commitments.shape[0],
        territorial,
        doctrine,
    )

    crises: tuple[AllianceCrisisEvent, ...] = ()
    if primary is not None and territorial.battles:
        attacker_supporters = tuple(
            sorted(
                event.supporter_id
                for event in events
                if event.side == "attacker" and event.action != "withhold"
            )
        )
        defender_supporters = tuple(
            sorted(
                event.supporter_id
                for event in events
                if event.side == "defender" and event.action != "withhold"
            )
        )
        battle = territorial.battles[0]
        third_parties = len(set(attacker_supporters) | set(defender_supporters))
        crises = (
            AllianceCrisisEvent(
                primary.attacker_id,
                primary.defender_id,
                primary.target,
                attacker_supporters,
                defender_supporters,
                2 + third_parties,
                bool(attacker_supporters) and bool(defender_supporters),
                battle.success,
                battle.conquered,
            ),
        )

    return AllianceWorld(
        territorial=territorial,
        commitments=commitments,
        reliability=reliability,
        threats=threats,
        polarity=world.polarity,
        threat_regime=world.threat_regime,
        focal_threat_id=world.focal_threat_id,
        doctrine_name=doctrine.name,
        support_events=events,
        crises=crises,
        alliance_changes=changes,
    )


def run_alliance(
    initial: AllianceWorld,
    params: TerritorialParameters,
    doctrine: AllianceDoctrine,
    *,
    steps: int,
    include_initial: bool = True,
) -> list[AllianceWorld]:
    """Run M4 and return independent alliance-world snapshots."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    current = replace(initial.copy(), doctrine_name=doctrine.name)
    history = [current.copy()] if include_initial else []
    for _ in range(steps):
        current = alliance_step(current, params, doctrine)
        history.append(current.copy())
    return history
