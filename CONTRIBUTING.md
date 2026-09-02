# Contributing

Contributions are welcome when they make a theoretical mechanism, experiment, replication, or spatial invariant clearer and more reproducible.

Before opening a substantial pull request, describe:

1. the IR concept or published model being implemented;
2. the information available to each cell or polity;
3. the transition or policy rule;
4. which existing world mechanics are reused and which must change;
5. the expected macro-pattern, rival explanation, and failure condition;
6. the smallest deterministic test demonstrating that the mechanism is live.

For M3 and later theory rules, keep the M2 world, battle resolver, initial maps, and measurements shared whenever possible. A rival theory should not quietly receive a friendlier geography or a different combat engine.

Run before submitting:

```bash
ruff check .
pytest --cov=international_life --cov-report=term-missing
```

Please do not add large frameworks, provider calls, opaque learned components, or new evaluation layers unless a concrete experiment requires them. The default is a small executable model whose causal structure and event trace can be inspected.
