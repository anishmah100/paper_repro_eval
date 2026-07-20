# Visual Research Arcade index

This is the tracking index for the first visual, competitive research-agent evaluation. Every arena
is designed to be inspectable by watching or manipulating the result and rankable by a quantitative
score. Internet use, public code, and normal assistant tools are allowed. The only forbidden
information flow is one candidate reading another candidate's workspace or output.

All entries are **benchmark-ready**: task-native protocols, hidden fixtures, private references,
failing mutants, deterministic calibration, lifecycle smoke tests, and visual review packets are
implemented. They are not independently audited. See the [calibration record](CALIBRATION.md) and
[operating guide](RUNNING_AGENTS.md) before running comparisons.

| Priority | Arena | Capsule | Visual result | Primary competitive signal | Intended frontier |
|---:|---|---|---|---|---|
| 1 | Multi-pole control | dm-control-suite/multipole-control | synchronized MuJoCo episodes | robust return across pole counts | floor through ceiling |
| 2 | Poisson editing | poisson-image-editing/competitive-editing | image grids and seam heatmaps | hidden-case reconstruction quality | floor |
| 3 | Path tracing | multiple-importance-sampling/progressive-path-tracer | equal-time canonical renders | quality/variance at fixed budget | middle through hard |
| 4 | Topology optimization | topology-optimization/robust-structure-design | evolving density and stress fields | robust compliance under constraints | middle through ceiling |
| 5 | Lightcycle tournament | lightcycle-agents/adversarial-tournament | direct bot match replays | tournament points and rating | floor through ceiling |
| 6 | Inverse smoke control | stable-fluids/inverse-smoke-control | controlled smoke trajectories | target match under energy budget | hard/open-ended |
| 7 | Offline world-model control | differentiable-world-model-mpc/visual-offline-control | rocket landing/docking trajectories | realized robust control score | hard |
| 8 | MLS-MPM simulation | mls-mpm/multimaterial-simulator | elastic, fluid, and snow scenes | physical fidelity plus throughput | hard |
| 9 | Soft-robot co-design | evolutionary-soft-robots/morphology-control-codesign | evolved locomotion replays | robust distance/energy score | open-ended |
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
5. MLS-MPM, soft robots, and inverse rendering as ceiling arenas.

No future task should be promoted merely because it launches. Promotion requires a reference,
hidden cases, score calibration, and evidence that visually impressive invalid solutions cannot
win. The current arenas passed that local gate; `audited` remains reserved for independent review.
