"""Reproducible capability, network, and threat initialization for M4."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import numpy as np

from international_life._alliances.types import (
    AllianceWorld,
    FloatMatrix,
    PolarityRegime,
    ThreatRegime,
)
from international_life._territorial.initialization import initialize_territorial_world
from international_life._territorial.measures import alive_polities, polity_capabilities
from international_life._territorial.types import TerritorialWorld


def _set_exact_shares(world: TerritorialWorld, shares_by_id: dict[int, float]) -> TerritorialWorld:
    ids = [int(value) for value in alive_polities(world)]
    if set(shares_by_id) != set(ids):
        raise ValueError("capability shares must cover every alive polity exactly once")
    shares = np.array([shares_by_id[polity_id] for polity_id in ids], dtype=np.float64)
    if np.any(shares <= 0.0) or not np.isclose(shares.sum(), 1.0):
        raise ValueError("capability shares must be positive and sum to one")

    production = np.bincount(
        world.polities.ravel(),
        weights=world.resources.ravel(),
        minlength=len(world.treasury),
    ).astype(np.float64)
    total = float(polity_capabilities(world)[ids].sum())
    treasury = world.treasury.copy()
    for polity_id, share in shares_by_id.items():
        treasury[polity_id] = share * total - production[polity_id]
    if np.any(treasury[ids] < -1e-9):
        raise ValueError("initial reserves are too small for the requested polarity")
    treasury[ids] = np.clip(treasury[ids], 0.0, None)
    treasury[0] = 0.0
    result = replace(world, treasury=treasury)
    realized = polity_capabilities(result)[ids]
    if not np.allclose(realized / realized.sum(), shares, atol=1e-10):
        raise AssertionError("polarity construction failed")
    return result


def set_initial_polarity(
    world: TerritorialWorld,
    regime: PolarityRegime,
    *,
    bipolar_leader_share: float = 0.30,
    multipolar_leader_share: float = 0.20,
) -> TerritorialWorld:
    """Construct exact bipolar or multipolar capability shares."""
    ids = [int(value) for value in alive_polities(world)]
    count = len(ids)
    if count < 4:
        raise ValueError("M4 polarity treatments require at least four polities")

    if regime == "bipolar":
        if not 0.0 < bipolar_leader_share < 0.5:
            raise ValueError("bipolar leader share must lie in (0, 0.5)")
        remainder = (1.0 - 2.0 * bipolar_leader_share) / (count - 2)
        shares = {polity_id: remainder for polity_id in ids}
        shares[ids[0]] = bipolar_leader_share
        shares[ids[1]] = bipolar_leader_share
    elif regime == "multipolar":
        leaders = min(4, count - 1)
        if not 0.0 < multipolar_leader_share < 1.0 / leaders:
            raise ValueError("multipolar leader share must be positive and leave a remainder")
        remainder = (1.0 - leaders * multipolar_leader_share) / (count - leaders)
        shares = {polity_id: remainder for polity_id in ids}
        for polity_id in ids[:leaders]:
            shares[polity_id] = multipolar_leader_share
    else:
        raise ValueError(f"unsupported polarity regime: {regime!r}")
    return _set_exact_shares(world, shares)


def _initial_edges(ids: list[int], regime: PolarityRegime) -> set[tuple[int, int]]:
    """Create two blocs or an overlapping multipolar alliance topology."""
    if regime == "bipolar":
        first_bloc = [ids[0], *ids[2::2]]
        second_bloc = [ids[1], *ids[3::2]]
        edges: set[tuple[int, int]] = set()
        for bloc in (first_bloc, second_bloc):
            for index, first in enumerate(bloc):
                for second in bloc[index + 1 :]:
                    edges.add(tuple(sorted((first, second))))
        return edges

    anchors = ids[: min(4, len(ids))]
    clients = ids[len(anchors) :]
    edges = set()
    for index, first in enumerate(anchors):
        second = anchors[(index + 1) % len(anchors)]
        edges.add(tuple(sorted((first, second))))
    for index, client in enumerate(clients):
        first = anchors[index % len(anchors)]
        second = anchors[(index + 1) % len(anchors)]
        edges.add(tuple(sorted((client, first))))
        edges.add(tuple(sorted((client, second))))
    return edges


def _initial_relations(
    world: TerritorialWorld,
    polarity: PolarityRegime,
    threat_regime: ThreatRegime,
) -> tuple[FloatMatrix, FloatMatrix, FloatMatrix, int]:
    size = len(world.treasury)
    ids = [int(value) for value in alive_polities(world)]
    commitments = np.zeros((size, size), dtype=np.float64)
    reliability = np.full((size, size), 0.30, dtype=np.float64)
    threats = np.zeros((size, size), dtype=np.float64)
    reliability[0, :] = 0.0
    reliability[:, 0] = 0.0
    np.fill_diagonal(reliability, 0.0)

    for first, second in _initial_edges(ids, polarity):
        commitments[first, second] = commitments[second, first] = 0.72
        reliability[first, second] = reliability[second, first] = 0.70

    focal = ids[0]
    if threat_regime == "concentrated":
        for observer in ids:
            if observer != focal:
                threats[observer, focal] = 1.0
        threats[focal, ids[1]] = 0.80
        for observer in ids:
            for target in ids:
                if observer != target and threats[observer, target] == 0.0:
                    threats[observer, target] = 0.10
    elif threat_regime == "diffuse":
        for index, observer in enumerate(ids):
            threats[observer, ids[(index + 1) % len(ids)]] = 0.75
            threats[observer, ids[(index - 1) % len(ids)]] = 0.65
            for target in ids:
                if observer != target and threats[observer, target] == 0.0:
                    threats[observer, target] = 0.12
    else:
        raise ValueError(f"unsupported threat regime: {threat_regime!r}")
    np.fill_diagonal(threats, 0.0)
    return commitments, reliability, threats, focal


def initialize_alliance_world(
    shape: tuple[int, int] = (12, 16),
    *,
    num_polities: int = 8,
    seed: int = 0,
    polarity: PolarityRegime = "bipolar",
    threat_regime: ThreatRegime = "concentrated",
) -> AllianceWorld:
    """Create the shared initial state for a matched commitment comparison."""
    base = initialize_territorial_world(
        shape,
        num_polities=num_polities,
        seed=seed,
        resource_dispersion=0.35,
        resource_smoothing=0.65,
        initial_reserve_turns=8.0,
    )
    territorial = set_initial_polarity(base, polarity)
    commitments, reliability, threats, focal = _initial_relations(
        territorial,
        polarity,
        threat_regime,
    )
    return AllianceWorld(
        territorial=replace(territorial, policy_name="alliance-crisis"),
        commitments=commitments,
        reliability=reliability,
        threats=threats,
        polarity=polarity,
        threat_regime=threat_regime,
        focal_threat_id=focal,
    )


def alliance_world_fingerprint(world: AllianceWorld) -> str:
    """Hash every treatment-invariant initial array used by M4."""
    digest = hashlib.sha256()
    arrays = (
        world.territorial.polities,
        world.territorial.resources,
        world.territorial.fortification,
        world.territorial.treasury,
        world.commitments,
        world.reliability,
        world.threats,
    )
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(str(contiguous.shape).encode("ascii"))
        digest.update(contiguous.tobytes())
    digest.update(world.polarity.encode("ascii"))
    digest.update(world.threat_regime.encode("ascii"))
    digest.update(str(world.focal_threat_id).encode("ascii"))
    return digest.hexdigest()
