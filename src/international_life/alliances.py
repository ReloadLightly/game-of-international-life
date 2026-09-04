"""M4: Snyderian alliance-security-dilemma experiments.

The public API keeps the alliance graph separate from the territorial lattice.
Commitment doctrines determine third-party support and relation learning while
M2/M3 continue to own battle resolution, conquest, extinction, and succession.
"""

from international_life._alliances.dynamics import alliance_step, run_alliance
from international_life._alliances.initialization import (
    alliance_world_fingerprint,
    initialize_alliance_world,
    set_initial_polarity,
)
from international_life._alliances.measures import alliance_edges, alliance_metrics
from international_life._alliances.types import (
    AllianceChangeEvent,
    AllianceCrisisEvent,
    AllianceDoctrine,
    AllianceWorld,
    CommitmentRegime,
    PolarityRegime,
    SupportEvent,
    ThreatRegime,
    doctrine_for,
)

__all__ = [
    "AllianceChangeEvent",
    "AllianceCrisisEvent",
    "AllianceDoctrine",
    "AllianceWorld",
    "CommitmentRegime",
    "PolarityRegime",
    "SupportEvent",
    "ThreatRegime",
    "alliance_edges",
    "alliance_metrics",
    "alliance_step",
    "alliance_world_fingerprint",
    "doctrine_for",
    "initialize_alliance_world",
    "run_alliance",
    "set_initial_polarity",
]
