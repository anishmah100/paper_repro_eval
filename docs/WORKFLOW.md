# Operator workflow

Validate and prepare a suite:

    paper_repro_eval suites validate synthetic-smoke
    paper_repro_eval prepare synthetic-smoke -a grok-4.5 -a gpt-5.6

Each row prints a run ID and workspace. Open the corresponding coding assistant in only that
workspace and say, for example: “Do the assigned task.” The task itself explains required outputs:
submission/reproduce.sh, submission/REPORT.md, and any capsule-specific source or demo.

When the assistant finishes:

    paper_repro_eval evaluate RUN_ID
    paper_repro_eval review RUN_ID
    paper_repro_eval report synthetic-smoke

Read SUMMARY.md, the candidate report, artifacts, evidence, review guide, and source. Write your
own conclusions in NOTES.md. curate RUN_ID copies the packet into the long-term learning tree.

Runs and lifecycle revisions are append-only. Preparing again creates a new attempt. Sealing an
unchanged submission is idempotent; a changed one creates another immutable revision.
