# M2 model specification: emergent territorial states

## Status

M2 is implemented as a common spatial substrate for later comparative theory experiments. It adds geographic cell identity, mutable political control, resource production, polity-level capability, borders, attack, defense, conquest, extinction, and fragmentation.

The supplied decision rule is an **opportunistic baseline**, not a coded claim about Waltz or Mearsheimer. Its job is to make every territorial mechanism causally live while keeping the future theory comparison honest: later rule families should replace attack selection while sharing this world, initialization, event resolution, and measurement layer.

## Geometry and identity

- two-dimensional NumPy array for storage;
- odd-row offset hexagonal geometry for interaction;
- six adjacent cells for interior sites;
- fixed boundaries in the implemented M2 transition model;
- discrete generations and synchronous territorial transfer.

A cell is a stable geographic site identified by its row-major coordinate or `cell_ids` value. `polities[row, col]` is a mutable positive integer describing who controls that site. Conquest changes political control without changing geographic identity.

Polity ID zero is reserved. IDs are never recycled, including after extinction, so historical event traces remain unambiguous.

## Initial world

`initialize_territorial_world` creates a reproducible artificial geography in three steps:

1. choose well-spaced polity seeds by seeded farthest-point sampling on the hex lattice;
2. grow all seeds simultaneously through local breadth-first expansion until every cell is controlled;
3. generate a positive, spatially smoothed lognormal resource field and normalize its world mean to one.

Multi-source local growth guarantees that each initial polity is connected. Initial treasuries are proportional to the resource production of the territory they control.

## Cell and polity state

Each cell has:

- a stable coordinate;
- a current polity ID;
- fixed positive resource productivity;
- dynamic non-negative fortification.

Each polity has:

- a non-negative treasury indexed by polity ID;
- territory and resource production derived from the control map;
- derived capability equal to treasury plus one turn of gross production;
- a current set of border cells and adjacent foreign targets.

The state is deliberately split this way. Geographic properties stay local to cells, while capability can be aggregated at the polity level without pretending that a multi-cell state is a single CA cell.

## One generation

### 1. Production and reserve decay

For polity `i`, gross local production is

```text
R_i(t) = Σ resource_c(t), for all cells c controlled by i.
```

The treasury available before conflict is

```text
T_i+(t) = (1 - decay) T_i(t) + production_rate × R_i(t).
```

### 2. Border-adjusted field strength

Let `B_i(t)` be the number of cells on polity `i`'s frontier. The generic baseline's deployable field strength is

```text
F_i(t) = mobilization × T_i+(t) / sqrt(max(1, B_i(t))).
```

The square-root frontier penalty captures a minimal concentration-versus-overextension trade-off: larger capability helps, but a long frontier dilutes immediately projectable power.

### 3. Local target evaluation

Every polity may issue at most one attack order. It evaluates only foreign cells adjacent to its existing territory.

Predicted attack strength combines:

- attacker field strength;
- an offense multiplier;
- the number of attacker-controlled cells adjacent to the target.

Predicted defense combines:

- defender field strength;
- a defense multiplier;
- adjacent defender support;
- target-cell resource garrison;
- accumulated target fortification.

A candidate is admissible only when its predicted attack-to-defense ratio reaches `attack_threshold`. Among admissible cells, the polity selects the highest score, consisting of the ratio plus a small resource-attraction term.

This is a transparent opportunity rule. It is not yet a security-seeking rule, a relative-power objective, a balancing rule, or an alliance rule.

### 4. Battle resolution and costs

All orders are selected from generation `t` before any territory changes. Seeded bounded battle noise is then applied to attack and defense strength. Both attacker and defender pay explicit treasury costs.

Several polities may attack the same cell. All such battles are recorded, but only the successful attacker with the strongest realized margin can acquire the site. Territorial transfers are applied simultaneously.

### 5. Fortification

Fortifications grow slowly in ordinary generations, are damaged when a cell is fought over, and retain only a fraction of their value following conquest.

### 6. Extinction and fragmentation

A polity becomes extinct when no cell carries its ID after simultaneous conquest.

Conquest may cut a polity into disconnected components. M2 imposes a contiguous-state convention:

- the largest component retains the parent ID;
- every smaller component receives a new successor ID;
- the parent's surviving treasury is divided in proportion to component resource production.

This turns geopolitical severance into endogenous political fragmentation and restores the invariant that every represented polity occupies one connected territory.

## Observables

`territorial_metrics` reports:

- number of surviving states;
- mean and largest state size;
- largest territorial share;
- capability Herfindahl concentration (`power_hhi`);
- effective number of powers (`1 / HHI`);
- largest capability share;
- cross-polity border edges;
- battles, successful battles, and territorial conquests;
- territorial turnover;
- extinctions and fragmentations.

These quantities are computed for every generation by `territorial-ensemble`, allowing trajectories to be compared across initial maps and future theory-specific policy rules.

## Verified invariants and checks

The test suite verifies that:

- interior cells have exactly six hex neighbors;
- every undirected hex edge is enumerated once;
- initial maps replay exactly for a fixed seed;
- every initial polity is contiguous;
- cell identity remains stable when political control changes;
- local resources aggregate correctly to polity production;
- an overwhelmingly stronger polity conquers and can extinguish a one-cell rival;
- disconnected components become new successor states and inherit treasury proportionally;
- fixed seeds replay identical territorial histories;
- ensemble commands write trajectories, maps, and plots end to end.

## Interpretive boundary

M2 establishes a functioning artificial geopolitical world. It does **not** yet test structural realism or offensive realism. The opportunistic baseline contains assumptions—one attack per state, local adjacency, aggregate treasuries, perfect knowledge of current local strength—that will shape its outcomes.

The next comparative milestone should preserve M2 and introduce matched decision-rule families:

1. a minimal security-seeking rule that stops accumulating or expanding beyond a defensible threshold;
2. a Waltzian balancing rule responding to the distribution and growth of capabilities;
3. a Mearsheimerian relative-power rule that values expansion beyond immediate sufficiency.

Their differences should be isolated in policy selection rather than hidden inside different worlds.
