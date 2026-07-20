# Soft-Robot Morphology and Control Co-Design

Use the supplied fast voxel or mass-spring simulator to design both a soft robot body and its
controller. The result should locomote across varied terrain rather than exploit one visible flat
course. Evolution, policy optimization, indirect encodings, hand design, or hybrids are allowed.

## Competition

The verifier checks connectivity, material and actuator budgets, then evaluates distance, progress,
energy, stability, and integrity on visible and hidden terrains. Hidden evaluation changes slopes,
gaps, friction, material stiffness, actuator strength, and initial phase. The primary score emphasizes
robust progress rather than one spectacular rollout.

## Candidate interface

Provide `submission/design.sh CASE.json OUTPUT.json`, returning the morphology and controller
parameters used by the trusted simulator. Provide `train.sh` when needed and `reproduce.sh` for
visible terrains.

Required visuals include morphology, actuation phase, center-of-mass trace, nominal success, hidden-
style perturbation, and representative failure. REPORT.md must explain encoding, search algorithm,
budget, fitness shaping, validation distribution, and morphology/controller interaction.

## Executable contract (v1.0.0)

The trusted harness invokes the task-native command and artifact interface defined above; it does
not substitute a generic solver API. Use `resources/visible-case.json` and the public arena kit for
development. Native entry-point scripts are supplied in `starter/` and the sealed submission must
be self-contained. Persistent agents receive JSON records one line at a time.

Three deterministic undisclosed seeds increase geometry or control difficulty. The verifier
reconstructs claimed metrics with trusted dynamics, preserves per-case JSON and PNG evidence, and
takes the geometric mean of quality. Malformed, non-finite, missing, or protocol-invalid results
score zero. Hidden cases change only fields represented by the visible schema.
