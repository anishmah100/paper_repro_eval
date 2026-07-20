# Exact executable contract: compact morphology/controller co-design proxy

This v1 capsule scores a connected voxel morphology together with two global oscillator parameters.
It is a lightweight co-design proxy inspired by evolutionary soft robotics, not a full mass-spring
or voxel-physics reproduction.

The harness runs `bash design.sh CASE.json OUTPUT.json` from `submission/`. The case contains
`width`, `height`, terrain samples, step count, and a voxel budget. Write a JSON object with
`morphology` as an `HEIGHTxWIDTH` occupancy array plus numeric `frequency` and `phase_gradient`.

The trusted objective checks connectivity and budget, then combines morphology use with an
oscillatory locomotion proxy. Hidden cases vary terrain, seed, and difficulty through the public
schema. Disconnected, over-budget, malformed, non-finite, failed, or timed-out designs cannot win.
Evolution traces and locomotion animations are useful qualitative evidence, but the exact v1 output
is the compact design object above.
