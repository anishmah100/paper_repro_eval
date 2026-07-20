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

Provide `submission/design.json` and persistent `submission/controller.sh`, or a single documented
portable policy artifact accepted by the supplied runner. Provide train.sh when needed and
reproduce.sh for visible terrains.

Required visuals include morphology, actuation phase, center-of-mass trace, nominal success, hidden-
style perturbation, and representative failure. REPORT.md must explain encoding, search algorithm,
budget, fitness shaping, validation distribution, and morphology/controller interaction.
