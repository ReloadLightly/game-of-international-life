"""Alliance learning, formation, dissolution, and successor inheritance."""

from __future__ import annotations

import numpy as np

from international_life._alliances.types import (
    AllianceChangeEvent,
    AllianceDoctrine,
    AllianceWorld,
    FloatMatrix,
    SupportEvent,
)
from international_life._territorial.measures import alive_polities
from international_life._territorial.types import TerritorialWorld


def update_relations(
    world: AllianceWorld,
    doctrine: AllianceDoctrine,
    events: tuple[SupportEvent, ...],
) -> tuple[FloatMatrix, FloatMatrix, tuple[AllianceChangeEvent, ...]]:
    """Learn from support and update the reciprocal alliance graph."""
    commitments = world.commitments.copy()
    reliability = world.reliability.copy()
    old_commitments = world.commitments.copy()
    learning = doctrine.relation_learning_rate

    for event in events:
        principal, supporter = event.principal_id, event.supporter_id
        if event.action == "full":
            reliability[principal, supporter] += learning * (
                1.0 - reliability[principal, supporter]
            )
            commitments[principal, supporter] += 0.40 * learning
        elif event.action == "partial":
            reliability[principal, supporter] += learning * (
                0.60 - reliability[principal, supporter]
            )
            commitments[principal, supporter] -= 0.20 * learning
        else:
            reliability[principal, supporter] -= learning * reliability[principal, supporter]
            commitments[principal, supporter] -= learning

    commitments = np.clip(commitments, 0.0, 1.0)
    reliability = np.clip(reliability, 0.0, 1.0)
    np.fill_diagonal(commitments, 0.0)
    np.fill_diagonal(reliability, 0.0)

    alive = [int(value) for value in alive_polities(world.territorial)]
    changes: list[AllianceChangeEvent] = []
    for index, first in enumerate(alive):
        for second in alive[index + 1 :]:
            old_strength = float(
                min(old_commitments[first, second], old_commitments[second, first])
            )
            new_strength = float(min(commitments[first, second], commitments[second, first]))
            if (
                old_strength >= doctrine.alliance_threshold
                and new_strength < doctrine.alliance_threshold
            ):
                commitments[first, second] = commitments[second, first] = 0.0
                changes.append(
                    AllianceChangeEvent(
                        first,
                        second,
                        "dissolved",
                        old_strength,
                        0.0,
                        "withheld or insufficient support",
                    )
                )

    candidates: list[tuple[float, int, int]] = []
    if doctrine.max_new_alliances:
        focal = world.focal_threat_id
        for index, first in enumerate(alive):
            for second in alive[index + 1 :]:
                strength = min(commitments[first, second], commitments[second, first])
                if strength >= doctrine.alliance_threshold:
                    continue
                shared = min(world.threats[first, focal], world.threats[second, focal])
                mutual = min(world.threats[first, second], world.threats[second, first])
                trust = 0.5 * (reliability[first, second] + reliability[second, first])
                score = float(max(shared, mutual) + 0.15 * trust)
                if score >= doctrine.formation_threshold:
                    candidates.append((score, first, second))

    for score, first, second in sorted(candidates, reverse=True)[: doctrine.max_new_alliances]:
        old_strength = float(min(commitments[first, second], commitments[second, first]))
        commitments[first, second] = commitments[second, first] = doctrine.formation_commitment
        reliability[first, second] = max(reliability[first, second], 0.55)
        reliability[second, first] = max(reliability[second, first], 0.55)
        changes.append(
            AllianceChangeEvent(
                first,
                second,
                "formed",
                old_strength,
                doctrine.formation_commitment,
                f"shared threat score {score:.3f}",
            )
        )
    return commitments, reliability, tuple(changes)


def _expand(matrix: FloatMatrix, size: int) -> FloatMatrix:
    if size <= matrix.shape[0]:
        return matrix.copy()
    result = np.zeros((size, size), dtype=np.float64)
    result[: matrix.shape[0], : matrix.shape[1]] = matrix
    return result


def inherit_successor_relations(
    commitments: FloatMatrix,
    reliability: FloatMatrix,
    threats: FloatMatrix,
    old_size: int,
    territorial: TerritorialWorld,
    doctrine: AllianceDoctrine,
) -> tuple[FloatMatrix, FloatMatrix, FloatMatrix]:
    """Expand relation matrices after territorial fragmentation."""
    new_size = len(territorial.treasury)
    if new_size <= old_size:
        return commitments, reliability, threats.copy()

    new_commitments = _expand(commitments, new_size)
    new_reliability = _expand(reliability, new_size)
    new_threats = _expand(threats, new_size)
    for event in territorial.fragmentations:
        parent, successor = event.parent_id, event.successor_id
        retention = doctrine.successor_retention
        new_commitments[successor, :old_size] = retention * commitments[parent, :old_size]
        new_commitments[:old_size, successor] = retention * commitments[:old_size, parent]
        new_reliability[successor, :old_size] = retention * reliability[parent, :old_size]
        new_reliability[:old_size, successor] = retention * reliability[:old_size, parent]
        new_threats[successor, :old_size] = threats[parent, :old_size]
        new_threats[:old_size, successor] = threats[:old_size, parent]

    for matrix in (new_commitments, new_reliability, new_threats):
        np.fill_diagonal(matrix, 0.0)
    return (
        np.clip(new_commitments, 0.0, 1.0),
        np.clip(new_reliability, 0.0, 1.0),
        np.clip(new_threats, 0.0, 1.0),
    )
