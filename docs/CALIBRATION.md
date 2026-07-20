# Visual arena calibration record

The ten visual arenas were promoted to `benchmark-ready` after their task-native protocols,
trusted runners, hidden cases, positive references, failing mutants, fail-closed behavior, and
review-packet generation passed locally on 2026-07-20. They are not independently audited, and the
private references are calibration frontiers rather than claims of global optimality.

## Reproducing the calibration

From the repository root:

```bash
uv sync --extra dev --extra arena
uv run python authoring/calibrate_arenas.py
uv run python authoring/calibrate_interactive.py
uv run python authoring/smoke_arenas.py
uv run python authoring/smoke_tournament.py
```

`calibrate_arenas.py` evaluates deterministic batch contracts. For the persistent control tasks,
its compact one-shot proxy is useful only as a shared scoring sanity check; the authoritative
protocol calibration is in `calibrate_interactive.py`. All scores are normalized to `[0, 1]`.

## Deterministic batch calibration

| Task | Malformed | Plausible mutant | Public baseline | Private frontier | Frontier headroom |
|---|---:|---:|---:|---:|---:|
| Poisson editing | 0.0000 | 0.3192 | 0.8732 | 1.0000 | 0.1268 |
| Multi-pole proxy | 0.0000 | 0.0345 | 0.0484 | 0.1052 | 0.0567 |
| Path tracing | 0.0000 | 0.0000 | 0.6087 | 1.0000 | 0.3913 |
| MLS-MPM | 0.0000 | 0.0000 | 0.6333 | 1.0000 | 0.3667 |
| World-MPC proxy | 0.0000 | 0.0079 | 0.4447 | 0.9867 | 0.5420 |
| Topology optimization | 0.0000 | 0.0000 | 0.3029 | 0.6913 | 0.3885 |
| Inverse smoke | 0.0000 | 0.0584 | 0.0584 | 0.3061 | 0.2477 |
| Soft-robot co-design | 0.0000 | 0.0000 | 0.5239 | 0.8167 | 0.2927 |
| Inverse rendering | 0.0000 | 0.0119 | 0.6479 | 0.9418 | 0.2939 |

Every private frontier was bitwise repeatable in the calibration run, exceeded the public baseline
by at least the declared margin, and exceeded the plausible mutant by at least the declared margin.
Malformed candidate output scored zero. The inverse-smoke plausible mutant intentionally matches
the weak public baseline; both remain well below the positive reference.

## Persistent protocol calibration

| Task | Failing mutant | Public baseline | Private frontier/reference | Headroom |
|---|---:|---:|---:|---:|
| Multi-pole control | zero controller: 0.0632 | 0.0328 | 0.0761 | 0.0433 |
| World-model MPC | zero controller: 0.0028 | 0.6082 | 0.9593 | 0.3511 |
| Lightcycle fixed field | illegal/timeout bots: 0.0000 | 0.4375 | 0.4375 | n/a |

The multi-pole frontier improves both survival and angle RMS over the public baseline. The
world-model frontier reaches near-zero terminal distance while respecting the bounded-action
protocol. Both report zero protocol errors and timeouts.

Lightcycle's fixed reference field is a qualification and sanity test, not the final discriminator;
the public and private legal bots tie there. The illegal mutant produced 16 illegal actions, and the
slow mutant was timed out and failed closed. Candidate separation comes from the direct tournament,
which uses paired starting sides, deterministic symmetric maps, persistent-process deadlines,
points, replay evidence, and uncertainty intervals.

## What the gate establishes

The calibration supports these limited claims:

- valid task-native submissions can execute through the complete lifecycle;
- evaluator measurements separate a positive implementation from relevant broken strategies;
- malformed, illegal, non-finite, and timed-out outputs cannot win by default;
- hidden evidence and raw state are preserved for a quick human trust audit;
- the score retains nontrivial headroom above the public starter on the independent-score arenas.

It does not establish that a score perfectly measures research utility, that difficulty labels will
remain stable across future models, that the private frontier is optimal, or that scale-reduced
results transfer without qualification to the full original paper. Pilot results should therefore
be reported alongside raw metrics, visuals, failure cases, and the capsule's fidelity limitations.
