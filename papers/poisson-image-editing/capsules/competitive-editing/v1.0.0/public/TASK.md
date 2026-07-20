# Competitive Poisson Editing Laboratory

Implement the gradient-domain image-editing methods in the supplied paper and build a small
interactive C++ application. You may use OpenGL for display and any reasonable sparse linear
algebra library. Normal internet use and public implementations are allowed. Do not inspect another
candidate's workspace or output.

This is both a reproduction and a competition. A basic seamless clone qualifies; the winner is the
submission with the strongest numerical and perceptual result over unseen edits.

## Required capabilities

1. Ordinary seamless cloning from source, target, offset, and arbitrary binary mask.
2. Mixed-gradient cloning.
3. Masks with holes, disconnected components, and contact with image boundaries.
4. At least one additional paper-derived operation: illumination change, texture flattening, or
   seamless tiling.
5. An interactive viewer that can move the source region and switch methods.

The evaluator will use canonical visible cases and hidden source/target/mask combinations. It will
measure the discrete Poisson residual, boundary consistency, seam-gradient error, image quality
against a trusted solve, and runtime. Hard-coded visible outputs cannot score on hidden cases.

## Candidate interface

Provide `submission/run_case.sh CASE.json OUTPUT_DIR`. CASE.json identifies source and target PNG
files, mask PNG, offset, mode, and solver tolerance. Write `result.png`, `metrics.json`, and enough
intermediate data to recompute the residual. Provide `submission/demo.sh OUTPUT_DIR` for the
interactive or recorded demonstration.

## Required submission artifacts

- `submission/reproduce.sh`, honoring `REPRO_OUTPUT_DIR`;
- `submission/REPORT.md` with equations, solver choice, validation, deviations, and limitations;
- source and build files;
- a canonical comparison grid and seam-error heatmap;
- deterministic settings for every scored case.

Qualification requires a valid build, a fresh result, and a numerically meaningful Poisson solve.
The private verifier, not the candidate's own metrics, determines the score.
