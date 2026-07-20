# Visual arena protocol

Every visual arena is an ordinary paper-reproduction capsule with one extra property: the trusted
verifier emits a continuous `objective-score`, so qualifying submissions can be ranked rather than
only passed or failed.

The prepared workspace exposes `TASK.md`, paper material, resources, starter code, and an empty
`submission/` directory. Private cases, reference implementations, calibration mutants, and score
code are never copied. Each model receives a separately initialized Git repository containing an
identical public tree. Models may use the network and any tools available to their native coding
assistant, but must never inspect another model's run directory.

## Candidate contract

Each task defines one command under `submission/`. Batch tasks consume a public or hidden JSON case
and write machine-readable state plus a PNG or GIF replay. Interactive tasks use newline-delimited
JSON over standard input and output. Randomness is seeded. Candidate output is treated as a claim:
the trusted verifier reconstructs or simulates the result wherever practical.

## Score contract

Scores lie in `[0, 1]`; higher is better. A separate qualification check covers buildability,
protocol conformance, finite values, and required evidence. Scientific metrics are normalized
against an intentionally weak baseline and a private reference frontier. Geometric aggregation
prevents one excellent scene from hiding a catastrophic one. Exact metric definitions and tie
breakers live in each `TASK.md`; hidden cases vary geometry, seeds, and nuisance parameters without
changing the stated problem.

## Evidence and review

Verifiers preserve inputs, logs, raw trajectories, per-case metrics, and contact sheets or replays.
`REPORT.md` is the model's explanation, while the private review guide tells a human what to inspect
first, which visual pathologies indicate cheating or a broken simulation, and which claims deserve
code review. A reviewer can therefore compare the leaderboard, watch the result, and spot-check a
small trusted numerical reconstruction instead of reading the entire submission.

## Calibration gate

An arena is benchmark-ready only when its public smoke implementation executes, its private
reference qualifies, at least one plausible broken mutant scores lower, malformed output fails
closed, and repository validation plus unit tests pass. Calibration records the expected ordering;
it does not promise that the private reference is globally optimal.
