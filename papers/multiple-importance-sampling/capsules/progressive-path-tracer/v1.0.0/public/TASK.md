# Progressive Competitive Path Tracer

> **Read `EXECUTABLE_CONTRACT.md` first.** It defines the exact v1 process protocol, JSON schema,
> scored behavior, and fidelity boundary. The broader paper-oriented goals below describe valuable
> educational extensions; they do not override the compact executable contract.

Implement a C++ path tracer and display its progressive output through the supplied OpenGL shell.
The central reproduction is multiple importance sampling using complementary light and BSDF
sampling. Public code and libraries are allowed; another candidate's output is not.

A submission may add BVHs, better sampling, GGX, dielectric transport, Russian roulette, adaptive
sampling, denoising, or other improvements. The competition rewards correct equal-time images, not
the longest feature list.

## Evaluation

Visible and hidden scenes stress diffuse transport, small lights, glossy lobes, glass, occlusion,
and mixed sampling regimes. The verifier compares equal-time and equal-sample renders against
high-sample references. It measures image error, variance across seeds, bias/energy checks, and
throughput. Any denoising must be disclosed and is scored on held-out scenes.

## Candidate interface

Provide `submission/render.sh SCENE.json OUTPUT.exr METRICS.json`. It must accept seed, dimensions,
sample or time budget, and feature flags from the scene file. Provide a CMake build and
`submission/demo.sh OUTPUT_DIR` for progressive visualization.

Required artifacts include equal-time PNG/EXR renders, variance or error heatmaps, a canonical scene
orbit, and raw timing/sample counts. REPORT.md must explain the estimator, PDFs and MIS weights,
termination policy, acceleration structure, validation, and known bias.

## Executable contract (v1.0.0)

`EXECUTABLE_CONTRACT.md` is authoritative for commands, fields, deadlines, scored measurements,
and what is or is not mechanically verified. Use `resources/visible-case.json`, `starter/`, and
`arena_kit/` for development. The sealed `submission/` must be self-contained. Three deterministic
hidden seeds vary only fields represented by the public schema. The verifier preserves per-case JSON
and PNG evidence, geometrically aggregates quality, and assigns zero to malformed, non-finite,
missing, failed, timed-out, or protocol-invalid results.
