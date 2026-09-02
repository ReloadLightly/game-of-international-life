"""Territorial competition on a hexagonal lattice.

The public facade keeps the theory-facing API compact while world state,
initialization, policy, transition, and measurement layers remain separately
inspectable. M2 supplies the generic opportunistic baseline; M3 adds matched
security-seeking and power-maximizing policies without changing the world.
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
    resource_coefficient_of_variation,
    territorial_metrics,
)
from international_life._territorial.policy import (
    OpportunisticPolicy,
    PowerMaximizingPolicy,
    SecuritySeekingPolicy,
    TerritorialPolicy,
    attack_candidates,
    propose_attacks,
)
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
    "OpportunisticPolicy",
    "PowerMaximizingPolicy",
    "SecuritySeekingPolicy",
    "TerritorialParameters",
    "TerritorialPolicy",
    "TerritorialWorld",
    "alive_polities",
    "attack_candidates",
    "border_edge_count",
    "fragment_disconnected_polities",
    "initialize_territorial_world",
    "polity_capabilities",
    "polity_cell_counts",
    "polity_production",
    "propose_attacks",
    "resource_coefficient_of_variation",
    "run_territorial",
    "territorial_metrics",
    "territorial_step",
]
