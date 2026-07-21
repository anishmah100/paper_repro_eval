# Human guide to paper_repro_eval

This document explains what the repository is, how its parts fit together, what happens during an
evaluation, and what a human operator should inspect. For a concise command-by-command runbook, use
[Running the visual research evaluation](RUNNING_AGENTS.md). For scientific descriptions of the ten
current tasks, use the [task catalog](TASK_CATALOG.md).

## What the framework is trying to measure

The unit of evaluation is a complete native coding-assistant system, not an isolated language-model
answer. A candidate may search the web, read papers, find public implementations, install packages,
write code, run experiments, and debug normally. That reflects the intended use: “Can this system
turn a research specification into a correct, inspectable artifact?”

The framework has two simultaneous outputs:

1. a comparative result showing which candidates qualified and how they scored;
2. a durable reproduction that a human can run, watch, inspect, and learn from.

The sole comparison-specific prohibition is cross-candidate information flow. A candidate may not
read another candidate's workspace, result, score, or review. Public information remains allowed.

## Mental model

The repository hierarchy separates shared scientific context from bounded tasks and isolated
candidate attempts:

```text
paper_repro_eval/
├── papers/
│   └── PAPER/
│       ├── paper.yaml                 paper identity and capsule index
│       ├── materials/                 shared paper-level reading material
│       ├── resources/                 shared public assets
│       └── capsules/
│           └── CAPSULE/VERSION/
│               ├── capsule.yaml       fidelity, submission, and competition contract
│               ├── public/            task, visible cases, and starter code
│               └── private/           verifier, hidden cases, reference, mutants, review guide
├── suites/                             explicit lists of capsule versions to compare
├── templates/                          copied agent instructions and public arena tools
├── runs/                               isolated per-agent attempts; ignored by outer Git
├── reports/                            leaderboards, galleries, launch sheets, tournaments
├── learning/                           explicitly curated review packets
├── src/paper_repro_eval/               lifecycle and reporting implementation
└── docs/                               operator, authoring, and interpretation guides
```

A paper is the parent scientific object. A capsule is one bounded, verifiable claim or engineering
artifact associated with that paper. One paper may eventually have several capsules. A suite pins
specific capsule versions so every candidate receives the same evaluation.

## Public and private halves of a capsule

The public half is copied into candidate workspaces. It contains:

- `TASK.md`: the scientific assignment and broader educational goals;
- `EXECUTABLE_CONTRACT.md`: the authoritative scored process interface and fidelity boundary;
- `resources/`: visible cases and fixtures;
- `starter/`: optional starter scripts, build shells, or baseline code.

Paper-level `materials/` and `resources/` are copied as `paper/` and `paper_resources/`. The generic
`arena_kit/` provides visible case generation, scoring, and rendering utilities. Workspace-level
`WORK_PLAN.md`, `AGENTS.md`, and `CLAUDE.md` state the isolation rule and completion checklist.

The private half never enters a candidate workspace. It contains:

- hidden case definitions or deterministic hidden seeds;
- trusted task-native verifier code;
- a positive reference used to calibrate reachable behavior;
- broken or adversarial mutants used to detect weak scoring contracts;
- a calibration manifest describing expected ordering;
- a human review guide naming task-specific pathologies.

This split lets the candidate understand the complete problem schema without seeing the exact
instances, implementation frontier, or score-side code used for comparison.

## What `prepare` does

`paper_repro_eval prepare SUITE -a AGENT...` resolves the suite and creates one physical workspace
for every capsule/agent pair. It does not use symlinks or shared Git worktrees. For each workspace it:

1. copies only public paper and capsule material;
2. copies the general agent work plan and native assistant instruction files;
3. creates an empty `submission/` directory;
4. computes a digest of the identical public starting tree;
5. initializes a separate Git repository using the operator's global Git identity;
6. records the run ID, agent label, capsule version/digest, attempt number, and workspace path;
7. verifies that candidates for the same capsule received identical starting digests;
8. validates every workspace as pristine and writes a launch sheet.

The generated launch sheet contains the exact workspace, run ID, `enter` command, and one-line
prompt for each assignment. If an expected instruction is absent, private data appears, a symlink is
present, `submission/` is prepopulated, or the initial digest has changed, launch-sheet generation
fails instead of silently handing over a contaminated run.

## What the candidate does

The candidate opens one workspace and follows `WORK_PLAN.md`, the exact `EXECUTABLE_CONTRACT.md`,
and the task-specific scientific goals in `TASK.md`.
Although interfaces differ, the general result always includes:

- a task-native executable script from `EXECUTABLE_CONTRACT.md`, such as `render.sh`, `agent.sh`, or `optimize.sh`;
- a portable self-contained implementation under `submission/`;
- `submission/reproduce.sh`, which writes visible artifacts to `REPRO_OUTPUT_DIR`;
- `submission/REPORT.md`, which explains method, evidence, deviations, and limitations;
- a visual or replayable demonstration when required by the task.

Only `submission/` is sealed. Code left exclusively in `starter/`, temporary directories, or the
workspace root will not be part of the evaluated artifact. This is why the work plan explicitly asks
the candidate to package every runtime asset and dependency declaration beneath `submission/`.

## Lifecycle after the agent finishes

The lifecycle is append-only:

```text
prepared → sealed → reproduced → verified → review-ready
```

### Seal

The framework copies `submission/` into an immutable seal revision, rejects symlinks, records missing
required artifacts, hashes the tree, and captures Git provenance. Re-sealing identical content is
idempotent; changed content creates another immutable revision.

### Reproduce

The sealed `reproduce.sh` runs with a fresh `REPRO_OUTPUT_DIR`. Its logs, exit status, duration, and
artifacts are retained. Reproduction checks whether the candidate can produce its own visible claim;
it does not decide scientific correctness.

### Verify

The private verifier invokes the sealed task-native interface on deterministic hidden cases. It
recomputes metrics with trusted dynamics or numerical routines wherever practical. Malformed,
missing, non-finite, illegal, or timed-out output fails closed rather than receiving a favorable
default. Verification stores objective and diagnostic checks, raw measurements, and evaluator-made
visual evidence.

### Review

The review packet combines the immutable candidate report, reproduction artifacts, private evidence,
objective check table, general review norms, capsule-specific review guide, and an empty `NOTES.md`.
The human writes qualitative conclusions there. Qualitative judgment remains prose; it is not hidden
inside an uninspectable model-judge number.

## How quantitative comparison works

Every competitive capsule declares:

- qualification checks that must pass before a result can win;
- a primary metric and direction;
- a tie tolerance;
- a plain-language winner rule.

Independent-score tasks receive a normalized objective score in `[0, 1]`, while preserving raw
task-specific measurements. Normalization aids display but does not make scores from unrelated tasks
scientifically interchangeable. Use per-task rankings and raw metrics before considering any broad
summary across the suite.

The Lightcycle capsule additionally runs a direct round robin. Each pair sees the same deterministic
maps with starting sides exchanged. Standings include match points, wins/draws/losses, a descriptive
rating, score-rate uncertainty, protocol errors, timeouts, and replay files.

## How visual comparison works

`paper_repro_eval gallery` chooses the latest verified attempt for each requested agent/capsule and
builds a self-contained HTML gallery. The important distinction is evidence provenance:

- candidate artifacts show what the model chose to demonstrate;
- evaluator artifacts show canonical visible and hidden conditions;
- raw state allows targeted rerendering or numerical spot checks.

Review evaluator evidence first, then numeric overlays, then the candidate demo, and finally targeted
source code. This reduces anchoring on attractive cherry-picked outputs. The detailed task catalog
lists what to look for in each arena.

## Attempts, conditions, and fairness

Preparing the same suite with the same agent label again creates a new numbered attempt. Earlier
attempts remain intact. Reports use the latest attempt per label and capsule. Use different labels
for meaningfully different conditions, such as `model-autonomous` and `model-interactive`, if both
should remain visible at once.

The framework deliberately does not enforce an exact one-hour timer or score operator interaction.
Those are qualitative aspects of actual use. Apply comparable expectations, preserve the autonomous
first attempt before collaborating, and describe meaningful intervention differences in your report.

Directory isolation is strong against accidental mixing but is not an adversarial operating-system
sandbox. The root work plan tells agents not to inspect parent/sibling evaluation directories. For
strict enforcement, prepare with container isolation and mount only the selected workspace; normal
network access may remain enabled.

## Reading the output directories

Within an attempt directory:

```text
attempt-NNN/
├── run.json                 stable run metadata and state
├── workspace/               candidate's independent Git repository
├── seals/revision-NNN/      immutable submitted content and seal record
├── reproductions/           clean runs, logs, and visible artifacts
├── verifications/           private results, checks, raw metrics, evidence
└── review/                  human-readable review packets and notes
```

Suite reports contain JSON/CSV for analysis, Markdown/HTML for reading, and leaderboards. Galleries
copy review packets into a side-by-side visual surface. Tournament directories contain standings and
one JSON/HTML replay pair per match. These operational outputs are ignored by outer Git because they
may contain prompts, generated code, absolute paths, or private reviewer notes.

## A practical human workflow

Before access to candidate agents:

1. install the development and arena dependencies;
2. validate all manifests and run the repository tests;
3. read this guide, the task catalog, and the operating runbook;
4. choose stable, non-sensitive labels for model/condition combinations;
5. decide which models will receive autonomous versus interactive attempts.

When access arrives:

1. run `paper_repro_eval` with no arguments;
2. choose model and task numbers when prompted, then launch the assistant in the shell that opens;
3. use the one-line prompt printed by the command;
4. exit the workspace shell and accept the evaluation prompt;
5. rerun the same bare command to resume or choose another task;
6. preserve the candidate's first complete attempt before offering help;
7. build the report, filtered gallery, and Lightcycle tournament;
8. write qualitative notes using hidden evidence and the capsule guide;
9. curate reproductions that are genuinely useful for learning.

The lower-level `prepare`, `status`, `enter`, and `evaluate` commands remain available for
batch automation and auditing. Ordinary interactive use does not require run IDs.

## Troubleshooting

If `prepare` fails, run capsule and suite validation and confirm `templates/workspace/` and
`templates/arena_kit/` exist. If launch-sheet generation rejects a workspace, do not repair it
silently; prepare a fresh attempt or inspect the reported contamination.

If reproduction fails but verification can still run, retain both outcomes: packaging and visible
reproducibility are themselves useful model capabilities. If verification returns evaluator error,
distinguish a harness failure from a scientifically wrong candidate and fix the harness before
ranking. If a visual looks excellent but metrics fail, inspect raw state and task invariants. If a
score looks excellent but the visual is implausible, look for proxy exploitation, invalid state, or
a missing transfer argument.

## Extending the repository

Use the authoring workflow described in [Capsule design](CAPSULES.md) and the
[competition contract](COMPETITIONS.md). New capsules begin as drafts and are promoted only after
task-native execution, hidden cases, a deterministic positive reference, meaningful failing mutants,
repeatability, fail-closed behavior, and human review evidence are complete. Large cloud runs can use
the same contracts because verifiers and candidate commands are filesystem/process interfaces rather
than assumptions about a particular local machine.
