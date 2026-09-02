"""M2: territorial competition on a hexagonal lattice.

This public facade keeps the theory-facing API compact while the world state,
initialization, policy, transition, and measurement layers remain separately
inspectable. The supplied attack policy is a generic opportunistic baseline,
not a Waltzian or Mearsheimerian rule.
"""

from international_life._territorial.dynamics import (
    fragment_disconnected_polities,
    run_territorial,
    territorial_step,
)
from international_life._territorial.initialization import initialize_territorial_world
from international_life._territorial.measures import (
    alive_polities,
    border_edge_count,
    polity_capabilities,
    polity_cell_counts,
    polity_production,
    territorial_metrics,
)
from international_life._territorial.policy import propose_attacks
from international_life._territorial.types import (
    AttackOrder,
    BattleEvent,
    FragmentationEvent,
    TerritorialParameters,
    TerritorialWorld,
)

__all__ = [
    "AttackOrder",
    "BattleEvent",
    "FragmentationEvent",
    "TerritorialParameters",
    "TerritorialWorld",
    "alive_polities",
    "border_edge_count",
    "fragment_disconnected_polities",
    "initialize_territorial_world",
    "polity_capabilities",
    "polity_cell_counts",
    "polity_production",
    "propose_attacks",
    "run_territorial",
    "territorial_metrics",
    "territorial_step",
]
