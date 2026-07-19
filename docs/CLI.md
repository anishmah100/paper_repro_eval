# CLI reference

The installed command is paper_repro_eval.

- capsules list/show/validate inspects the registry and immutable packs.
- suites list/show/validate inspects suites.
- prepare SUITE -a AGENT [-a AGENT...] makes isolated physical workspaces.
- path RUN_ID, enter RUN_ID, and status [RUN_ID] support native-assistant work.
- runs list lists every attempt.
- seal, reproduce, and verify expose lifecycle stages.
- evaluate RUN_ID performs all three stages and creates a review packet.
- review RUN_ID, report SUITE, and curate RUN_ID create human-facing artifacts.
- author init/proposals/approve-scope/scaffold/templates/validate/review/publish/revise
  drives gated capsule creation.

PAPER_REPRO_EVAL_ROOT may identify the repository when commands run elsewhere. Exit code 2 from
verification means an evaluator error; a scientifically wrong candidate remains a recorded result.
