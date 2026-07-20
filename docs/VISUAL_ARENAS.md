# Visual Research Arcade index

This is the tracking index for the first visual, competitive research-agent evaluation. Every arena
is designed to be inspectable by watching or manipulating the result and rankable by a quantitative
score. Internet use, public code, and normal assistant tools are allowed. The only forbidden
information flow is one candidate reading another candidate's workspace or output.

All entries are **benchmark-ready**: task-native protocols, hidden fixtures, private references,
failing mutants, deterministic calibration, lifecycle smoke tests, and visual review packets are
implemented. They are not independently audited. See the [calibration record](CALIBRATION.md) and
[operating guide](RUNNING_AGENTS.md) before running comparisons. Read the
[detailed task catalog](TASK_CATALOG.md) for each capsule's exact proxy boundary.

| Priority | Arena | Capsule | Visual result | Primary competitive signal | Intended frontier |
|---:|---|---|---|---|---|
| 1 | Multi-pole control | dm-control-suite/multipole-control | compact cart/pole trajectories | survival and pole-angle quality | floor through ceiling |
| 2 | Poisson editing | poisson-image-editing/competitive-editing | image grids and seam heatmaps | hidden-case reconstruction quality | floor |
| 3 | Rendering reconstruction | multiple-importance-sampling/progressive-path-tracer | hidden procedural renders | hidden-scene image quality | floor |
| 4 | Structural layout | topology-optimization/robust-structure-design | density and load-path fields | connectivity/alignment under volume | middle through hard |
| 5 | Lightcycle tournament | lightcycle-agents/adversarial-tournament | direct bot match replays | tournament points and rating | floor through ceiling |
| 6 | Inverse smoke control | stable-fluids/inverse-smoke-control | target/density overlays | final target overlap | hard/open-ended |
| 7 | Landing-control proxy | differentiable-world-model-mpc/visual-offline-control | point-mass target trajectories | terminal distance and effort | hard |
| 8 | Material trajectory proxy | mls-mpm/multimaterial-simulator | jelly/water/snow particle replays | full-trajectory fidelity | floor through middle |
| 9 | Soft-robot co-design proxy | evolutionary-soft-robots/morphology-control-codesign | morphology and parameter plots | terrain-conditioned proxy quality | middle |
| 10 | Procedural inverse rendering | inverse-rendering/procedural-scene-recovery | target/reconstruction camera orbits | held-out-view image quality | open-ended |

## Work states

Use these states in planning notes:

1. **specified** — public task and score contract exist;
2. **scaffolded** — common engine, fixtures, and candidate interface run;
3. **reference-complete** — trusted reference produces canonical artifacts;
4. **calibrated** — mutants and repeatability locate meaningful thresholds;
5. **benchmark-ready** — private verifier and human packet reviewed;
6. **audited** — an independent reviewer has rerun and inspected the task.

The manifests deliberately use the framework's formal status values: draft, benchmark-ready,
audited, deprecated. This index supplies the more granular authoring state.

## Implementation history

The common deterministic replay, offscreen rendering, artifact capture, and score serialization
layer was built before the task-specific engines. The arenas were then onboarded in this order:

1. Poisson editing and multi-pole control for end-to-end plumbing.
2. Topology optimization and path tracing for continuous visual leaderboards.
3. Lightcycle for head-to-head tournament orchestration.
4. Inverse smoke and world-model control for research optimization.
5. Material-trajectory, co-design, and inverse-rendering proxies as initial ceiling hypotheses.

No future task should be promoted merely because it launches. Promotion requires a reference,
hidden cases, score calibration, and evidence that visually impressive invalid solutions cannot
win. The current arenas passed that local gate; `audited` remains reserved for independent review.
