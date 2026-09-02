"""A minimal Jervisian security-dilemma cellular automaton.

This is a *mechanism model*, not an empirical model of any particular region.
Each cell is a polity in a local strategic neighborhood. Arms are discrete,
updates are synchronous, and every transition depends only on the cell and its
Moore neighbors.

The first model isolates two variables from Robert Jervis's four-worlds
framework:

* offense advantage: -1 (strong defense advantage) to +1 (strong offense advantage)
* distinguishability: 0 (defensive and offensive postures look alike) to 1
  (perfectly distinguishable)

A small exogenous share of cells uses an offensive posture. Defensive arming by
other cells is misread as threatening in proportion to ``1 - distinguishability``.
This simplification is intentionally visible so it can later be challenged.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from international_life.core import Boundary, moore_neighbors, validate_2d

ArmsGrid = NDArray[np.uint8]
BoolGrid = NDArray[np.bool_]
FloatGrid = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class JervisParameters:
    """Parameters defining one strategic environment."""

    offense_advantage: float = 0.75
    distinguishability: float = 0.25
    max_arms: int = 6
    base_arms: int = 1
    threat_response: float = 0.80
    offensive_drive: float = 0.45
    preemption: float = 0.55
    attack_threshold: float = 0.36
    conflict_alarm: float = 0.25
    war_exhaustion: int = 1
    boundary: Boundary = "wrap"

    def __post_init__(self) -> None:
        if not -1.0 <= self.offense_advantage <= 1.0:
            raise ValueError("offense_advantage must lie in [-1, 1]")
        if not 0.0 <= self.distinguishability <= 1.0:
            raise ValueError("distinguishability must lie in [0, 1]")
        if self.max_arms < 1:
            raise ValueError("max_arms must be at least 1")
        if not 0 <= self.base_arms <= self.max_arms:
            raise ValueError("base_arms must lie in [0, max_arms]")
        for name in ("threat_response", "offensive_drive", "preemption", "conflict_alarm"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.war_exhaustion < 0:
            raise ValueError("war_exhaustion must be non-negative")
        if self.boundary not in {"wrap", "fixed"}:
            raise ValueError("boundary must be 'wrap' or 'fixed'")


@dataclass(frozen=True, slots=True)
class JervisWorld:
    """One generation of the model.

    ``offensive_posture`` is fixed in M1 so the experiment cleanly isolates the
    strategic environment. Later milestones may allow doctrine and intentions
    to evolve separately.
    """

    arms: ArmsGrid
    offensive_posture: BoolGrid
    conflict: BoolGrid
    generation: int = 0

    def __post_init__(self) -> None:
        validate_2d(self.arms, name="arms")
        validate_2d(self.offensive_posture, name="offensive_posture")
        validate_2d(self.conflict, name="conflict")
        shapes_match = (
            self.arms.shape == self.offensive_posture.shape == self.conflict.shape
        )
        if not shapes_match:
            raise ValueError("all JervisWorld arrays must share the same shape")
        if np.any(self.arms < 0):
            raise ValueError("arms levels must be non-negative")

    def copy(self) -> JervisWorld:
        """Return a deep-enough snapshot for simulation histories."""
        return replace(
            self,
            arms=self.arms.copy(),
            offensive_posture=self.offensive_posture.copy(),
            conflict=self.conflict.copy(),
        )


def initialize_jervis_world(
    shape: tuple[int, int] = (40, 40),
    *,
    seed: int = 0,
    max_arms: int = 6,
    offensive_share: float = 0.08,
    initial_arms_high: int = 2,
) -> JervisWorld:
    """Create a reproducible heterogeneous initial strategic environment."""
    height, width = shape
    if height <= 0 or width <= 0:
        raise ValueError("shape dimensions must be positive")
    if max_arms < 1:
        raise ValueError("max_arms must be at least 1")
    if not 0.0 <= offensive_share <= 1.0:
        raise ValueError("offensive_share must lie in [0, 1]")
    if not 0 <= initial_arms_high <= max_arms:
        raise ValueError("initial_arms_high must lie in [0, max_arms]")

    rng = np.random.default_rng(seed)
    arms = rng.integers(0, initial_arms_high + 1, size=shape, dtype=np.uint8)
    offensive = (rng.random(shape) < offensive_share).astype(np.bool_)
    conflict = np.zeros(shape, dtype=np.bool_)
    return JervisWorld(arms=arms, offensive_posture=offensive, conflict=conflict)


def perceived_threat(world: JervisWorld, params: JervisParameters) -> FloatGrid:
    """Compute locally perceived threat on a normalized 0..1 scale.

    Offensive postures are fully threatening. Defensive postures contribute in
    proportion to their ambiguity. Recent conflict adds a temporary alarm
    signal. The neighborhood contribution is averaged across eight neighbors.
    """
    arms = world.arms.astype(np.float64) / params.max_arms
    neighbor_arms = moore_neighbors(arms, boundary=params.boundary, fill_value=0.0)
    neighbor_offense = moore_neighbors(
        world.offensive_posture, boundary=params.boundary, fill_value=False
    ).astype(np.float64)
    neighbor_conflict = moore_neighbors(
        world.conflict, boundary=params.boundary, fill_value=False
    ).astype(np.float64)

    ambiguous_defense = (1.0 - neighbor_offense) * (1.0 - params.distinguishability)
    strategic_signal = neighbor_arms * (neighbor_offense + ambiguous_defense)
    alarm_signal = params.conflict_alarm * neighbor_conflict
    return np.clip((strategic_signal + alarm_signal).mean(axis=0), 0.0, 1.0)


def _target_arms(
    world: JervisWorld,
    threat: FloatGrid,
    params: JervisParameters,
) -> NDArray[np.int16]:
    offense_scale = (params.offense_advantage + 1.0) / 2.0
    baseline = params.base_arms / params.max_arms
    offensive_motive = (
        params.offensive_drive
        * world.offensive_posture.astype(np.float64)
        * (0.35 + 0.65 * offense_scale)
    )
    structural_fear_multiplier = 0.75 + 0.50 * offense_scale
    target_fraction = (
        baseline
        + params.threat_response * structural_fear_multiplier * threat
        + offensive_motive
    )
    target_fraction = np.clip(target_fraction, 0.0, 1.0)
    return np.rint(target_fraction * params.max_arms).astype(np.int16)


def _conflict_initiation(
    world: JervisWorld,
    threat: FloatGrid,
    params: JervisParameters,
) -> BoolGrid:
    arms_fraction = world.arms.astype(np.float64) / params.max_arms
    neighbor_arms = moore_neighbors(
        arms_fraction, boundary=params.boundary, fill_value=0.0
    ).mean(axis=0)

    offense_multiplier = 1.0 + 0.70 * params.offense_advantage
    defense_multiplier = 1.0 - 0.70 * params.offense_advantage
    explicit_aggression = world.offensive_posture.astype(np.float64)
    preemptive_motive = params.preemption * threat
    motive = explicit_aggression + preemptive_motive

    structural_preemption = (
        max(0.0, params.offense_advantage) * params.preemption * threat * 0.80
    )
    attack_capacity = offense_multiplier * arms_fraction * motive + structural_preemption
    local_deterrence = defense_multiplier * neighbor_arms
    return (attack_capacity - local_deterrence) > params.attack_threshold


def jervis_step(world: JervisWorld, params: JervisParameters) -> JervisWorld:
    """Advance the Jervisian world by one synchronous local update."""
    if int(world.arms.max(initial=0)) > params.max_arms:
        raise ValueError("world contains an arms level above params.max_arms")

    threat = perceived_threat(world, params)
    target = _target_arms(world, threat, params)
    current = world.arms.astype(np.int16)

    direction = np.sign(target - current)
    next_arms = current + direction
    conflict = _conflict_initiation(world, threat, params)
    if params.war_exhaustion:
        next_arms = next_arms - conflict.astype(np.int16) * params.war_exhaustion
    next_arms = np.clip(next_arms, 0, params.max_arms).astype(np.uint8)

    return JervisWorld(
        arms=next_arms,
        offensive_posture=world.offensive_posture.copy(),
        conflict=conflict.astype(np.bool_),
        generation=world.generation + 1,
    )


def run_jervis(
    initial: JervisWorld,
    params: JervisParameters,
    *,
    steps: int,
    include_initial: bool = True,
) -> list[JervisWorld]:
    """Run the model and return independent generation snapshots."""
    if steps < 0:
        raise ValueError("steps must be non-negative")
    current = initial.copy()
    history = [current.copy()] if include_initial else []
    for _ in range(steps):
        current = jervis_step(current, params)
        history.append(current.copy())
    return history


def history_metrics(history: list[JervisWorld], params: JervisParameters) -> dict[str, float]:
    """Compute compact macro-level observables for one run."""
    if not history:
        raise ValueError("history must contain at least one world")
    mean_arms = np.array([state.arms.mean() / params.max_arms for state in history])
    conflict_rate = np.array([state.conflict.mean() for state in history])
    return {
        "initial_mean_arms": float(mean_arms[0]),
        "final_mean_arms": float(mean_arms[-1]),
        "spiral_delta": float(mean_arms[-1] - mean_arms[0]),
        "mean_conflict_rate": float(conflict_rate.mean()),
        "final_conflict_rate": float(conflict_rate[-1]),
        "peak_conflict_rate": float(conflict_rate.max()),
    }
