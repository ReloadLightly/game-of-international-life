# Project state — v0.4 checkpoint

**Checkpoint date:** 2026-09-04  
**Repository:** `ReloadLightly/game-of-international-life`  
**Status:** M0–M4 executable computational IR laboratory

## Stable identity

Game of International Life turns international-relations mechanisms into explicit artificial worlds. Canonical cellular automata provide the formal baseline; later milestones add territorial states, rival strategic rules, and alliance networks while preserving matched-world comparison as the core experimental discipline.

## Implemented

- **M0 — Conway:** faithful B3/S23, canonical patterns, synchronous updates.
- **M1 — Jervis:** offense–defense advantage × distinguishability security-dilemma CA.
- **M2 — Territorial states:** hex geography, resources, capability, conquest, extinction, fragmentation.
- **M3 — Structural strategies:** security-seeking sufficiency versus continued relative-power maximization in matched worlds.
- **M4 — Alliance politics:** binding versus flexible commitment doctrines on a weighted alliance graph above the territorial world.

## M4 invariants

1. Alliances are a graph layer, not geographic adjacency.
2. Binding and flexible pairs share the same initial territory, capabilities, relations, threats, and battle physics.
3. Initial alliance worlds are fingerprinted.
4. M2/M3 retain ownership of battle resolution, conquest, extinction, and fragmentation.
5. Alliance support has explicit costs.
6. The doctrine treatment is bundled and must not be described as a one-parameter causal estimate.
7. Abandonment and entrapment are process traces, not post-hoc labels inferred from final outcomes.
8. Successor polity IDs are not recycled; inherited alliance relations are attenuated but traceable.
9. Attractive single histories never substitute for matched ensembles.

## Frozen M4 experiment

```text
commitment doctrine ∈ {binding, flexible}
polarity            ∈ {bipolar, multipolar}
threat distribution ∈ {concentrated, diffuse}

12 × 16 hex cells
8 initial states
24 generations
6 seeds per structural condition
48 histories / 24 matched pairs
```

## Reference mechanism check

The rebuilt v0.4 implementation produces the intended alliance-security-dilemma contrast in the frozen reference ensemble:

```text
                                      binding    flexible
abandonment                              0.00       15.25
entrapment                              54.29        0.00
chain-ganging crises                    24.00        0.00
third-party participations             135.62       52.25
support cost                            951.89      464.27
total conflict cost                   1440.97      751.13
final alliance edges                    17.38       13.71
original-state survival                  0.964       1.000
```

Interpretation: the mechanism is behaviorally live in this artificial world. This is not historical validation of Snyder and not evidence that either doctrine is normatively preferable.

## Verification before publication

- focused alliance mechanism tests pass locally;
- frozen M4 reference command runs end to end locally;
- 48 histories and 24 matched doctrine pairs are produced;
- Python source compiles;
- full repository CI must pass on Python 3.11 and 3.12 before merge to `main`.

## Exact next milestone

**M5 — Perception and signaling on the territorial-alliance world.**

Add actual versus perceived posture, noisy capability estimates, offense–defense advantage, distinguishability, reassurance/deterrence signals, and mobilization visibility. Preserve M2–M4 mechanics and make perception—not a rewritten world—the treatment.

## Deferred

- independent sweeps of the components bundled inside M4 doctrines;
- richer bargaining and endogenous threat learning;
- heterogeneous doctrines within one system;
- simultaneous crises;
- broader M3/M4 sensitivity surfaces;
- evolutionary discovery of compact strategic and alliance rules;
- fossil-record replications of Bremer–Mihalka and Cederman;
- empirical initialization and held-out historical comparison.
