# Exact executable contract: Poisson editing proxy

This v1 capsule scores the discrete seamless-cloning kernel at small image sizes. It is a faithful
scale reduction of the Poisson solve, not a scored requirement to build the larger C++/OpenGL editor
described as an educational extension in `TASK.md`.

The harness runs `bash run_case.sh CASE.json OUTPUT_DIR` from `submission/`. `CASE.json` contains
`source`, `target`, and binary `mask` arrays. RGB values are floats in `[0,1]`. Write
`OUTPUT_DIR/result.json` containing `{"image": HxWx3_FLOAT_ARRAY}` with the same shape.

The trusted evaluator solves the masked sparse Poisson system independently and scores candidate
mean-squared image error. Hidden cases vary image size, color fields, mask position, and mask shape
through the visible schema. Incorrect shape, missing/non-finite JSON, command failure, or timeout
scores zero. A demo/editor is useful qualitative evidence but does not replace this native command.
