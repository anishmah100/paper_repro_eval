# Robust Topology-Optimization Challenge

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

The trusted harness invokes the task-native command and artifact interface defined above; it does
not substitute a generic solver API. Use `resources/visible-case.json` and the public arena kit for
development. Native entry-point scripts are supplied in `starter/` and the sealed submission must
be self-contained. Persistent agents receive JSON records one line at a time.

Three deterministic undisclosed seeds increase geometry or control difficulty. The verifier
reconstructs claimed metrics with trusted dynamics, preserves per-case JSON and PNG evidence, and
takes the geometric mean of quality. Malformed, non-finite, missing, or protocol-invalid results
score zero. Hidden cases change only fields represented by the visible schema.
