# CLI reference

The installed command is paper_repro_eval.

- papers list/show/validate inspects paper manifests and shared material.
- capsules list/show/validate addresses a capsule through paper ID, capsule ID, and version.
- suites list/show/validate inspects suites.
- prepare SUITE -a AGENT [-a AGENT...] makes isolated physical workspaces.
- path RUN_ID, enter RUN_ID, and status [RUN_ID] support native-assistant work.
- runs list lists every attempt.
- seal, reproduce, and verify expose lifecycle stages.
- evaluate RUN_ID performs all three stages and creates a review packet.
- review RUN_ID, report SUITE, and curate RUN_ID create human-facing artifacts.
- gallery SUITE [-a AGENT...] creates a filtered, self-contained visual comparison of the latest
  verified attempts.
- tournament SUITE [-a AGENT...] [--seeds N] runs the paired-side Lightcycle round robin and emits
  standings, raw replays, and self-contained HTML viewers.
- author paper-init creates the owning paper; author init PAPER CAPSULE begins a capsule.
- author proposals/approve-scope/scaffold/templates/validate/review/publish/revise
  drives gated capsule creation.

PAPER_REPRO_EVAL_ROOT may identify the repository when commands run elsewhere. Exit code 2 from
verification means an evaluator error; a scientifically wrong candidate remains a recorded result.

See [Running the visual research evaluation](RUNNING_AGENTS.md) for the end-to-end command order,
native assistant launch procedure, interpretation rules, and qualitative review workflow.
