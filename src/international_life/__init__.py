"""Game of International Life.

Small, explicit cellular-automata experiments for studying how local strategic
rules can generate system-level patterns in international politics.
"""

from international_life.conway import conway_step
from international_life.jervis import JervisParameters, JervisWorld, jervis_step
from international_life.territorial import (
    TerritorialParameters,
    TerritorialWorld,
    territorial_step,
)

__all__ = [
    "JervisParameters",
    "JervisWorld",
    "TerritorialParameters",
    "TerritorialWorld",
    "conway_step",
    "jervis_step",
    "territorial_step",
]
__version__ = "0.2.0"
