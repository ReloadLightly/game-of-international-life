# Project state — v0.3 checkpoint

**Checkpoint date:** 2026-09-02  
**Repository:** `ReloadLightly/game-of-international-life`  
**Status:** public, executable M0–M3 computational IR laboratory

## Stable identity

Game of International Life studies how explicit local rules generate system-level patterns in international politics under anarchy. It combines:

1. faithful cellular-automata baselines;
2. theory-bearing artificial worlds;
3. matched comparisons of rival IR mechanisms;
4. later evolutionary discovery of interpretable strategic rules.

The central standard is not a visually interesting map. It is a transparent chain from assumptions to information, decisions, interactions, process traces, outcomes, and failure conditions.

## Implemented

### M0 — Conway laboratory

- generic two-dimensional Moore-neighborhood utilities;
- synchronous fixed and toroidal updates;
- faithful Conway B3/S23;
- block, blinker, glider, and R-pentomino seeds;
- canonical still-life, oscillator, and glider tests.

### M1 — Jervisian security dilemma

- discrete arms and posture cellular automaton;
- offense–defense advantage;
- distinguishability of offensive and defensive postures;
- reciprocal local threat response;
- matched four-world experiment;
- continuous parameter sweep and phase diagrams;
- explicit model specification and directional tests.

### M2 — Hexagonal territorial states

- six-neighbor odd-row hex geometry;
- stable geographic identity distinct from political control;
- reproducible connected-state maps;
- spatial resource fields;
- polity production, treasury, and capability aggregation;
- frontier dispersion and local concentration;
- fortification, battle costs, conquest, and turnover;
- state extinction;
- connected-component fragmentation and non-recycled successor IDs;
- state-size, polarity, border, conflict, extinction, and fragmentation metrics;
- single-history and ensemble CLI workflows.

### M3 — Structural-policy comparison

- replaceable `TerritorialPolicy` interface;
- one shared candidate generator for all rival policies;
- M2 opportunistic policy preserved as backward-compatible default;
- security-seeking rule with a declared `1.10` sufficiency threshold;
- power-maximizing rule that continues exploiting relative gains after sufficiency;
- exact balanced and dominant-power initial capability regimes;
- diffuse and clustered resource geographies;
- SHA-256 fingerprints over all policy-visible initial arrays;
- encounter-keyed common random numbers;
- attack-order motive and security metadata;
- realized attacker and defender cost traces;
- full trajectory, run, ensemble, and paired-difference tables;
- machine-readable experiment manifest;
- matched-world and mechanism plots;
- rigorous M3 specification and a substantially rebuilt README.

## Frozen M3 design

Default run:

```text
12 × 16 hex cells
8 initial polities
40 generations
6 seeds per structural condition
2 capability regimes
2 resource regimes
2 policy rules
48 histories / 24 matched pairs
```

Matched pair contract:

- same initial territory;
- same resource field;
- same exact capability distribution;
- same fortification and treasury state;
- same world dynamics and feasibility threshold;
- same stochastic shock for every shared encounter;
- only the policy objective and stopping rule differ.

## Reference-run mechanism check

The committed v0.3 reference run produced these mean paired differences, defined as `power-maximizing minus security-seeking`:

```text
attack orders                         +21.54
attacks after security sufficiency    +31.63
cumulative war cost                  +135.73
territorial conquests                 +20.83
final capability HHI                  +0.041
original-state survival rate          -0.115
final state count                     -0.96
```

Interpretation boundary:

- this verifies that the implemented stopping-rule contrast is behaviorally live;
- it is a small artificial-world ensemble, not evidence that offensive realism is historically true;
- aggregate directions are tendencies and individual paired seeds can reverse;
- systematic parameter sensitivity has not yet been completed.

## Verification

At this checkpoint:

- 38 tests pass locally;
- local statement coverage is 94%;
- Python source and tests compile cleanly;
- M0–M3 CLI commands run end to end;
- M2 and M3 deterministic replay are covered;
- the M3 experiment writes auditable manifests and paired outputs;
- CI is configured for Python 3.11 and 3.12.

Remote CI must be checked after the v0.3 commit reaches `main`.

## Decisions that should not be silently reversed

1. Conway's Life remains a faithful baseline rather than an IR metaphor with renamed cells.
2. Theory names require explicit theory-to-mechanism chains.
3. Geographic identity and political identity remain separate.
4. Rival policy rules share one world, one feasibility model, and one battle resolver.
5. The treatment difference belongs in the policy—not in hidden environmental advantages.
6. Matched fingerprints and common random numbers remain part of comparative experiments.
7. Process observables remain first-class outputs alongside final outcomes.
8. Hand-coded theory baselines precede GA/GP rule evolution.
9. Alliance ties will use a graph layer rather than being forced into geographic adjacency.
10. Polity IDs are not recycled; extinction, fragmentation, and succession remain traceable.
11. Single attractive maps do not substitute for paired ensembles.
12. Complexity is added only when a concrete substantive question requires it.

## Exact next milestone

**M4 — Snyderian alliance politics on a territorial world.**

The smallest meaningful M4 should add a dynamic alliance graph without rewriting M2/M3 territory or battle mechanics.

Minimum state:

- alliance partner set;
- bilateral commitment strength;
- dependence;
- perceived reliability;
- adversary relation;
- abandonment exposure;
- entrapment exposure.

Minimum crisis actions:

- support;
- partial support;
- withhold support;
- tighten or loosen commitment;
- seek or leave an alliance.

First matched experiment:

```text
commitment flexibility × polarity × threat concentration
```

Primary process measurements:

- abandonment;
- entrapment;
- chain-ganging;
- buck-passing;
- alliance turnover;
- conflict diffusion.

M4 is successful only if stronger commitments reduce some abandonment risk while increasing entrapment exposure or cost. A costless “strong alliance” variable would erase Snyder's central dilemma.

## Deferred—not forgotten

- full M3 sensitivity surfaces;
- system-wide balancing rather than strongest-neighbor sufficiency;
- internal balancing as a peaceful allocation choice;
- incomplete information and signaling;
- heterogeneous policy populations;
- fossil-record replication of Bremer–Mihalka and Cederman;
- GA/GP evolution of interpretable local rules;
- empirical initialization and held-out historical comparison.
