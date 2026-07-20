# Exact executable contract: compact structural-layout proxy

This v1 capsule scores a small density-layout problem using trusted connectivity, load-path
alignment, and material-volume measurements. It is inspired by SIMP topology optimization but does
not currently run or verify a finite-element compliance solve.

The harness runs `bash optimize.sh CASE.json OUTPUT_DIR` from `submission/`. The case contains grid
height/width, material-volume limit, and one or more loads. Write `OUTPUT_DIR/result.json` as
`{"density": HxW_FLOAT_ARRAY}`. Values are interpreted in `[0,1]`; use the exact requested shape.

The objective rewards material connected from the supported left boundary to load cells, alignment
with a useful load path, and compliance with the volume fraction. Hidden cases vary grid size, load
height/direction/count, seed, and difficulty. Disconnected, over-volume, malformed, non-finite, or
timed-out designs cannot win. FEA, sensitivities, filtering, and animated optimization are valuable
extensions but must be described as extensions beyond the exact v1 score.
