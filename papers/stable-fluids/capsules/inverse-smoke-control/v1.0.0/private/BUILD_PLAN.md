# Private readiness record

Status: benchmark-ready; not independently audited.

Implemented evidence:

- deterministic trusted runner and task-native candidate protocol;
- hidden cases spanning multiple seeds and difficulty levels;
- private positive reference plus malformed and plausible failing mutants;
- private measurements for: control-format, visible-targets, hidden-target-match, perturbation-robustness, control-efficiency;
- evaluator-generated numerical and visual evidence;
- repeatable calibration ordering and fail-closed protocol handling;
- end-to-end prepare, seal, reproduce, verify, and review-packet smoke coverage.

Residual limitations:

- the arena is a faithful scale reduction or proxy, as declared in capsule.yaml;
- the private reference is a calibration frontier, not a proof of global optimality;
- independent audit remains required before changing the status to audited.

Winner rule: Highest qualifying target-match score under hidden perturbations wins.
