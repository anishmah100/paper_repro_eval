# Exact executable contract: compact inverse-smoke proxy

This v1 capsule optimizes controls for a supplied 2D semi-Lagrangian-style density kernel. It is a
small inverse-control proxy inspired by Stable Fluids, not a full Navier–Stokes reproduction.

The harness runs `bash control.sh CASE.json OUTPUT.json` from `submission/`. The case contains a
target density image, grid size, source cell, and number of steps. Write
`{"controls": STEPSx2_FLOAT_ARRAY}`. Components are clipped to `[-1,1]`; shorter sequences receive
zero action for missing steps.

The trusted simulator scores normalized correlation between final smoke density and the hidden
target. Hidden cases vary target location/scale, source relationship, seed, and difficulty.
Malformed/non-finite sequences, command failure, or timeout score zero. Search, differentiable
optimization, surrogate models, and richer smoke visualizations are allowed and should be explained,
but the compact control sequence is the v1 ranking artifact.
