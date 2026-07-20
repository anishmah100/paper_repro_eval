# Human-readable task catalog

This catalog explains the ten assignments in `visual-research-arcade-v0` from the operator's point
of view. It distinguishes three things that should not be conflated:

- the motivating paper or research area;
- the exact compact v1 artifact an agent must build;
- optional larger educational extensions that may make a reproduction more valuable but are not
  silently treated as scored evidence.

Every prepared workspace contains `TASK.md` for the scientific motivation and
`EXECUTABLE_CONTRACT.md` for the authoritative command, schema, deadlines, and fidelity boundary.
The exact contract wins if broader paper-oriented prose suggests a larger system.

## Suite at a glance

| Paper / capsule | Exact v1 artifact | Fidelity | Primary comparison |
|---|---|---|---|
| Poisson image editing / `competitive-editing` | masked RGB Poisson solve | faithful scale reduction | trusted hidden reconstruction error |
| dm_control / `multipole-control` | persistent compact multi-pole controller | proxy | hidden survival and pole-angle RMS |
| Multiple importance sampling / `progressive-path-tracer` | procedural scene image synthesis | proxy | hidden-scene image error |
| MLS-MPM / `multimaterial-simulator` | material-conditioned particle trajectory | proxy | hidden full-trajectory RMSE |
| Differentiable world-model MPC / `visual-offline-control` | persistent 2D landing controller | proxy | terminal distance and action energy |
| Topology optimization / `robust-structure-design` | constrained density/load-path layout | proxy | connectivity, alignment, and material use |
| Lightcycle agents / `adversarial-tournament` | persistent adversarial game bot | proxy | paired-side round-robin match points |
| Stable Fluids / `inverse-smoke-control` | bounded compact smoke-control sequence | proxy | hidden final-density target overlap |
| Evolutionary soft robots / `morphology-control-codesign` | voxel morphology and oscillator | proxy | hidden terrain-conditioned co-design quality |
| Inverse rendering / `procedural-scene-recovery` | colored primitive scene recovery | proxy | observed and held-out rerender error |

“Proxy” is not a euphemism for full reproduction. It means the capsule deliberately preserves a
small algorithmic or systems property so it can run locally and be inspected quickly. These tasks
can compare research-tool behavior and produce educational artifacts, but results must not be
reported as reproducing every mechanism or scale of the motivating paper.

## 1. Competitive Poisson editing

**Paper/capsule:** `poisson-image-editing/competitive-editing@1.0.0`

**Scientific idea.** Gradient-domain editing chooses unknown pixels inside a mask so their discrete
Laplacian follows the source image while boundary neighbors remain anchored to the target. The
result tests whether an agent can turn a PDE statement into a correct sparse linear system and
package the solve robustly.

**What the agent receives.** A visible JSON case containing small source and target RGB arrays and a
binary mask, a weak baseline, the public arena utility, paper material, and starter scripts.

**What it must build.** `submission/run_case.sh CASE.json OUTPUT_DIR` must write
`OUTPUT_DIR/result.json` with an image array of identical shape. It must also package
`reproduce.sh`, `REPORT.md`, and useful visual evidence under `submission/`.

**What is actually scored.** A private sparse solver computes the trusted seamless-cloning result.
Quality is an exponential transform of candidate/reference image MSE over three hidden geometries.
Shape, finiteness, command execution, artifacts, and report presence are checked separately.

**Why models may differ.** A weak model may paste source pixels, return the target, mishandle mask
boundaries, transpose coordinates, or fail to vendor the solver. A strong model should derive the
right-hand side and boundary terms, test residuals, and leave a clear visual comparison.

**Human inspection.** Look for seams and color discontinuities at the mask boundary. Compare the
candidate report's equations with the exact stencil. A polished editor is valuable, but the compact
hidden Poisson solve is the quantitative result.

## 2. Progressive compact multi-pole control

**Paper/capsule:** `dm-control-suite/multipole-control@1.0.0`

**Scientific idea.** Coupled unstable dynamics become harder as pole count and parameter variation
increase. The capsule tests online feedback, state handling, persistent-process engineering, and
robustness to hidden dynamics.

**Fidelity boundary.** The scorer uses a supplied deterministic cart/multi-pole kernel. It does not
start official MuJoCo or mechanically verify an RL training run. Experiments in dm_control can still
inform the controller and improve the educational artifact.

**What it must build.** `submission/agent.sh` is a persistent JSONL process. After `reset`, each
observation supplies cart position/velocity and arrays of pole angles/angular velocities. The agent
returns one bounded scalar force before the deadline. Any weights must be sealed inside
`submission/`.

**What is actually scored.** Hidden cases change pole count, lengths, initial angles, wind, and
difficulty. Quality combines fraction of the horizon survived with an exponential pole-angle RMS
penalty. The first action has a ten-second warm-up allowance; later actions have 0.25 seconds.
Protocol errors or timeouts fail qualification.

**Why models may differ.** The task rewards quickly reading the dynamics, designing or searching
feedback gains, handling variable state dimension, maintaining JSONL state correctly, and validating
the controller rather than merely writing generic RL scaffolding.

**Human inspection.** Watch cart and pole trajectories, especially the first failure. Check whether
high score means genuine upright survival rather than a brief low-angle prefix. Read how the report
distinguishes the compact proxy from dm_control.

## 3. Procedural rendering reconstruction

**Paper/capsule:** `multiple-importance-sampling/progressive-path-tracer@1.0.0`

**Scientific idea.** The motivating topic is correct, efficient image synthesis and the way sampling
strategies affect variance. The compact v1 task principally tests whether the agent can understand a
procedural scene, produce the correct image, package rendering software, and diagnose image error.

**Fidelity boundary.** V1 does not mechanically establish that the candidate implemented path
transport or MIS. A C++/CMake progressive path tracer with an MIS analysis is an excellent
educational extension, but the leaderboard must be described as procedural image reconstruction.

**What it must build.** `submission/render.sh SCENE.json OUTPUT.json METRICS.json` writes a linear-RGB
`image` array and a metrics JSON file. Reproduction should emit a preview and explain any larger
renderer in `REPORT.md`.

**What is actually scored.** Three hidden sphere/light scenes are compared with a deterministic
reference using image MSE. Runtime is retained for inspection. Wrong dimensions, non-finite values,
missing output, command failure, or timeout fail closed.

**Why models may differ.** This is intentionally closer to the floor of the suite: it tests contract
reading, code reuse, image-array correctness, deterministic rendering, and packaging. An agent that
blindly builds a large renderer without noticing the exact v1 schema may do worse than one that
first satisfies the compact contract and then adds the larger artifact.

**Human inspection.** Compare object silhouettes, colors, shading, and light placement. Treat any MIS
claim as qualitative unless the submission provides its own convincing ablation; the v1 verifier
does not certify that claim.

## 4. Compact material trajectory reproduction

**Paper/capsule:** `mls-mpm/multimaterial-simulator@1.0.0`

**Scientific idea.** MLS-MPM motivates particle/grid simulation, stable integration, and
material-dependent dynamics. V1 extracts a deterministic trajectory-conformance problem that is
quick to execute and easy to animate.

**Fidelity boundary.** The local kernel is not a complete MLS-MPM transfer/stress implementation.
The task does not justify claims about full constitutive fidelity. Its scored artifact is an exact
particle trajectory conditioned on the case's material label.

**What it must build.** `submission/simulate.sh SCENE.json OUTPUT_DIR` writes
`result.json` containing every particle position at every requested step. Particle identity and
array shape must remain stable. A C++/OpenGL viewer is encouraged but not required to qualify.

**What is actually scored.** The evaluator recomputes the trusted jelly-, snow-, or water-like
trajectory and measures full-state RMSE. Hidden cases vary initial positions, material, and
difficulty. Missing frames, particle-count changes, non-finite state, or execution failure score
zero.

**Why models may differ.** Success depends on identifying the material-conditioned update,
reproducing integration and collision details exactly, understanding the entire trajectory schema,
and packaging a portable command. It can reveal whether an agent verifies numerical state rather
than trusting a plausible-looking animation.

**Human inspection.** Animate the raw trajectory, looking for explosions, disappearing particles,
floor penetration, or final-frame-only fakery. Do not describe a high score as full MLS-MPM unless
the candidate independently built and validated that extension.

## 5. Compact world-model-style landing control

**Paper/capsule:** `differentiable-world-model-mpc/visual-offline-control@1.0.0`

**Scientific idea.** The motivating question is whether planning or adaptation in a learned model
produces actions that work under real dynamics mismatch. V1 keeps the crucial realized-control
check while making the environment a small 2D point mass.

**Fidelity boundary.** No learned world model, offline dataset, or differentiable optimizer is
mechanically required. The method is open: analytic feedback, shooting, MPC, search, or learned
control can all compete. Ranking reflects realized trusted dynamics only.

**What it must build.** A persistent `submission/agent.sh` receives state, target, and step over
JSONL and returns a two-dimensional bounded action. It has the same warm-up and per-step deadlines
as multi-pole control.

**What is actually scored.** Hidden cases vary initial state, target, wind, drag, and difficulty.
Quality exponentially penalizes final target distance and mean squared action. Invalid action shape,
non-finite output, process exit, or timeout fails qualification.

**Why models may differ.** The task probes protocol reliability, rapid dynamics analysis, planning
horizon judgment, action saturation, and the ability to improve a decent public feedback baseline.
It is one of the more open continuous-optimization arenas.

**Human inspection.** Watch the full path to the target and representative overshoots or crashes.
Compare final distance with action effort. Check whether the report calls a hand-designed controller
a “world model” without evidence.

## 6. Constrained structural load-path design

**Paper/capsule:** `topology-optimization/robust-structure-design@1.0.0`

**Scientific idea.** Topology optimization allocates limited material spatially so loads reach
supports efficiently. V1 makes that intuition directly visible through a compact density grid.

**Fidelity boundary.** The scorer does not assemble a finite-element stiffness matrix or measure
compliance/stress. It measures connected material, alignment with trusted load paths, and volume.
SIMP/FEA implementations can be educational extensions but are not certified by the v1 score.

**What it must build.** `submission/optimize.sh CASE.json OUTPUT_DIR` writes `result.json` with an
`HxW` density grid matching the case dimensions. Loads, the supported boundary, and volume limit are
part of the public schema.

**What is actually scored.** The trusted evaluator labels connected components, checks whether a
component links the left support to load cells, measures alignment with a useful path, and penalizes
volume above the limit. Hidden cases change grid dimensions and load configurations.

**Why models may differ.** The task invites constructive geometry, numerical optimization, graph
reasoning, continuation, and local search. It is hard to maximize perfectly while remaining easy to
see when a structure is disconnected or wastes material.

**Human inspection.** Look for complete support-to-load paths, excessive gray material,
checkerboards, isolated islands, and over-volume designs. Use “load-path proxy” rather than
“compliance optimum” in conclusions unless the candidate separately validates FEA.

## 7. Adversarial Lightcycle tournament

**Paper/capsule:** `lightcycle-agents/adversarial-tournament@1.0.0`

**Scientific idea.** This software/game capsule probes adversarial planning, territory estimation,
simultaneous-action reasoning, opponent interaction, and strict real-time reliability. Its main
value is direct model-versus-model comparison rather than reproduction of one paper result.

**What it must build.** Persistent `submission/bot.sh` consumes reset and turn records and returns
one of `U`, `D`, `L`, or `R` within 0.25 seconds. It may retain match state but must reset correctly.

**What is actually scored.** A fixed opponent field supplies qualification and a pre-tournament
signal. The decisive result is the external round robin: every pair plays deterministic symmetric
maps twice with starting sides exchanged. Standings preserve match points, W/D/L, descriptive
rating, uncertainty, illegal moves, timeouts, and raw replays.

**Why models may differ.** Legal flood-fill play is accessible; deeper search, articulation-point
awareness, opponent modeling, time management, and simultaneous-action traps create headroom.
Because candidates play each other, no fixed reference must be globally optimal.

**Human inspection.** Use the HTML replay slider to watch territory choices, traps, head-on
collisions, and side symmetry. Check uncertainty and error counts before interpreting rating gaps.

## 8. Inverse smoke control

**Paper/capsule:** `stable-fluids/inverse-smoke-control@1.0.0`

**Scientific idea.** Given a fixed differentiable-or-simulatable transport process, choose controls
that make a distributed state resemble a target. This is an auto-research-style optimization task
with an immediately visible outcome.

**Fidelity boundary.** The simulator is a compact 2D density advection/diffusion proxy, not a full
Navier–Stokes solver. Hidden variation currently changes the target geometry and its relationship to
the source through deterministic seeds.

**What it must build.** `submission/control.sh CASE.json OUTPUT.json` returns one bounded 2D control
per step. The visible tools can simulate and render target, achieved density, and overlays.

**What is actually scored.** The trusted simulator rolls out the sequence and measures normalized
correlation between final density and target. Three hidden target cases are geometrically aggregated.
Malformed/non-finite control, failure, or timeout scores zero.

**Why models may differ.** The search landscape is nonconvex but cheap. Agents can use coordinate
search, evolution, finite differences, model-based planning, or exploit structure in the target.
The result reveals experimentation discipline and budget allocation.

**Human inspection.** Compare target and final smoke, checking whether high overlap is broad blur or
correct localization. Inspect the full sequence rather than only the final frame, and distinguish
the compact transport proxy from full fluid control.

## 9. Terrain-conditioned soft-robot co-design proxy

**Paper/capsule:** `evolutionary-soft-robots/morphology-control-codesign@1.0.0`

**Scientific idea.** Morphology and control should be chosen together because body structure changes
which actuation patterns are effective. V1 compresses that idea into connected voxel occupancy and
two oscillator parameters conditioned on terrain statistics.

**Fidelity boundary.** There is no mass-spring or voxel-physics rollout in v1. The objective is an
explicit co-design proxy based on connectivity, horizontal span, lower-body occupancy, budget,
terrain roughness/slope, and oscillator fit.

**What it must build.** `submission/design.sh CASE.json OUTPUT.json` returns an occupancy grid,
`frequency`, and `phase_gradient`. The grid must match case dimensions and obey the voxel budget.

**What is actually scored.** Disconnected or malformed bodies fail. Connected designs receive a
morphology score and a terrain-dependent oscillator score, with over-budget penalties. Hidden cases
change terrain, seed, and difficulty, so one fixed oscillator is no longer identical across cases.

**Why models may differ.** The task is fast enough for enumeration or evolutionary search yet has a
mixed discrete/continuous space. It probes whether an agent reads the metric, designs an efficient
search, validates hidden-style terrains, and reports the proxy honestly.

**Human inspection.** View occupancy, body span, budget use, and parameter sensitivity plots. Do not
interpret the rendered body as demonstrated locomotion; a candidate wishing to make that claim must
provide a separate physical simulator and evidence.

## 10. Procedural inverse rendering

**Paper/capsule:** `inverse-rendering/procedural-scene-recovery@1.0.0`

**Scientific idea.** Infer a compact scene description that explains several rendered observations
and generalizes to cameras whose images were not used for fitting. This tests optimization,
representation, ambiguity handling, and visual validation.

**Fidelity boundary.** Scenes contain colored circular primitives with normalized position, radius,
and RGB values. V1 does not recover general meshes, BRDFs, lighting, or unknown camera calibration.

**What it must build.** `submission/recover.sh CASE.json OUTPUT_DIR` writes `result.json` with an
`objects` list. Each object is `[x, y, radius, red, green, blue]`. Input contains low-resolution
observations and observed camera offsets; ground-truth objects are removed.

**What is actually scored.** The trusted renderer evaluates both observed-view fit and three
held-out camera views rendered from hidden truth, with a small primitive-count penalty. Hidden cases
change count, geometry, colors, and views. Invalid primitives, non-finite state, failure, or timeout
score zero.

**Why models may differ.** This is a genuine continuous, variable-cardinality inverse problem.
Agents may use image analysis, optimization, differentiable approximations, matching, or stochastic
search. Local minima and primitive correspondence create useful ceiling behavior.

**Human inspection.** Compare observed views, held-out views, and a camera orbit. Look for one-view
billboards, duplicated primitives, color/geometry tradeoffs, and complexity inflation. The held-out
evidence is the most important visual cross-check.

## Interpreting the suite as a whole

The suite intentionally mixes low-floor contract/software tasks, medium optimization tasks, and
open adversarial or inverse problems. Exact difficulty labels remain hypotheses until real candidate
agents run. The first model fleet should therefore be treated as empirical capability-frontier
calibration as well as the first comparison.

When presenting results, report each capsule's exact v1 name and fidelity. A candidate can be
quantitatively excellent on the compact proxy while producing a weak full-paper explanation, or it
can build an impressive educational extension that is imperfect on hidden cases. Those are distinct
and interesting findings; preserve both rather than forcing them into one number.
