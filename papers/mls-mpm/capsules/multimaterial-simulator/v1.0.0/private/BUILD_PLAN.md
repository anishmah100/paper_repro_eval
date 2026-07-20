# Private build and calibration plan

Status: specified; not benchmark-ready.

1. Pin source, engine, compiler/runtime dependencies, and visible fixtures.
2. Implement the candidate protocol and a deterministic trusted runner.
3. Build a positive reference and generate canonical replay artifacts.
4. Implement private measurements for: simulation-validity, transfer-and-invariants, hidden-scene-fidelity, material-frontier, throughput.
5. Add hidden cases spanning easy, discriminating, and ceiling regimes.
6. Add at least two mutants: one superficially plausible algorithmic error and one score-hacking or
   cherry-picking strategy.
7. Measure repeatability and set normalization bounds without using candidate results.
8. Review side-by-side artifacts and promote only after invalid-but-attractive outputs cannot win.

Winner rule: Highest qualifying physical-fidelity score across hidden material scenes wins.
