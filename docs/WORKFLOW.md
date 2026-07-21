# Operator workflow

## Normal interactive use

From the repository root, run:

    uv run paper_repro_eval

This bare command is the human dashboard. On first use it asks for a model/condition label and
prepares the suite. With existing real models, it shows a numbered model menu whose final choice is
`Create a new model / condition`. Choosing that option prepares the new model's full isolated suite
automatically. It then shows the selected model's numbered task menu, including state and attempt,
and opens the chosen workspace. Internal smoke, unit-test, and tournament labels are hidden.

Launch the normal coding assistant in the shell that opens and use the prompt printed by the
dashboard. When the assistant finishes, exit its interface and then exit the workspace shell. The
dashboard offers to seal, reproduce, verify, and create the review packet, then offers to return to
the model/task home screen. Closing a terminal does not lose the workspace.

No model label, task alias, workspace path, or run ID must be remembered for normal use.

Each workspace contains WORK_PLAN.md, EXECUTABLE_CONTRACT.md, AGENTS.md, and CLAUDE.md. The task
explains required outputs: submission/reproduce.sh, submission/REPORT.md, and any capsule-specific
source or demo.

Attempts live beneath runs/SUITE/papers/PAPER/capsules/CAPSULE/agents/AGENT. Each workspace receives
shared paper material plus only that capsule's public task data.

## Advanced batch and audit use

Inspect paper-level information with papers show PAPER_ID and its capsules with capsules list
PAPER_ID. Suites use explicit paper/capsule/version references. For scripted multi-model setup:

    paper_repro_eval suites validate synthetic-smoke
    paper_repro_eval prepare synthetic-smoke -a grok-4.5 -a gpt-5.6

The lower-level path, enter, status, and evaluate commands accept persistent run IDs:

    paper_repro_eval evaluate RUN_ID
    paper_repro_eval review RUN_ID
    paper_repro_eval report synthetic-smoke

Read SUMMARY.md, the candidate report, artifacts, evidence, review guide, and source. Write your
own conclusions in NOTES.md. curate RUN_ID copies the packet into the long-term learning tree.

For the ten visual arenas, follow the detailed [agent-running, visualization, trust-audit, and
qualitative-analysis procedure](RUNNING_AGENTS.md). It includes native Codex/Claude-style launch
instructions, filtered side-by-side galleries, direct Lightcycle tournaments, and an arena-specific
visual checklist.

Runs and lifecycle revisions are append-only. Preparing again creates a new attempt. Sealing an
unchanged submission is idempotent; a changed one creates another immutable revision.

## Competitive suites

Competitive capsule manifests declare qualification checks, a primary metric, tie tolerance,
tie tolerance and winner semantics. `paper_repro_eval report SUITE` writes both the complete audit
table and `LEADERBOARD.md`. The leaderboard uses the latest attempt for each agent and ranks only
runs that passed every declared qualification check.

The visual arcade is benchmark-ready but not independently audited. Its local reference/mutant
evidence is recorded in [the calibration record](CALIBRATION.md). New draft suites may still be
materialized for development, but their scores are not benchmark claims. Before promotion, finish
the private build plan, passing reference, mutants, hidden cases, repeatability study, and human
packet review described in [the competition contract](COMPETITIONS.md).
