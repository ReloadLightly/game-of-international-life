"""M3: matched structural-realist policy experiments.

The module exposes two deliberately minimal rule families:

``SecuritySeekingPolicy``
    Expansion stops once capability is sufficient relative to the strongest
    adjacent rival.

``PowerMaximizingPolicy``
    Favorable relative-power gains remain valuable even after immediate
    security sufficiency has been reached.

They are computational probes inspired by defensive and offensive structural
realism—not executable summaries of Waltz or Mearsheimer in their entirety.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Literal

import numpy as np

from international_life._territorial.initialization import initialize_territorial_world
from international_life._territorial.measures import (
    alive_polities,
    polity_capabilities,
    polity_production,
)
from international_life._territorial.policy import (
    PowerMaximizingPolicy,
    SecuritySeekingPolicy,
    TerritorialPolicy,
    attack_candidates,
)
from international_life._territorial.types import TerritorialWorld

CapabilityRegime = Literal["balanced", "dominant-power"]
ResourceRegime = Literal["diffuse", "clustered"]

_RESOURCE_PARAMETERS: dict[ResourceRegime, tuple[float, float]] = {
    "diffuse": (0.12, 0.55),
    "clustered": (0.95, 0.78),
}


def set_initial_capability_regime(
    world: TerritorialWorld,
    regime: CapabilityRegime,
    *,
    dominant_share: float = 0.35,
    dominant_id: int | None = None,
) -> TerritorialWorld:
    """Set exact initial capability shares while preserving total capability.

    Production is fixed by the territorial resource map. M3 initializes enough
    reserves to make both requested distributions feasible, then reallocates
    only treasury. Geography, resources, fortification, and total capability do
    not change.
    """
    ids = alive_polities(world)
    count = len(ids)
    if count == 0:
        raise ValueError("world must contain at least one polity")
    if regime not in {"balanced", "dominant-power"}:
        raise ValueError(f"unsupported capability regime: {regime!r}")

    selected_dominant = int(ids[0]) if dominant_id is None else int(dominant_id)
    if selected_dominant not in {int(value) for value in ids}:
        raise ValueError("dominant_id must identify a currently represented polity")

    minimum_share = 1.0 / count
    if regime == "dominant-power" and not minimum_share <= dominant_share < 1.0:
        raise ValueError(
            "dominant_share must be at least the equal share and smaller than 1"
        )

    shares = np.zeros(len(world.treasury), dtype=np.float64)
    if regime == "balanced" or count == 1:
        shares[ids] = 1.0 / count
    else:
        remainder = (1.0 - dominant_share) / (count - 1)
        shares[ids] = remainder
        shares[selected_dominant] = dominant_share

    production = polity_production(world)
    total_capability = float(polity_capabilities(world)[ids].sum())
    desired_capability = shares * total_capability
    treasury = world.treasury.copy()
    treasury[ids] = desired_capability[ids] - production[ids]
    if np.any(treasury[ids] < -1e-9):
        raise ValueError(
            "requested capability shares are infeasible with the fixed production map; "
            "increase initial reserves"
        )
    treasury[ids] = np.clip(treasury[ids], 0.0, None)
    treasury[0] = 0.0

    result = replace(world, treasury=treasury)
    result_capabilities = polity_capabilities(result)[ids]
    result_shares = result_capabilities / result_capabilities.sum()
    if not np.allclose(result_shares, shares[ids], atol=1e-10):
        raise AssertionError("capability-regime construction failed")
    return result


def initialize_structural_world(
    shape: tuple[int, int] = (12, 16),
    *,
    num_polities: int = 8,
    seed: int = 0,
    resource_regime: ResourceRegime = "diffuse",
    capability_regime: CapabilityRegime = "balanced",
    dominant_share: float = 0.35,
) -> TerritorialWorld:
    """Create one matched M3 world under an explicit structural condition."""
    if resource_regime not in _RESOURCE_PARAMETERS:
        raise ValueError(f"unsupported resource regime: {resource_regime!r}")
    dispersion, smoothing = _RESOURCE_PARAMETERS[resource_regime]
    base = initialize_territorial_world(
        shape,
        num_polities=num_polities,
        seed=seed,
        resource_dispersion=dispersion,
        resource_smoothing=smoothing,
        initial_reserve_turns=4.0,
    )
    return set_initial_capability_regime(
        base,
        capability_regime,
        dominant_share=dominant_share,
    )


def world_fingerprint(world: TerritorialWorld) -> str:
    """Hash all policy-visible initial arrays for matched-run auditing."""
    digest = hashlib.sha256()
    for array in (world.polities, world.resources, world.fortification, world.treasury):
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(str(contiguous.shape).encode("ascii"))
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


__all__ = [
    "CapabilityRegime",
    "PowerMaximizingPolicy",
    "ResourceRegime",
    "SecuritySeekingPolicy",
    "TerritorialPolicy",
    "attack_candidates",
    "initialize_structural_world",
    "set_initial_capability_regime",
    "world_fingerprint",
]
