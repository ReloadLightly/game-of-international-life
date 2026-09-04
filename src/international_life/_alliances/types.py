"""State, doctrine, and event types for M4 alliance politics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from international_life._territorial.types import TerritorialWorld
from international_life.hexgrid import HexCoordinate

CommitmentRegime = Literal["binding", "flexible"]
PolarityRegime = Literal["bipolar", "multipolar"]
ThreatRegime = Literal["concentrated", "diffuse"]
SupportAction = Literal["full", "partial", "withhold"]
SupportSide = Literal["attacker", "defender"]
AllianceChange = Literal["formed", "dissolved"]
FloatMatrix = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class AllianceDoctrine:
    """A commitment doctrine governing requests, support, and relation learning."""

    name: CommitmentRegime
    defensive_scope: float
    offensive_scope: float
    full_support_threshold: float
    partial_support_threshold: float
    entrapment_aversion: float
    relation_learning_rate: float
    support_fraction: float = 0.18
    partial_support_fraction: float = 0.09
    support_cost_rate: float = 0.20
    request_threshold: float = 0.35
    alliance_threshold: float = 0.50
    formation_threshold: float = 0.72
    formation_commitment: float = 0.66
    successor_retention: float = 0.65
    max_new_alliances: int = 1

    def __post_init__(self) -> None:
        unit_interval = (
            "defensive_scope",
            "offensive_scope",
            "full_support_threshold",
            "partial_support_threshold",
            "entrapment_aversion",
            "relation_learning_rate",
            "support_fraction",
            "partial_support_fraction",
            "support_cost_rate",
            "request_threshold",
            "alliance_threshold",
            "formation_threshold",
            "formation_commitment",
            "successor_retention",
        )
        for field_name in unit_interval:
            value = float(getattr(self, field_name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must lie in [0, 1]")
        if self.partial_support_threshold > self.full_support_threshold:
            raise ValueError("partial support threshold must not exceed full threshold")
        if self.partial_support_fraction > self.support_fraction:
            raise ValueError("partial support must not exceed full support")
        if self.formation_commitment < self.alliance_threshold:
            raise ValueError("new alliance commitment must reach the alliance threshold")
        if self.max_new_alliances < 0:
            raise ValueError("max_new_alliances must be non-negative")


def doctrine_for(regime: CommitmentRegime) -> AllianceDoctrine:
    """Return one endpoint of the frozen M4 commitment-bindingness treatment."""
    if regime == "binding":
        return AllianceDoctrine(
            name="binding",
            defensive_scope=1.00,
            offensive_scope=0.90,
            full_support_threshold=0.58,
            partial_support_threshold=0.48,
            entrapment_aversion=0.08,
            relation_learning_rate=0.04,
        )
    if regime == "flexible":
        return AllianceDoctrine(
            name="flexible",
            defensive_scope=0.55,
            offensive_scope=0.20,
            full_support_threshold=0.70,
            partial_support_threshold=0.56,
            entrapment_aversion=0.45,
            relation_learning_rate=0.07,
        )
    raise ValueError(f"unsupported commitment regime: {regime!r}")


@dataclass(frozen=True, slots=True)
class SupportEvent:
    """One ally's response to one offensive or defensive support request."""

    supporter_id: int
    principal_id: int
    opponent_id: int
    side: SupportSide
    action: SupportAction
    score: float
    contribution: float
    cost: float
    commitment: float
    reliability: float
    dependence: float
    direct_threat: float
    own_security_ratio: float
    abandonment: bool = False
    entrapment: bool = False
    buck_passing: bool = False


@dataclass(frozen=True, slots=True)
class AllianceChangeEvent:
    """Formation or dissolution of one undirected alliance edge."""

    first_id: int
    second_id: int
    action: AllianceChange
    old_strength: float
    new_strength: float
    reason: str


@dataclass(frozen=True, slots=True)
class AllianceCrisisEvent:
    """A primary attack plus any third-party alliance participation."""

    attacker_id: int
    defender_id: int
    target: HexCoordinate
    attacker_supporters: tuple[int, ...]
    defender_supporters: tuple[int, ...]
    participant_count: int
    chain_ganging: bool
    success: bool
    conquered: bool


@dataclass(frozen=True, slots=True)
class AllianceWorld:
    """Territorial state plus commitments, reliability beliefs, and threats."""

    territorial: TerritorialWorld
    commitments: FloatMatrix
    reliability: FloatMatrix
    threats: FloatMatrix
    polarity: PolarityRegime
    threat_regime: ThreatRegime
    focal_threat_id: int
    doctrine_name: str = "unassigned"
    support_events: tuple[SupportEvent, ...] = ()
    crises: tuple[AllianceCrisisEvent, ...] = ()
    alliance_changes: tuple[AllianceChangeEvent, ...] = ()

    def __post_init__(self) -> None:
        matrices = (self.commitments, self.reliability, self.threats)
        size = self.commitments.shape[0]
        for matrix in matrices:
            if matrix.ndim != 2 or matrix.shape != (size, size):
                raise ValueError("all alliance matrices must be square and share one shape")
            if np.any(~np.isfinite(matrix)) or np.any((matrix < 0.0) | (matrix > 1.0)):
                raise ValueError("alliance matrices must contain finite values in [0, 1]")
            if np.any(np.diag(matrix) != 0.0):
                raise ValueError("alliance matrices must have zero diagonals")
        if size < len(self.territorial.treasury):
            raise ValueError("alliance matrices must cover every historical polity ID")
        if self.polarity not in {"bipolar", "multipolar"}:
            raise ValueError("unsupported polarity")
        if self.threat_regime not in {"concentrated", "diffuse"}:
            raise ValueError("unsupported threat regime")
        if not 0 < self.focal_threat_id < size:
            raise ValueError("focal_threat_id must identify a matrix row")
        if not self.doctrine_name:
            raise ValueError("doctrine_name must not be empty")

    @property
    def generation(self) -> int:
        return self.territorial.generation

    def copy(self) -> AllianceWorld:
        """Return an independent history snapshot."""
        return replace(
            self,
            territorial=self.territorial.copy(),
            commitments=self.commitments.copy(),
            reliability=self.reliability.copy(),
            threats=self.threats.copy(),
        )
