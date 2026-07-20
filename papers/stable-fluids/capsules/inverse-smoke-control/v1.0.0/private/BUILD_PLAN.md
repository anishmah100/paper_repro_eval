# Private build and calibration plan

Status: specified; not benchmark-ready.

1. Pin source, engine, compiler/runtime dependencies, and visible fixtures.
2. Implement the candidate protocol and a deterministic trusted runner.
3. Build a positive reference and generate canonical replay artifacts.
4. Implement private measurements for: control-format, visible-targets, hidden-target-match, perturbation-robustness, control-efficiency.
5. Add hidden cases spanning easy, discriminating, and ceiling regimes.
6. Add at least two mutants: one superficially plausible algorithmic error and one score-hacking or
   cherry-picking strategy.
7. Measure repeatability and set normalization bounds without using candidate results.
8. Review side-by-side artifacts and promote only after invalid-but-attractive outputs cannot win.

Winner rule: Highest qualifying target-match score under hidden perturbations wins.
