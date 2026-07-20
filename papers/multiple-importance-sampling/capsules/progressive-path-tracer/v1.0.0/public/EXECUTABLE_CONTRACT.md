# Exact executable contract: compact rendering reconstruction proxy

This v1 capsule scores image synthesis for a small procedural sphere-and-light scene. It is a
rendering algorithm/software proxy motivated by multiple-importance sampling, not a mechanically
verified claim that the submission implemented a production path tracer or MIS estimator.

The harness runs `bash render.sh SCENE.json OUTPUT.json METRICS.json` from `submission/`.
`SCENE.json` contains width, height, colored spheres, and a light descriptor. Write `OUTPUT.json` as
`{"image": HxWx3_FLOAT_ARRAY}` in linear RGB `[0,1]`; write valid JSON to `METRICS.json` for human
inspection. The evaluator recomputes image error against its deterministic scene reference.

Hidden scenes change object count, locations, radii, colors, and light values. Wrong shape,
missing/non-finite JSON, command failure, or timeout scores zero. A C++/CMake progressive renderer,
variance heatmaps, and an MIS analysis materially improve the educational artifact, but v1 ranking
is determined by the exact image interface above and runtime—not by unverified feature claims.
