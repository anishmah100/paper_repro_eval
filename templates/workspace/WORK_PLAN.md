# Evaluation work plan

You are the sole implementation agent for this isolated research-reproduction workspace. Complete
the task in `TASK.md` as autonomously and rigorously as possible.

## Local evaluation boundary

- Treat this Git repository as the only local project you may inspect.
- Do not browse parent or sibling directories, the outer evaluation repository, private verifiers,
  hidden cases, or any other candidate's workspace, output, score, or review.
- Do not use `..` or unrelated absolute paths to search for evaluation material.
- Normal operating-system tools, runtimes, package managers, caches, temporary directories, and
  public internet resources are allowed. Public papers, documentation, packages, checkpoints, and
  implementations are allowed.
- Do not ask the operator for hidden data or information about another candidate.

These rules protect comparison independence; they are not intended to limit your normal research,
search, coding, installation, or debugging capabilities.

## Source of truth

Read these before implementing:

1. `TASK.md` — scientific objective, paper connection, and desired educational artifact;
2. `EXECUTABLE_CONTRACT.md` — exact scored process protocol, data schema, and v1 fidelity boundary;
3. `paper/` and `paper_resources/` — paper-level context;
4. `resources/` — visible cases and task assets;
5. `starter/` and `arena_kit/` — optional starting code and visible scoring/rendering tools.

`EXECUTABLE_CONTRACT.md` controls executable details if broader aspirations in `TASK.md` differ from
the compact v1 score. `TASK.md` controls the scientific and educational goals. This file controls
the workspace boundary and general completion procedure.

Complete and test the executable contract first. Treat broader paper-oriented capabilities as
optional extensions unless the contract explicitly makes them required; they must never displace a
working, portable scored submission.

## Required work

1. Understand the claimed mechanism and the quantitative/visual evaluation contract.
2. Design an approach that generalizes beyond the visible examples.
3. Implement the task-native entrypoint required by `EXECUTABLE_CONTRACT.md`.
4. Create `submission/reproduce.sh`, honoring `REPRO_OUTPUT_DIR`.
5. Create `submission/REPORT.md` explaining the method, evidence, deviations, and limitations.
6. Create the required demo or visual artifact described by `TASK.md`.
7. Test on visible and self-created edge cases, including malformed or degenerate inputs where
   relevant.
8. Leave the final portable implementation and every required runtime asset under `submission/`.

Only `submission/` is sealed for evaluation. Do not rely on modified files elsewhere in this
workspace, undeclared local services, or outputs that are not copied into `submission/`.

## Definition of done

Before stopping, verify all of the following:

- the task-native command runs from inside `submission/` using the interface in `EXECUTABLE_CONTRACT.md`;
- `submission/reproduce.sh` exits successfully and produces inspectable evidence;
- outputs are deterministic for fixed seeds unless the task explicitly says otherwise;
- outputs are finite, machine-readable, and satisfy documented bounds or invariants;
- the visual result can be opened or replayed by the operator;
- `submission/REPORT.md` distinguishes measured results from interpretation;
- dependencies and build steps needed by the evaluator are documented and available;
- no required implementation or asset exists only outside `submission/`;
- `git status` and the final file tree contain no credentials or unrelated personal data.

When finished, tell the operator what you built, what you tested, where the main visual artifact is,
and the most important remaining limitation. Do not claim hidden-evaluation success.
