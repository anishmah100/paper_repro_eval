# Inverse Smoke-Control Research Challenge

> **Read `EXECUTABLE_CONTRACT.md` first.** It defines the exact v1 process protocol, JSON schema,
> scored behavior, and fidelity boundary. The broader paper-oriented goals below describe valuable
> educational extensions; they do not override the compact executable contract.

Control jets in a supplied Stable Fluids simulator so smoke matches target silhouettes at specified
times. The simulator, render path, visible targets, and baseline controller are provided. Your task
is open-ended research: design the best optimizer or controller within the evaluation-call budget.

Finite differences, CMA-ES, trajectory optimization, differentiable unrolling, learned surrogates,
model-predictive control, and hybrid methods are all allowed.

## Competition

The trusted simulator scores image-space target similarity over time, control energy, validity, and
robustness to hidden viscosity, timestep, source, and obstacle perturbations. The primary score
combines target match and robustness under a hard action/evaluation budget. Candidate-reported
scores are not trusted.

## Candidate interface

Provide `submission/control.sh CASE.json OUTPUT.json`, returning a bounded time-indexed control
sequence. Provide reproduce.sh for visible targets and a demo that renders target, smoke, difference
heatmap, and control overlays.

REPORT.md must document the optimization method, evaluation budget, simulator assumptions,
validation targets, ablations or failed approaches, and how robustness was addressed.

## Executable contract (v1.0.0)

`EXECUTABLE_CONTRACT.md` is authoritative for commands, fields, deadlines, scored measurements,
and what is or is not mechanically verified. Use `resources/visible-case.json`, `starter/`, and
`arena_kit/` for development. The sealed `submission/` must be self-contained. Three deterministic
hidden seeds vary only fields represented by the public schema. The verifier preserves per-case JSON
and PNG evidence, geometrically aggregates quality, and assigns zero to malformed, non-finite,
missing, failed, timed-out, or protocol-invalid results.
