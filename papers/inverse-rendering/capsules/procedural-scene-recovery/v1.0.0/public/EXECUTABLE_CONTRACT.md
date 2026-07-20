# Exact executable contract: compact procedural scene recovery

This v1 capsule recovers a small set of colored circular scene primitives from low-resolution
multi-view observations. It is an inverse-rendering proxy, not recovery of general meshes, BRDFs,
lighting, or cameras.

The harness runs `bash recover.sh CASE.json OUTPUT_DIR` from `submission/`. The case contains width,
height, observed and held-out camera-view offsets, and observed RGB arrays; hidden truth and held-out images are removed. Write
`OUTPUT_DIR/result.json` with `objects`, where each object is `[x, y, radius, red, green, blue]`.
Normalized geometry and colors should remain in `[0,1]`.

The trusted renderer scores observed-view and held-out-view image MSE with a small complexity
penalty. Hidden cases vary primitive count, location, radius, color, views, seed, and difficulty.
Malformed objects, non-finite state, command failure, or timeout score zero. A camera-orbit
comparison and discussion of ambiguity are required qualitative evidence; general differentiable
rendering systems are welcome extensions but are not implied by the v1 score.
