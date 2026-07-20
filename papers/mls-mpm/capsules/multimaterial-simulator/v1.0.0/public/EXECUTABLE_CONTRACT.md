# Exact executable contract: compact material-trajectory proxy

This v1 capsule scores a small deterministic particle-trajectory kernel across jelly, snow, and
water-like material labels. It is inspired by MLS-MPM state evolution but does not mechanically
verify a full MLS-MPM grid transfer, stress tensor, or constitutive implementation.

The harness runs `bash simulate.sh SCENE.json OUTPUT_DIR` from `submission/`. The scene contains
initial 2D particle positions, material, step count, timestep, and gravity. Write
`OUTPUT_DIR/result.json` as `{"frames": STEPSxPARTICLESx2_FLOAT_ARRAY}`. Every frame must contain the
same particles in the same order.

The trusted kernel compares the entire trajectory with material-specific hidden dynamics using
RMSE, while checking shape, finite values, and particle count. Hidden cases vary positions,
material, seed, and difficulty. Malformed state, missing frames, command failure, or timeout scores
zero. A C++/OpenGL simulator is a valuable visual extension, but only the portable trajectory
interface is required for v1 scoring.
