# M4 model specification — alliance security dilemma

## Status

M4 is the first relational layer in Game of International Life. It adds an alliance graph above the M2/M3 territorial lattice and implements a matched comparison of two alliance-commitment doctrines inspired by Glenn Snyder's abandonment–entrapment dilemma.

M4 is a **generative computational experiment**. It is not a complete formalization of Snyder, an empirical validation of alliance theory, or a policy recommendation.

## Research question

> When alliance promises become more binding, do allies become less vulnerable to abandonment at the cost of greater entrapment, third-party participation, and conflict burden?

The model is considered mechanism-valid only if stronger commitments have a cost. A variable that simply makes alliances stronger and safer would erase the theoretical dilemma.

## Two topologies

M4 deliberately separates:

1. **territorial adjacency** — the six-neighbor hexagonal lattice inherited from M2/M3;
2. **alliance relations** — a weighted graph whose edges can connect geographically separated polities.

The alliance layer never replaces territorial state identity. It modifies crisis participation around territorial disputes.

## State

An `AllianceWorld` contains the complete `TerritorialWorld` plus three relation matrices.

### Commitment

`commitments[i, j] ∈ [0, 1]` records how strongly polity `i` expects polity `j` to support it. An active alliance edge requires reciprocal commitment above the alliance threshold.

### Reliability

`reliability[i, j] ∈ [0, 1]` is polity `i`'s current belief that `j` will honor requests. Reliability changes after observed support or withholding.

### Threat

`threats[i, j] ∈ [0, 1]` represents the threat polity `i` attributes to polity `j`. Threats are directed: `i` can fear `j` more than `j` fears `i`.

All matrices have zero diagonals. Polity IDs remain aligned with the territorial model, including non-recycled successor IDs.

## Structural treatments

### Polarity

M4 constructs exact initial capability shares while preserving the spatial world.

**Bipolar** — two leading powers begin with 30% of system capability each; the remainder is divided among the other polities.

**Multipolar** — with the default eight states, four leading powers begin with 20% each and the remaining 20% is divided among the others.

The default alliance topologies are designed to have the same initial edge count (12 with eight states) so the polarity treatment does not silently become an alliance-density treatment.

### Threat distribution

**Concentrated threat** gives most actors a common focal threat.

**Diffuse threat** gives actors heterogeneous local opponents, making partner interests less aligned and therefore making abandonment/entrapment tensions easier to express.

## Commitment doctrines

M4 compares bundled doctrinal endpoints rather than pretending commitment is one scalar.

### Binding

- broad defensive scope;
- broad offensive scope;
- lower full- and partial-support thresholds;
- low entrapment aversion;
- slower relationship revision.

### Flexible

- narrower defensive scope;
- sharply narrower offensive scope;
- higher support thresholds;
- stronger entrapment aversion;
- faster relationship revision.

Future work should vary these components independently. The v0.4 causal contrast is **binding doctrine versus flexible doctrine**, not “one unit more commitment.”

## One generation

### 1. Primary crisis selection

The shared M3 territorial candidate generator produces adjacent foreign targets. Active allies are excluded as primary targets. Candidates must meet the shared territorial feasibility threshold. Threat enters only as a transparent bonus when choosing among feasible non-allied disputes.

### 2. Alliance consultation

The attacker and defender request support from current partners. If a third party is tied to both principals, it receives one request; the stronger commitment decides the side, with defense winning exact ties.

### 3. Support choice

Each request is scored from:

- commitment;
- offensive or defensive scope;
- direct threat from the opponent;
- dependence on the principal;
- expected reliability;
- entrapment aversion.

The doctrine maps the score to `full`, `partial`, or `withhold`.

### 4. Contribution and cost

Full and partial supporters contribute fractions of their current capability to the principal's predicted battle strength. Support is not free: supporters pay an explicit treasury cost.

### 5. Territorial resolution

The alliance layer sends the adjusted primary order through `territorial_step_from_orders`. Production, encounter-keyed battle noise, attacker/defender costs, fortification, conquest, extinction, and fragmentation remain owned by the M2/M3 territorial engine.

### 6. Learning and alliance change

Observed support updates reliability and commitment. Repeated withholding can dissolve an alliance. High shared-threat scores can create new alliances. If conquest fragments a state, successor polities inherit attenuated relations rather than receiving magically blank diplomatic histories.

## Process observables

### Abandonment

A defensive ally is counted as abandoned when a reciprocal commitment exists but the requested partner does not provide full support.

### Entrapment

A supporter is counted as entrapped when it joins an ally's offensive crisis while its direct threat from the opponent is low.

### Chain-ganging

A crisis is marked chain-ganging when alliance support mobilizes third parties on **both** the attacker and defender sides.

### Buck-passing

A defensive supporter buck-passes when it withholds despite substantial direct threat from the opponent.

### Conflict diffusion

A bilateral crisis diffuses when at least one third party participates.

### Alliance turnover

Formation plus dissolution events measure how rapidly the alliance graph rewires.

## Matching contract

For every `polarity × threat × seed` world, binding and flexible runs share:

- territorial map;
- resources and fortification;
- exact capabilities;
- initial alliance graph;
- reliability matrix;
- threat matrix;
- territorial parameters;
- common crisis candidate generator;
- encounter-keyed battle shocks.

All treatment-invariant initial arrays are hashed by `alliance_world_fingerprint`. Paired analysis aborts if the fingerprints differ.

## Frozen reference design

```text
12 × 16 hex cells
8 initial states
24 generations
6 seeds
2 doctrines
2 polarity regimes
2 threat regimes
48 histories / 24 matched pairs
```

Command:

```bash
international-life m4 --output-dir artifacts/m4
```

Outputs:

- `m4_manifest.json`
- `m4_timeseries.csv`
- `m4_run_summary.csv`
- `m4_ensemble_summary.csv`
- `m4_paired_differences.csv`
- abandonment, entrapment, chain-ganging, conflict-cost, and matched-network figures

## v0.4 reference mechanism result

Means across the 24 histories per doctrine:

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

The reference ensemble satisfies the core success condition: the binding doctrine reduces abandonment and raises entrapment. It also produces greater third-party participation and higher conflict cost. These are properties of this artificial-world design, not estimates of real-world effects.

## Limits

- the doctrine treatment bundles several parameters;
- actors have highly simplified preferences and information;
- alliance bargaining is not yet strategic negotiation;
- threat perceptions are initialized exogenously and only relationships learn;
- crisis selection is endogenous to current geography and alliances;
- support contribution is a stylized capability transfer rather than force deployment;
- 24 generations and six seeds per condition are a mechanism check, not a broad sensitivity study;
- no historical data are used.

## Next step

M5 should add actual versus perceived posture, noisy capability estimates, offense–defense advantage, distinguishability, reassurance, deterrence, and mobilization signals to the territorial-alliance world. That will connect Jervisian perception to alliance commitments without rewriting the M2–M4 substrate.
