"""Game of International Life.

Cellular automata, emergent territorial states, alliance networks, and matched
artificial-world experiments for international-relations theory.
"""

from international_life.alliances import (
    AllianceDoctrine,
    AllianceWorld,
    alliance_metrics,
    alliance_step,
    doctrine_for,
    initialize_alliance_world,
    run_alliance,
)
from international_life.conway import conway_step
from international_life.jervis import JervisParameters, JervisWorld, jervis_step
from international_life.structural import PowerMaximizingPolicy, SecuritySeekingPolicy
from international_life.territorial import (
    TerritorialParameters,
    TerritorialWorld,
    territorial_step,
)

__all__ = [
    "AllianceDoctrine",
    "AllianceWorld",
    "alliance_metrics",
    "JervisParameters",
    "JervisWorld",
    "PowerMaximizingPolicy",
    "SecuritySeekingPolicy",
    "TerritorialParameters",
    "TerritorialWorld",
    "alliance_step",
    "conway_step",
    "doctrine_for",
    "initialize_alliance_world",
    "jervis_step",
    "run_alliance",
    "territorial_step",
]
__version__ = "0.4.0"
