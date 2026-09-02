# M1 model specification: Jervisian security-dilemma CA

## Status

M1 is a transparent mechanism model intended to establish the repository's experimental grammar. It does not yet represent territorial states, diplomacy, bargaining, or a historically calibrated international system.

## Lattice and update timing

- two-dimensional square lattice;
- Moore neighborhood of eight adjacent cells;
- toroidal boundary by default;
- discrete generations;
- synchronous update from generation `t` to `t + 1`.

## Cell state

For polity `i` at generation `t`:

- `a_i(t) ∈ {0, …, A_max}`: arms level;
- `o_i ∈ {0, 1}`: fixed defensive (`0`) or offensive (`1`) posture;
- `c_i(t) ∈ {0, 1}`: conflict initiation in the current generation.

## Strategic-environment parameters

- `β ∈ [-1, 1]`: offense advantage;
- `d ∈ [0, 1]`: distinguishability;
- response, preemption, alarm, and exhaustion coefficients documented in `JervisParameters`.

## Threat perception

Neighboring offensive arms are fully treated as threatening. Neighboring defensive arms are treated as threatening in proportion to ambiguity:

```text
signal_j = normalized_arms_j × [offensive_j + (1 - offensive_j)(1 - d)]
```

Recent neighboring conflict adds a temporary alarm term. Perceived threat is the mean signal across the eight neighbors, clipped to `[0, 1]`.

This operationalization deliberately treats posture as observable with error. It does not yet separate intent, weapon technology, doctrine, and signaling behavior.

## Arms update

Each cell computes a target arms level from:

- a common baseline;
- perceived local threat;
- a stronger fear response when offense is advantaged;
- an additional drive for offensive-posture cells.

Arms move by at most one discrete level per generation toward the target. This preserves local, finite-state, temporally bounded adaptation rather than allowing instantaneous jumps.

## Conflict initiation

Attack capacity increases with:

- own arms;
- offensive posture;
- preemptive pressure from perceived threat;
- offense advantage.

Local deterrence increases with neighboring arms and defense advantage. A conflict event occurs when attack capacity minus local deterrence crosses a fixed threshold. Conflict produces one-step arms exhaustion by default.

## Observables

- initial and final mean normalized arms;
- spiral delta: final minus initial mean arms;
- mean, final, and peak conflict-initiation rates.

Future additions should include spatial autocorrelation, cascade size, persistence, hysteresis, and separate false-positive versus true-positive threat responses.

## Directional checks

The test suite currently verifies:

- fully distinguishable defensive arming produces zero perceived threat in the simplified M1 signal model;
- ambiguous defensive arming produces greater perceived threat;
- fixed seeds replay exactly;
- the offense-dominant/indistinguishable corner produces more final arming than the defense-dominant/distinguishable corner.

These checks establish that the theoretical controls are causally live. They do not establish external validity.
