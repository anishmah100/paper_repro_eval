# Operator workflow

Inspect paper-level information with papers show PAPER_ID and its capsules with
capsules list PAPER_ID. Suites use explicit paper/capsule/version references.

Validate and prepare a suite:

    paper_repro_eval suites validate synthetic-smoke
    paper_repro_eval prepare synthetic-smoke -a grok-4.5 -a gpt-5.6

Each row prints a run ID and workspace. Open the corresponding coding assistant in only that
workspace and say, for example: “Do the assigned task.” The task itself explains required outputs:
submission/reproduce.sh, submission/REPORT.md, and any capsule-specific source or demo.

Attempts live beneath runs/SUITE/papers/PAPER/capsules/CAPSULE/agents/AGENT. Each workspace receives
shared paper material plus only that capsule's public task data.

When the assistant finishes:

    paper_repro_eval evaluate RUN_ID
    paper_repro_eval review RUN_ID
    paper_repro_eval report synthetic-smoke

Read SUMMARY.md, the candidate report, artifacts, evidence, review guide, and source. Write your
own conclusions in NOTES.md. curate RUN_ID copies the packet into the long-term learning tree.

Runs and lifecycle revisions are append-only. Preparing again creates a new attempt. Sealing an
unchanged submission is idempotent; a changed one creates another immutable revision.

## Competitive suites

Competitive capsule manifests declare qualification checks, a primary metric, tie tolerance,
tiebreakers, and winner semantics. `paper_repro_eval report SUITE` writes both the complete audit
table and `LEADERBOARD.md`. The leaderboard uses the latest attempt for each agent and ranks only
runs that passed every declared qualification check.

Draft suites may be materialized for development and pilot calibration, but their scores are not
benchmark claims. Before promotion, finish the private build plan, passing reference, mutants,
hidden cases, repeatability study, and human packet review described in
[the competition contract](COMPETITIONS.md).
