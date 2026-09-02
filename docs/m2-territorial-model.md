# M2 model specification — Emergent territorial states

## Status

M2 is the common spatial substrate for later comparative theory experiments. It adds geographic identity, mutable political control, resource production, polity-level capability, borders, attack, defense, conquest, extinction, and fragmentation.

The supplied M2 decision rule is an **opportunistic baseline**, not a coded claim about Waltz or Mearsheimer. Its purpose is to make the territorial mechanisms causally active while preserving an honest architecture: later theory modules replace policy selection but share the world, initialization, battle resolution, succession, and measurement layers.

M3 now demonstrates that replacement by running security-seeking and power-maximizing rules inside the same M2 world.

## Geometry and identity

- two-dimensional NumPy arrays for storage;
- odd-row offset hexagonal geometry for interaction;
- six adjacent cells for interior sites;
- fixed boundaries in territorial transitions;
- discrete generations and synchronous territorial transfer.

A cell is a stable geographic site identified by its coordinate or row-major `cell_ids` value. `polities[row, col]` is a mutable positive integer identifying who controls the site. Conquest changes political control without changing geographic identity.

Polity ID zero is reserved. IDs are never recycled, including after extinction, so historical event traces remain unambiguous.

## Initial world

`initialize_territorial_world` creates a reproducible artificial geography in three steps:

1. choose well-spaced polity seeds through seeded farthest-point sampling on the hex lattice;
2. grow all seeds simultaneously through local breadth-first expansion until every cell is controlled;
3. generate a positive, spatially smoothed lognormal resource field and normalize its world mean to one.

Multi-source local growth guarantees that every initial polity is connected. Initial treasuries are proportional to the resource production of controlled territory.

## Cell and polity state

Each cell carries:

- a stable geographic coordinate;
- a current polity ID;
- fixed positive resource productivity;
- dynamic non-negative fortification.

Each polity has:

- a non-negative treasury indexed by polity ID;
- territory and resource production derived from the control map;
- capability equal to treasury plus one turn of gross production;
- a current set of border cells and adjacent foreign targets.

The split is deliberate. Geographic properties remain local to cells, while political agency and capability aggregate across a connected territory. A multi-cell state is not reduced to one CA cell.

## One generation

### 1. Production and reserve decay

For polity `i`, gross local production is:

```text
R_i(t) = Σ resource_x, for every cell x controlled by i
```

The treasury available before conflict is:

```text
A_i(t) = (1 − decay) T_i(t) + production_rate × R_i(t)
```

### 2. Border-adjusted field strength

Let `B_i(t)` be the number of border cells held by polity `i`. Its deployable field strength is:

```text
F_i(t) = mobilization × A_i(t) / √max(1, B_i(t))
```

The square-root frontier penalty creates a minimal concentration-versus-overextension mechanism: greater capability helps, but a long frontier dilutes immediately projectable power.

### 3. Local candidate generation

A polity may target only a foreign cell adjacent to its territory and may issue at most one attack order per generation.

Predicted attack combines:

- attacker field strength;
- an offense multiplier;
- local attacker support around the target.

Predicted defense combines:

- defender field strength;
- a defense multiplier;
- local defender support;
- target-cell resource garrison;
- accumulated target fortification.

A candidate becomes feasible when its predicted attack-to-defense ratio reaches `attack_threshold`.

The M2 opportunistic policy selects the feasible target with the best force-ratio and resource score. M3 policies receive the exact same candidate set but apply different objectives and stopping rules.

### 4. Battle resolution and costs

All orders are selected from generation `t` before any territory changes. Bounded, seeded multiplicative noise is applied to attack and defense strength. Both sides pay costs proportional to realized strength.

Several polities may attack the same cell. Every battle is recorded, but only the successful attacker with the strongest realized margin can acquire the target. Transfers are applied simultaneously.

For M3, battle noise is keyed to generation, attacker, defender, and target. This preserves common random numbers for encounters shared across divergent policy histories.

### 5. Fortification

Fortification grows gradually in ordinary generations, is damaged when a site is fought over, and retains only a fraction of its value after conquest.

### 6. Extinction and fragmentation

A polity becomes extinct when no cell carries its ID after simultaneous conquest.

Conquest may cut a polity into disconnected components. M2 enforces a contiguous-state convention:

- the largest component retains the parent ID;
- every smaller component receives a new successor ID;
- the parent's surviving treasury is divided in proportion to component resource production.

Geopolitical severance can therefore produce endogenous political fragmentation while preserving the invariant that every represented polity occupies one connected territory.

## Observables

`territorial_metrics` reports:

- surviving state count;
- mean and maximum territorial size;
- largest territorial share;
- capability HHI;
- effective number of powers (`1 / HHI`);
- largest capability share;
- interstate border edges;
- attack orders and battles;
- successful battles and territorial conquests;
- territorial turnover;
- realized war costs;
- policy motives and attacker security ratios;
- attacks launched after security sufficiency;
- state extinctions and fragmentations.

The additional policy-process fields are empty or generic under the M2 baseline but become essential in M3 comparisons.

## Verified invariants and checks

The test suite verifies that:

- an interior site has exactly six hex neighbors;
- every undirected hex edge is enumerated once;
- initial maps replay exactly for a fixed seed;
- every initial polity is contiguous;
- geographic identity remains stable when political control changes;
- local resources aggregate correctly to polity production;
- an overwhelmingly stronger polity can conquer and extinguish a one-cell rival;
- disconnected components become successor states and inherit treasury proportionally;
- fixed seeds replay identical territorial histories;
- policy runs do not mutate the shared initial world;
- long stress runs preserve contiguity and non-negative finite treasury;
- ensemble commands write trajectories, maps, and plots end to end.

## Interpretive boundary

M2 establishes a functioning artificial geopolitical world. Its opportunistic policy contains substantive assumptions—one action per state, local adjacency, aggregate treasuries, perfect knowledge, and myopic target selection—and those assumptions shape its histories.

M2 alone does not test structural realism. M3 begins comparative theory work by replacing only the policy layer. Later modules should preserve the same discipline:

- alliance rules add a graph layer rather than receiving a different territorial world;
- perception rules alter information rather than silently changing true capability;
- evolved rules compete against the same hand-coded baselines and held-out worlds.

The world substrate is useful precisely because it makes such comparisons possible without rebuilding reality for every theory.
