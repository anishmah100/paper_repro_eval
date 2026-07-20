# Progressive Competitive Path Tracer

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
