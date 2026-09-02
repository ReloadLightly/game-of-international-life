# Contributing

Contributions are welcome when they make a theoretical mechanism, computational experiment, replication, invariant, or result easier to inspect and reproduce.

## Before proposing a substantive model

Describe:

1. the IR concept, theory, or published model being implemented;
2. the state carried by cells, polities, relations, and the system;
3. the information available to each decision rule;
4. the exact action or transition rule;
5. which world mechanics are shared and which variable is the treatment;
6. the expected macro-pattern and at least one rival explanation;
7. a direct process observable showing that the mechanism is active;
8. a failure condition;
9. the smallest deterministic test demonstrating the implementation;
10. the matched or held-out worlds used for comparison.

A theory should not receive a friendlier geography, lower combat threshold, better information, or different random shocks unless that difference is itself the declared treatment.

## Development checks

```bash
ruff check .
pytest --cov=international_life --cov-report=term-missing
```

New experiment commands should write machine-readable configuration, run-level data, aggregate data, and plots derived from saved histories or tables.

## Scope discipline

Please avoid adding large frameworks, provider calls, opaque learned components, governance layers, or generic evaluator infrastructure unless a concrete data-bearing experiment requires them. The default contribution should be a small executable model with visible causal structure.

For evolutionary work, keep candidate representations interpretable, use hand-coded theory baselines, evaluate across distributions of worlds, and archive behavioral diversity rather than only a best scalar score.
