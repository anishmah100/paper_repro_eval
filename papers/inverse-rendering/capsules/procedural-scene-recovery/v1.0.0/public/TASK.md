# Procedural Inverse-Rendering Challenge

Recover a compact 3D scene from a small set of rendered observations. Optimize or infer geometry,
materials, lights, and cameras in the supplied scene language. Differentiable rendering, stochastic
search, procedural priors, computer vision, and hybrid strategies are allowed.

## Competition

The verifier rerenders the submitted scene from observed and hidden cameras. The primary score is
held-out-view image quality, supplemented by geometry/material consistency, valid scene constraints,
complexity, and recovery time. Fitting a billboard to one visible camera should fail badly on hidden
views.

## Candidate interface

Provide `submission/recover.sh CASE.json OUTPUT_DIR`. Write a portable scene.json, predicted
calibration, metrics.json, and convergence trace. Provide reproduce.sh and an interactive or recorded
camera orbit comparing target and reconstruction.

REPORT.md must explain representation, renderer or search method, loss terms, priors, optimization
schedule, ambiguities, validation, and which properties cannot be identified from the observations.
