"""Primary-crisis selection and third-party support decisions for M4."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from international_life._alliances.types import (
    AllianceDoctrine,
    AllianceWorld,
    SupportAction,
    SupportEvent,
    SupportSide,
)
from international_life._territorial.measures import alive_polities, polity_capabilities
from international_life._territorial.policy import attack_candidates
from international_life._territorial.types import AttackOrder, TerritorialParameters


def _edge_strength(world: AllianceWorld, first: int, second: int) -> float:
    return float(min(world.commitments[first, second], world.commitments[second, first]))


def active_allies(
    world: AllianceWorld,
    polity_id: int,
    threshold: float,
) -> tuple[int, ...]:
    """Return reciprocal allies above a commitment threshold."""
    alive = {int(value) for value in alive_polities(world.territorial)}
    return tuple(
        other
        for other in sorted(alive)
        if other != polity_id and _edge_strength(world, polity_id, other) >= threshold
    )


def primary_order(
    world: AllianceWorld,
    params: TerritorialParameters,
    doctrine: AllianceDoctrine,
) -> AttackOrder | None:
    """Select one feasible non-allied territorial crisis."""
    choices: list[AttackOrder] = []
    for attacker_id, candidates in attack_candidates(world.territorial, params).items():
        allies = set(active_allies(world, attacker_id, doctrine.alliance_threshold))
        for candidate in candidates:
            if candidate.defender_id in allies:
                continue
            if candidate.expected_ratio < params.attack_threshold:
                continue
            threat_bonus = 0.55 * float(world.threats[attacker_id, candidate.defender_id])
            choices.append(
                replace(
                    candidate,
                    score=float(candidate.score + threat_bonus),
                    policy="alliance-crisis",
                    motive="primary-crisis",
                )
            )
    if not choices:
        return None
    return max(
        choices,
        key=lambda order: (
            order.score,
            order.expected_ratio,
            world.threats[order.attacker_id, order.defender_id],
            -order.attacker_id,
            -order.target[0],
            -order.target[1],
        ),
    )


def _request_score(
    world: AllianceWorld,
    doctrine: AllianceDoctrine,
    *,
    supporter_id: int,
    principal_id: int,
    opponent_id: int,
    side: SupportSide,
    capabilities: np.ndarray,
) -> tuple[float, float, float, float, float]:
    commitment = float(world.commitments[principal_id, supporter_id])
    reliability = float(world.reliability[principal_id, supporter_id])
    direct_threat = float(world.threats[supporter_id, opponent_id])
    principal_capability = float(capabilities[principal_id])
    supporter_capability = float(capabilities[supporter_id])
    opponent_capability = float(capabilities[opponent_id])
    dependence = principal_capability / max(
        principal_capability + supporter_capability,
        1e-12,
    )
    own_security_ratio = supporter_capability / max(opponent_capability, 1e-12)
    scope = doctrine.defensive_scope if side == "defender" else doctrine.offensive_scope
    commitment_scope = scope if side == "attacker" else 1.0
    score = (
        0.55 * commitment * commitment_scope
        + 0.35 * scope
        + 0.25 * direct_threat
        + 0.15 * dependence
        + 0.15 * reliability
        - doctrine.entrapment_aversion * (1.0 - direct_threat)
    )
    return score, commitment, reliability, dependence, own_security_ratio


def _support_event(
    world: AllianceWorld,
    doctrine: AllianceDoctrine,
    *,
    supporter_id: int,
    principal_id: int,
    opponent_id: int,
    side: SupportSide,
    capabilities: np.ndarray,
) -> SupportEvent:
    score, commitment, reliability, dependence, own_security_ratio = _request_score(
        world,
        doctrine,
        supporter_id=supporter_id,
        principal_id=principal_id,
        opponent_id=opponent_id,
        side=side,
        capabilities=capabilities,
    )
    direct_threat = float(world.threats[supporter_id, opponent_id])
    action: SupportAction
    if score >= doctrine.full_support_threshold:
        action, fraction = "full", doctrine.support_fraction
    elif score >= doctrine.partial_support_threshold:
        action, fraction = "partial", doctrine.partial_support_fraction
    else:
        action, fraction = "withhold", 0.0
    contribution = fraction * float(capabilities[supporter_id])
    cost = doctrine.support_cost_rate * contribution
    return SupportEvent(
        supporter_id=supporter_id,
        principal_id=principal_id,
        opponent_id=opponent_id,
        side=side,
        action=action,
        score=float(score),
        contribution=float(contribution),
        cost=float(cost),
        commitment=commitment,
        reliability=reliability,
        dependence=float(dependence),
        direct_threat=direct_threat,
        own_security_ratio=float(own_security_ratio),
        abandonment=(
            side == "defender"
            and commitment >= doctrine.alliance_threshold
            and action != "full"
        ),
        entrapment=(
            side == "attacker" and action != "withhold" and direct_threat < 0.35
        ),
        buck_passing=(
            side == "defender" and action == "withhold" and direct_threat >= 0.55
        ),
    )


def support_events(
    world: AllianceWorld,
    doctrine: AllianceDoctrine,
    order: AttackOrder,
) -> tuple[SupportEvent, ...]:
    """Evaluate all alliance requests generated by one primary crisis."""
    capabilities = polity_capabilities(world.territorial)
    attacker_allies = set(
        active_allies(world, order.attacker_id, doctrine.request_threshold)
    )
    defender_allies = set(
        active_allies(world, order.defender_id, doctrine.request_threshold)
    )
    attacker_allies.discard(order.defender_id)
    defender_allies.discard(order.attacker_id)

    for supporter in attacker_allies & defender_allies:
        attack_commitment = world.commitments[order.attacker_id, supporter]
        defense_commitment = world.commitments[order.defender_id, supporter]
        if attack_commitment > defense_commitment:
            defender_allies.remove(supporter)
        else:
            attacker_allies.remove(supporter)

    events = [
        _support_event(
            world,
            doctrine,
            supporter_id=supporter,
            principal_id=order.attacker_id,
            opponent_id=order.defender_id,
            side="attacker",
            capabilities=capabilities,
        )
        for supporter in sorted(attacker_allies)
    ]
    events.extend(
        _support_event(
            world,
            doctrine,
            supporter_id=supporter,
            principal_id=order.defender_id,
            opponent_id=order.attacker_id,
            side="defender",
            capabilities=capabilities,
        )
        for supporter in sorted(defender_allies)
    )
    return tuple(events)
