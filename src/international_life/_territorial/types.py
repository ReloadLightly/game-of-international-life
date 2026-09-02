"""State and event types shared by the territorial models."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from international_life.core import Boundary, validate_2d
from international_life.hexgrid import HexCoordinate, validate_hex_shape

PolityGrid = NDArray[np.int32]
FloatGrid = NDArray[np.float64]
FloatVector = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class TerritorialParameters:
    """Shared transition parameters for M2 and M3 territorial worlds."""

    production_rate: float = 0.55
    reserve_decay: float = 0.04
    mobilization: float = 0.34
    offense_multiplier: float = 1.05
    defense_multiplier: float = 1.10
    support_bonus: float = 0.12
    garrison_strength: float = 0.35
    fortification_value: float = 0.75
    fortification_growth: float = 0.05
    fortification_cap: float = 1.50
    battle_damage: float = 0.88
    conquest_retention: float = 0.20
    attack_threshold: float = 0.98
    resource_attraction: float = 0.12
    attack_cost: float = 0.10
    defense_cost: float = 0.06
    battle_noise: float = 0.06
    battle_seed: int = 0
    boundary: Boundary = "fixed"

    def __post_init__(self) -> None:
        nonnegative = (
            "production_rate",
            "support_bonus",
            "garrison_strength",
            "fortification_value",
            "fortification_growth",
            "fortification_cap",
            "resource_attraction",
            "attack_cost",
            "defense_cost",
            "battle_noise",
        )
        for name in nonnegative:
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if not 0.0 <= self.reserve_decay <= 1.0:
            raise ValueError("reserve_decay must lie in [0, 1]")
        if not 0.0 < self.mobilization <= 1.0:
            raise ValueError("mobilization must lie in (0, 1]")
        if self.offense_multiplier <= 0.0 or self.defense_multiplier <= 0.0:
            raise ValueError("offense_multiplier and defense_multiplier must be positive")
        for name in ("battle_damage", "conquest_retention"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.attack_threshold <= 0.0:
            raise ValueError("attack_threshold must be positive")
        if self.battle_noise > 1.0:
            raise ValueError("battle_noise must not exceed 1")
        if self.battle_seed < 0:
            raise ValueError("battle_seed must be non-negative")
        if self.boundary != "fixed":
            raise ValueError("territorial transitions currently require fixed boundaries")


@dataclass(frozen=True, slots=True)
class AttackOrder:
    """One polity's chosen border-cell attack before stochastic resolution.

    The first seven fields preserve the M2 order contract. M3 appends explicit
    process metadata so rival policy rules can be distinguished even when they
    happen to produce similar final maps.
    """

    attacker_id: int
    defender_id: int
    target: HexCoordinate
    predicted_attack: float
    predicted_defense: float
    expected_ratio: float
    score: float
    policy: str = "opportunistic"
    motive: str = "opportunity"
    security_ratio: float = 0.0
    security_target: float = 1.0
    secure_at_attack: bool = False
    attacker_power_share: float = 0.0
    defender_power_share: float = 0.0
    expected_relative_gain: float = 0.0
    border_relief: int = 0
    target_resource_ratio: float = 0.0


@dataclass(frozen=True, slots=True)
class BattleEvent:
    """One resolved attack; at most one successful attacker conquers a target."""

    attacker_id: int
    defender_id: int
    target: HexCoordinate
    attack_strength: float
    defense_strength: float
    success: bool
    conquered: bool = False
    attacker_cost: float = 0.0
    defender_cost: float = 0.0


@dataclass(frozen=True, slots=True)
class FragmentationEvent:
    """A disconnected component that becomes a successor polity."""

    parent_id: int
    successor_id: int
    cells: int
    inherited_treasury: float


@dataclass(frozen=True, slots=True)
class TerritorialWorld:
    """One synchronous generation of the territorial world.

    Array coordinates are stable geographic cell identities. ``polities`` is a
    mutable control map, so a cell can change political identity without losing
    its identity as a location. ``treasury`` is indexed by polity ID; index zero
    is reserved and polity IDs are never recycled.
    """

    polities: PolityGrid
    resources: FloatGrid
    fortification: FloatGrid
    treasury: FloatVector
    orders: tuple[AttackOrder, ...] = ()
    battles: tuple[BattleEvent, ...] = ()
    fragmentations: tuple[FragmentationEvent, ...] = ()
    extinctions: tuple[int, ...] = ()
    policy_name: str = "opportunistic"
    generation: int = 0

    def __post_init__(self) -> None:
        validate_2d(self.polities, name="polities")
        validate_2d(self.resources, name="resources")
        validate_2d(self.fortification, name="fortification")
        if not (self.polities.shape == self.resources.shape == self.fortification.shape):
            raise ValueError("all territorial cell arrays must share the same shape")
        validate_hex_shape(self.polities.shape, boundary="fixed")
        if np.any(self.polities <= 0):
            raise ValueError("every territorial cell must have a positive polity ID")
        if np.any(~np.isfinite(self.resources)) or np.any(self.resources <= 0.0):
            raise ValueError("resources must be finite and strictly positive")
        if np.any(~np.isfinite(self.fortification)) or np.any(self.fortification < 0.0):
            raise ValueError("fortification must be finite and non-negative")
        if self.treasury.ndim != 1:
            raise ValueError("treasury must be one-dimensional")
        if np.any(~np.isfinite(self.treasury)) or np.any(self.treasury < 0.0):
            raise ValueError("treasury must be finite and non-negative")
        if int(self.polities.max()) >= len(self.treasury):
            raise ValueError("treasury must contain an entry for every polity ID")
        if not self.policy_name:
            raise ValueError("policy_name must not be empty")
        if self.generation < 0:
            raise ValueError("generation must be non-negative")

    @property
    def shape(self) -> tuple[int, int]:
        return self.polities.shape

    @property
    def cell_ids(self) -> NDArray[np.int64]:
        """Return stable row-major geographic cell identifiers."""
        return np.arange(self.polities.size, dtype=np.int64).reshape(self.polities.shape)

    def copy(self) -> TerritorialWorld:
        """Return an independent snapshot suitable for a simulation history."""
        return replace(
            self,
            polities=self.polities.copy(),
            resources=self.resources.copy(),
            fortification=self.fortification.copy(),
            treasury=self.treasury.copy(),
        )
