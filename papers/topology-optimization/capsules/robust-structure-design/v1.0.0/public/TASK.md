# Robust Topology-Optimization Challenge

> **Read `EXECUTABLE_CONTRACT.md` first.** It defines the exact v1 process protocol, JSON schema,
> scored behavior, and fidelity boundary. The broader paper-oriented goals below describe valuable
> educational extensions; they do not override the compact executable contract.

Implement a density-based topology optimizer and design the strongest feasible structures for
visible and hidden boundary/load configurations. Reproduce the compact SIMP method, then improve it
through filtering, continuation, better optimization, multiresolution, or robust objectives.

## Competition

Every case fixes a finite-element grid, supports, load distribution, volume fraction, material law,
and evaluation budget. The verifier recomputes compliance, volume, connectivity, stress diagnostics,
and manufacturability. It includes hidden load directions and perturbed supports. Infeasible or
numerically invalid structures cannot win, regardless of appearance.

## Candidate interface

Provide `submission/optimize.sh CASE.json OUTPUT_DIR`. Write density.npy or a documented portable
density grid, metrics.json, convergence.csv, and visual frames. The evaluator will independently
solve the submitted design.

The demo must animate density evolution and show final density, displacement, and stress fields.
REPORT.md must describe FEA assembly, sensitivities, optimizer, filters, convergence, constraints,
and the difference between nominal and robust performance.

## Executable contract (v1.0.0)

`EXECUTABLE_CONTRACT.md` is authoritative for commands, fields, deadlines, scored measurements,
and what is or is not mechanically verified. Use `resources/visible-case.json`, `starter/`, and
`arena_kit/` for development. The sealed `submission/` must be self-contained. Three deterministic
hidden seeds vary only fields represented by the public schema. The verifier preserves per-case JSON
and PNG evidence, geometrically aggregates quality, and assigns zero to malformed, non-finite,
missing, failed, timed-out, or protocol-invalid results.
