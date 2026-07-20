# Soft-Robot Morphology and Control Co-Design

> **Read `EXECUTABLE_CONTRACT.md` first.** It defines the exact v1 process protocol, JSON schema,
> scored behavior, and fidelity boundary. The broader paper-oriented goals below describe valuable
> educational extensions; they do not override the compact executable contract.

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

`EXECUTABLE_CONTRACT.md` is authoritative for commands, fields, deadlines, scored measurements,
and what is or is not mechanically verified. Use `resources/visible-case.json`, `starter/`, and
`arena_kit/` for development. The sealed `submission/` must be self-contained. Three deterministic
hidden seeds vary only fields represented by the public schema. The verifier preserves per-case JSON
and PNG evidence, geometrically aggregates quality, and assigns zero to malformed, non-finite,
missing, failed, timed-out, or protocol-invalid results.
