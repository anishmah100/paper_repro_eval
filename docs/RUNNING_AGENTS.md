# Running the visual research evaluation

This guide is the operator playbook for comparing native coding assistants on the ten
`visual-research-arcade-v0` capsules. It preserves the intended open-world evaluation: launch the
ordinary assistant in its assigned directory, allow its normal tools and internet access, and judge
the complete result. The only forbidden information flow is one candidate seeing another
candidate's workspace, submission, artifacts, scores, or review.

The framework does not enforce a one-hour cutoff or score operator interaction. Those are
deliberately qualitative parts of the study. Use the same broad expectations for every model and
record surprising interaction costs in your notes.

## 1. Install and validate once

Run commands from the repository root:

```bash
uv sync --extra dev --extra arena
uv run paper_repro_eval capsules validate
uv run paper_repro_eval suites validate visual-research-arcade-v0
uv run pytest -q
```

The `arena` extra supplies the compact numerical and rendering dependencies used by the trusted
verifiers. Candidate assistants remain free to choose other dependencies inside their own
workspaces.

## 2. Choose public, stable agent labels

Labels become directory names and appear in reports. Use labels such as `grok-4.5-run1`,
`fable-run1`, `gpt-5.6-run1`, `claude-opus-run1`, and `gpt-older-run1`. Do not put account names,
API keys, machine names, or private notes in a label.

Prepare every capsule for every candidate in one operation:

```bash
uv run paper_repro_eval prepare visual-research-arcade-v0 \
  -a grok-4.5-run1 \
  -a fable-run1 \
  -a gpt-5.6-run1 \
  -a claude-opus-run1 \
  -a gpt-older-run1
```

This creates 50 physical workspaces: ten capsules times five candidates. Every workspace is a
separate Git repository initialized from the same public tree. Paper material and capsule-specific
task data are copied automatically. Private cases, verifiers, references, calibration mutants, and
other candidates' outputs are not copied.

`prepare` also prints a generated launch-sheet path containing the exact run IDs, workspaces, enter
commands, and one-line prompt. Save it. Run IDs can also be recovered with:

```bash
uv run paper_repro_eval status
uv run paper_repro_eval path RUN_ID
```

If needed, regenerate a pristine handoff sheet for selected labels:

```bash
uv run paper_repro_eval launch-sheet visual-research-arcade-v0 \
  -a grok-4.5-run1 -a fable-run1 -a gpt-5.6-run1
```

Regeneration deliberately fails if a latest workspace has already changed or contains a prefilled
submission; prepare a fresh attempt rather than presenting a modified workspace as pristine.

The directory hierarchy is:

```text
runs/visual-research-arcade-v0/
  papers/PAPER/capsules/CAPSULE/agents/AGENT/attempt-NNN/workspace/
```

`runs/`, `reports/`, and `learning/` are ignored by the outer repository, so experimental outputs
are not accidentally published.

## 3. Launch a native assistant in exactly one workspace

For a selected run:

```bash
uv run paper_repro_eval enter RUN_ID
```

That opens a shell at the isolated workspace. Alternatively, use `paper_repro_eval path RUN_ID`,
change into that path, and launch the normal assistant command, for example `codex` or `claude`.

A sufficient initial prompt is:

> Read WORK_PLAN.md, EXECUTABLE_CONTRACT.md, and TASK.md, then complete the task autonomously.

Do not give the model hidden verifier details, another model's result, or advice derived from a
previous candidate. Otherwise, let it work normally. Searching online, finding an existing
implementation, installing packages, writing its own tests, and using any native agent feature are
all legitimate capabilities in this evaluation.

The assistant should read `WORK_PLAN.md`, `EXECUTABLE_CONTRACT.md`, `TASK.md`, `paper/`,
`paper_resources/`, `resources/`, `starter/`, and `arena_kit/`. It should place its final portable artifact in `submission/`. Every task requires
`submission/reproduce.sh` and `submission/REPORT.md`, plus the task-native entrypoint named in
`EXECUTABLE_CONTRACT.md`. A demo is required where the task says so and strongly preferred everywhere.

If the model asks a genuine product-use question, answer naturally. If it asks for another model's
output, decline. Do not silently fix its code before evaluation. If you want to collaborate after
the first result, preserve the first attempt and prepare a new attempt so autonomous and assisted
results remain distinguishable.

## 4. Evaluate an attempt

When the assistant declares completion, return to the framework root and run:

```bash
uv run paper_repro_eval evaluate RUN_ID --timeout 300
```

`evaluate` performs four linked steps:

1. seals `submission/` into an immutable revision with a digest;
2. runs `reproduce.sh` in a clean output directory;
3. invokes the private task-native verifier on hidden cases;
4. creates a human review packet.

A scientifically wrong result is a normal recorded result. Exit code 2 is reserved for an
evaluator failure, not a weak candidate. You can inspect stages independently with `seal`,
`reproduce`, `verify`, and `review`.

Do not edit an already sealed result to make it look better. Preparing the same suite again with
the same agent label creates `attempt-002`; earlier attempts and seals remain intact. The suite
leaderboard uses the latest attempt for each agent and capsule, so use distinct labels if you want
autonomous and interactive conditions shown simultaneously.

## 5. Produce quantitative comparisons

After evaluating the desired runs:

```bash
uv run paper_repro_eval report visual-research-arcade-v0
```

The command writes machine-readable JSON/CSV, a Markdown audit table, an HTML report, and
`LEADERBOARD.md` under `reports/visual-research-arcade-v0/`. Rankings use only qualifying results,
the capsule's declared primary metric, tie tolerance, and winner rule. Raw component measurements
remain in each verification record; the normalized objective score should not replace them in the
final analysis.

Lightcycle also supports direct model-versus-model play:

```bash
uv run paper_repro_eval tournament visual-research-arcade-v0 \
  -a grok-4.5-run1 -a fable-run1 -a gpt-5.6-run1 \
  -a claude-opus-run1 -a gpt-older-run1 \
  --seeds 8 --turn-timeout 0.25
```

Each pair plays every deterministic map twice with starting sides exchanged. The output includes
points, wins/draws/losses, an Elo-style descriptive rating, a 95% score-rate interval, protocol
errors, timeouts, raw JSON replays, and self-contained HTML replay viewers. Treat the rating as a
summary of this tournament, not a universal skill estimate.

## 6. Build the visual comparison gallery

Generate a gallery containing only the intended candidates:

```bash
uv run paper_repro_eval gallery visual-research-arcade-v0 \
  -a grok-4.5-run1 -a fable-run1 -a gpt-5.6-run1 \
  -a claude-opus-run1 -a gpt-older-run1
```

The printed directory contains `index.html` and a self-contained copy of every latest verified
review packet. Open the HTML file in a browser. The gallery uses evaluator-generated evidence, not
only candidate-selected beauty shots. Click thumbnails at full resolution; then open the linked
packet for metrics, raw artifacts, `CANDIDATE_REPORT.md`, the capsule rubric, and `NOTES.md`.

Inspect visual evidence in this order:

1. evaluator-generated median, failure, or hidden-case evidence;
2. the numeric overlays and raw component metrics;
3. the candidate's visible reproduction and demo;
4. the candidate report and only then targeted source code.

This order prevents a polished demo from anchoring the review before hidden evidence is seen.

## 7. Fast manual trust audit

You should not need to read every line of generated code. For each result, use a compact audit:

- Confirm the required native command built or launched and the qualification check passed.
- Compare the score with the evaluator-generated image or replay. A mismatch is more informative
  than either signal alone.
- Inspect the median case and worst case, not just the best frame.
- Open the raw trajectory, scene, or state file and verify that it is sufficient to rerender.
- Read the method and limitations sections of `CANDIDATE_REPORT.md`; mark claims not supported by
  the packet.
- Search the submission for hard-coded visible-case values, canned outputs, disabled physics,
  score-specific constants, and code paths that bypass the claimed mechanism.
- Spot-check one scientific invariant: a PDE residual, conservation/constraint trace, held-out
  view, robust perturbation, collision rule, or control rollout as appropriate.
- If suspicious, construct one small counterexample or ask a coding assistant to do a focused
  review. Compact counterexamples are more useful than an unfocused line-by-line audit.

Using public code is allowed and should not itself be treated as cheating. The question is whether
the sealed artifact satisfies the task and whether its report accurately explains what it does.

## 8. Arena-specific visual questions

| Arena | Look for first | Quantitative cross-check |
|---|---|---|
| Poisson editing | seams, color bleeding, mask-boundary halos | interior guidance error and boundary residual |
| Multi-pole control | stable compact trajectories across pole counts | survival and angle RMS |
| Rendering proxy | silhouettes, colors, shading, and light placement | hidden-scene image MSE |
| Material trajectory proxy | stable particle identity and plausible motion | full-trajectory RMSE |
| Landing-control proxy | path, overshoot, and target arrival | terminal distance, effort, protocol errors |
| Structural-layout proxy | connected support-to-load paths without islands | connectivity, alignment, volume |
| Lightcycle | spatial planning, traps, side symmetry, legal timely moves | paired points, interval, errors/timeouts |
| Inverse-smoke proxy | coherent transport into the target rather than broad blur | final target overlap |
| Soft-robot co-design proxy | connected morphology, span, and parameter sensitivity | terrain-conditioned proxy quality |
| Inverse rendering | multi-view agreement rather than one matched camera | held-out-view error and parameter recovery |

## 9. Qualitative and educational notes

Write prose in each packet's `NOTES.md`. Do not collapse the human review into an opaque LLM-judge
number. A useful note records:

- first visual impression before reading the report;
- what scientific mechanism appears to have been reproduced;
- strongest evidence and most revealing failure;
- whether the score matches the visible behavior;
- originality, simplicity, and engineering quality of the approach;
- what you learned about the paper from the artifact;
- unsupported claims, caveats, and confidence in the result;
- what using the assistant felt like: autonomy, judgment, debugging ability, and interaction cost.

For a second opinion, open a separate coding assistant on one review packet—not on another
candidate workspace—and ask it to follow `REVIEWING.md` and `CAPSULE_REVIEW_GUIDE.md`, identify the
smallest decisive counterexample, and return prose with file/metric evidence. You remain the final
reviewer and should record disagreements rather than averaging them into a score.

For the final report, combine three layers: the qualification/leaderboard table, a few decisive
side-by-side visuals or replays, and your qualitative account of why the models diverged. Highlight
capability patterns across tasks rather than declaring a universal winner from ten small samples.

## 10. Preserve valuable reproductions

After review, copy a useful packet into the long-term educational tree:

```bash
uv run paper_repro_eval curate RUN_ID
```

Curate results because they teach something—even a clean failure can be valuable. The original run
and verification remain the audit source; the curated copy is a reading and exploration artifact.

## 11. Publication and privacy check

Experimental runs and reports may contain model prompts, generated code, usernames embedded by a
tool, or other local details. They are ignored by default. Before publishing framework changes,
review `git status`, scan staged files for secrets and personal information, and inspect the staged
diff. Never force-add `runs/`, `reports/`, or `learning/` without a deliberate separate review.
