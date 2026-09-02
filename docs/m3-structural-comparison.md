# M3 specification — Security seeking versus power maximization

## 1. Purpose

M3 is the first matched rival-rule experiment in **Game of International Life**. It asks:

> What system-level differences arise when a polity stops expanding after reaching a declared security threshold, compared with a polity that continues exploiting favorable relative-power opportunities?

The experiment is inspired by the contrast between defensive and offensive structural realism. It does **not** claim that either policy is a complete computational rendering of Kenneth Waltz or John Mearsheimer. The purpose is narrower and more falsifiable: isolate one consequential disagreement—the stopping rule—and make its process and systemic effects observable inside a shared artificial world.

M3 is a **discriminating computational experiment**, not an empirical test of historical international politics.

## 2. The comparison contract

The experiment is valid only if the policy objective is the intended difference. Both rule families therefore share:

- the same hexagonal geography;
- the same territorial borders and polity identities at generation zero;
- the same local resource field;
- the same exact initial capability shares;
- the same treasury, production, decay, and mobilization equations;
- the same fortification and power-projection mechanics;
- the same candidate target generator;
- the same attack feasibility threshold;
- the same one-order-per-polity action budget;
- the same simultaneous territorial update;
- the same battle resolver and cost functions;
- the same extinction and fragmentation mechanics;
- the same stochastic shock assigned to any encounter shared across runs.

Every initial world is hashed with SHA-256 over the policy-visible arrays:

```text
polity control map
resource field
fortification field
treasury vector
```

The two policy histories in a matched pair must have the same fingerprint. The experiment aborts if they do not.

## 3. State and topology

The territorial substrate is inherited from M2.

A world is an odd-row offset hexagonal lattice. Each site has six or fewer geographic neighbors under fixed boundaries. A site carries:

- stable geographic identity;
- local resource productivity;
- local fortification;
- a mutable polity ID identifying its current controller.

A polity controls a connected set of cells. It also holds a treasury indexed by a non-recycled polity ID. If conquest divides a polity into disconnected territorial components, the largest component keeps the parent ID and each detached component becomes a traceable successor polity.

The model distinguishes:

1. **site-level geography**, which persists;
2. **polity-level agency**, which aggregates over controlled sites;
3. **system-level structure**, which is measured from the distribution of capabilities and territorial relations.

## 4. Shared political economy

Let:

- `R_x` be the fixed resource productivity of cell `x`;
- `P_i(t)` be the sum of resources controlled by polity `i` at generation `t`;
- `T_i(t)` be its treasury;
- `δ` be reserve decay;
- `ρ` be the production rate entering the available treasury.

The available treasury before policy choice is:

```text
A_i(t) = (1 − δ) T_i(t) + ρ P_i(t)
```

The broader capability observable used for structural comparison is:

```text
C_i(t) = T_i(t) + P_i(t)
```

`A_i` represents resources immediately available to the territorial contest. `C_i` represents the polity's treasury plus one gross production turn and is used to calculate capability shares, polarity, and the policy's security comparison.

## 5. Shared local attack candidates

A policy may target only a directly adjacent foreign cell and may issue at most one order per generation.

### 5.1 Border dispersion

Let `B_i` be the number of border cells held by polity `i`, `m` the mobilization fraction, and `A_i` its available treasury. Its projected field strength is:

```text
F_i = m A_i / √B_i
```

The square-root denominator creates a transparent concentration-versus-overextension trade-off. A polity with a longer frontier cannot project its entire available capability at full strength onto every border site.

### 5.2 Local concentration

For target cell `x`, the shared candidate builder counts adjacent attacker-controlled and defender-controlled cells. These counts modify projected strength through a support bonus.

Predicted attack strength is:

```text
attack(i, x) = offense_multiplier × F_i × local_attack_concentration(i, x)
```

Predicted defense strength is:

```text
defense(j, x) =
    defense_multiplier × F_j × local_defense_concentration(j, x)
    + garrison_strength × R_x
    + fortification_value × fortification_x
```

The expected local force ratio is:

```text
Q(i, j, x) = attack(i, x) / defense(j, x)
```

A candidate is feasible only when:

```text
Q(i, j, x) ≥ attack_threshold
```

Both policies receive the complete same candidate set. This is crucial: the power-maximizing rule is not allowed to attack weaker defenses under a more permissive combat model.

## 6. Policy-visible information

At each generation, both policies can observe:

- the complete current territorial control map;
- the fixed local resource field;
- current fortification;
- polity treasuries;
- aggregate production and capability of all living polities;
- which polities are territorially adjacent;
- predicted attack and defense values for adjacent target cells.

This is a full-information first baseline. Partial observability, mistaken beliefs, and strategic deception belong in later milestones. Keeping perception fixed in M3 prevents informational assumptions from being confounded with the stopping-rule comparison.

## 7. Security-seeking policy

For polity `i`, let `N_i` be the set of adjacent rival polities. The security ratio is:

```text
S_i = C_i / max(C_j for j in N_i)
```

The default sufficiency threshold is:

```text
S* = 1.10
```

The rule is:

```text
if S_i ≥ S*:
    abstain
else:
    choose the highest-scoring feasible security-repair target
```

For each feasible target, the score combines:

- the expected local force ratio;
- the relative capability of the target's controller;
- whether taking the cell shortens or worsens the frontier;
- target-cell resource productivity.

In the default implementation:

```text
security_score =
    expected_force_ratio
    + 0.90 × defender_share / attacker_share
    + 0.10 × border_relief / 6
    + 0.08 × target_resource_ratio
```

The defining feature is not the exact target score. It is the **sufficiency stopping rule**. Once the polity reaches `S*`, additional relative power has no independent value in this policy.

The policy is best understood as a minimal **security-seeking expansion proxy**. It does not yet model peaceful internal balancing, alliance formation, arms procurement choices, or doctrinal adaptation.

## 8. Power-maximizing policy

The power-maximizing policy receives the same candidate set and applies the same attack threshold. It does not stop at security sufficiency.

Its default score is:

```text
power_score =
    expected_force_ratio
    + 80.0 × expected_relative_capability_gain
    + 1.00 × defender_power_share
    + 0.12 × target_resource_ratio
    + 0.05 × border_relief / 6
```

The expected relative gain from taking cell `x` is operationalized as:

```text
R_x / total_system_capability
```

This is the immediate increase in the attacker's gross productive capability as a share of the current system total, before subsequent feedback.

The policy therefore values:

- feasible conquest;
- future productive capability;
- gains at the expense of powerful rivals;
- continued accumulation after security sufficiency.

It is a minimal **relative-power opportunity proxy**. It does not yet model global hegemony as an explicit terminal objective, balancing coalitions, uncertainty about intentions, or long-horizon strategic planning.

## 9. Shared battle resolution

An issued order receives independent multiplicative attack and defense shocks. To preserve common random numbers across divergent policy runs, the random stream is keyed to:

```text
battle seed
current generation
attacker polity ID
defender polity ID
target cell ID
```

It is not keyed to the order's position in a list. Therefore, adding an unrelated attack elsewhere does not change the random shock applied to a shared encounter.

A battle succeeds when realized attack strength exceeds realized defense strength. Attacker and defender pay explicit costs proportional to realized strength. When multiple successful attackers target the same cell, the winner is selected by realized attack-to-defense ratio, then attack strength, then a deterministic polity-ID tie-break.

All transfers are applied to the next control map, preserving synchronous updating.

## 10. Structural conditions

M3 uses a `2 × 2 × 2` design.

### 10.1 Capability distribution

With the default eight initial polities:

- **Balanced:** each polity begins with exactly `1/8 = 0.125` of total capability.
- **Dominant power:** one polity begins with `0.35`; the remaining `0.65` is divided equally among seven others.

Treasury is reallocated to achieve exact shares while preserving:

- total system capability;
- geography;
- resource locations;
- fortification.

The balanced initial HHI is `0.125`. The dominant-power HHI is approximately `0.182857`.

### 10.2 Resource geography

- **Diffuse:** low-dispersion resource draws with moderate local smoothing.
- **Clustered:** high-dispersion resource draws with stronger smoothing, creating spatially concentrated productive regions.

The same seed preserves the territorial map across the two resource regimes. Resource distributions change, not political geography.

### 10.3 Policy rule

- security seeking;
- power maximizing.

For each capability × resource × seed world, both policies begin from the exact same state.

## 11. Default reference run

The v0.3 reference run uses:

```text
world shape:              12 × 16 hex cells
initial polities:         8
steps:                    40
seeds per structure:      6
capability regimes:       balanced, dominant-power
resource regimes:         diffuse, clustered
policies:                 security-seeking, power-maximizing
policy histories:         48
matched policy pairs:     24
attack threshold:         0.98
battle noise:             0.06
security threshold:       1.10
```

The exact configuration is recorded in [`results/m3-reference-manifest.json`](results/m3-reference-manifest.json).

## 12. Observables

### 12.1 Process observables

- attack orders;
- attacks launched after security sufficiency;
- security-repair attacks;
- relative-power attacks;
- mean security ratio of attackers;
- battles and successful battles;
- realized war costs;
- conquests and territorial turnover;
- fragmentation and extinction events.

### 12.2 System outcomes

- number of surviving states;
- survival rate of original states;
- largest territorial share;
- capability HHI;
- effective number of powers (`1 / HHI`);
- largest capability share;
- interstate border length.

Process observables are not auxiliary decoration. Two theories can generate similar final polarity through different causal paths. M3 is designed to reveal that possibility rather than hiding it behind one final score.

## 13. Directional hypotheses

M3 freezes the following expectations before interpreting its reference outputs.

### H1 — Stopping-rule separation

The security-seeking policy should launch zero attacks once `S_i ≥ S*`. The power-maximizing policy should launch some feasible attacks while already at or above `S*` in at least part of the tested world distribution.

This is the primary mechanism-liveness criterion.

### H2 — Systemic expenditure

Power maximization should, on average, generate more attack orders and greater cumulative war cost because opportunity remains valuable after security sufficiency.

This is an ensemble expectation, not a requirement for every seed. Endogenous feedback can cause an initially more aggressive history to eliminate opportunities sooner.

### H3 — Territorial and capability concentration

Power maximization should, on average, generate more conquest and greater final capability concentration, especially where initial dominance or clustered resources create compounding opportunities.

### H4 — State survival

Higher conflict and concentration under power maximization should, on average, reduce the survival of original states and the final state count.

### H5 — Structural interaction

The gap between policies should vary across capability and resource regimes. A stopping rule that matters only under one specially tuned map is less theoretically interesting than one whose effects can be mapped across structural conditions.

## 14. Reference-run mechanism check

Across the 24 matched v0.3 policy pairs, the mean `power-maximizing minus security-seeking` differences were:

| Observable | Mean paired difference |
|---|---:|
| Attack orders | +21.54 |
| Attacks after security sufficiency | +31.63 |
| Cumulative war cost | +135.73 |
| Territorial conquests | +20.83 |
| Final capability HHI | +0.041 |
| Original-state survival rate | −0.115 |
| Final state count | −0.96 |

The primary check passes: every reference pair contains at least one post-sufficiency attack by the power-maximizing policy, while the security-seeking policy contains none by construction.

The aggregate directions also align with H2–H4 in this small reference ensemble. They should not be treated as validated general laws. Individual paired runs include reversals in attack count, war cost, conquest, concentration, and state survival. Those reversals are scientifically useful because they identify worlds in which feedback overwhelms the direct policy tendency.

Compact reference outputs are committed in [`results/`](results/). The full trajectories are regenerated by the command below rather than stored in the repository.

## 15. Failure criteria

M3 would be uninformative or misleading under any of the following conditions:

1. **No policy separation.** Neither policy ever reaches or acts beyond security sufficiency.
2. **Different worlds.** Matched policy runs receive different initial arrays or unrelated shocks for shared encounters.
3. **Hidden feasibility advantage.** One policy receives a lower attack threshold or stronger battle mechanics.
4. **Outcome-only equivalence.** Final maps differ, but no process trace reveals why.
5. **Hard-coded conclusion.** The environment directly rewards or enforces a particular polarity or survival outcome.
6. **Single-seed storytelling.** Interpretation rests on one attractive map rather than paired ensembles.
7. **Theory inflation.** A minimal stopping-rule result is described as a complete test of Waltz or Mearsheimer.
8. **Parameter fragility.** The comparison disappears under small, theoretically reasonable changes in thresholds or world structure.

M3 addresses the first seven directly. Systematic sensitivity analysis for the eighth belongs in the next structural-comparison refinement.

## 16. Reproduction

Install the project, then run:

```bash
international-life m3 --output-dir artifacts/m3
```

The command writes:

```text
m3_manifest.json
m3_timeseries.csv
m3_run_summary.csv
m3_ensemble_summary.csv
m3_paired_differences.csv
m3_matched_worlds.png
m3_attacks_while_secure.png
m3_war_cost.png
m3_power_concentration.png
```

For a smaller smoke run:

```bash
international-life m3 \
  --height 6 \
  --width 8 \
  --states 4 \
  --steps 5 \
  --seeds 1 \
  --dominant-share 0.40 \
  --output-dir artifacts/m3-smoke
```

## 17. Interpretive limits

M3 currently assumes:

- full and accurate observation;
- homogeneous decision rules within each run;
- one attack order per polity per generation;
- no diplomacy, bargaining, alliances, or reassurance;
- no peaceful investment decision separate from treasury accumulation;
- fixed local resource productivity;
- adjacent territorial power projection only;
- myopic target selection rather than multi-step planning;
- no domestic politics;
- no nuclear deterrence, technology, trade, or institutions.

These limitations are not hidden defects. They define what the experiment can and cannot claim. The value of M3 is causal austerity: it creates a clean baseline from which alliance structure, incomplete information, heterogeneous strategies, and evolutionary search can be added one mechanism at a time.

## 18. Exact next step

M4 should add **Snyderian alliance politics** as a graph layer above the territorial world. Alliance ties must not be restricted to adjacent cells. The smallest meaningful experiment should vary commitment strength and polarity while measuring abandonment, entrapment, chain-ganging, buck-passing, bloc formation, and conflict diffusion.

M4 should preserve the M3 discipline: alliance rules share the same territory, capabilities, battle mechanics, and shocks, and their trade-offs must appear in process observables rather than only in labels.
