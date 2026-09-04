"""Territorial competition on a hexagonal lattice."""

from international_life._territorial.dynamics import (
    fragment_disconnected_polities,
    run_territorial,
    territorial_step,
    territorial_step_from_orders,
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
    "run_territorial",
    "territorial_metrics",
    "territorial_step",
    "territorial_step_from_orders",
]
