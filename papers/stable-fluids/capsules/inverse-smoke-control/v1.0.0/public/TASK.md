# Inverse Smoke-Control Research Challenge

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
