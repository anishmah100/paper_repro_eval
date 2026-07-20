# Executable starter

The evaluated task-native entry point is `render.sh SCENE.json OUTPUT.json METRICS.json`. It produces linear-RGB image JSON and metrics. The starter is a
deliberately weak but runnable implementation; improve or replace the research method while keeping
the documented protocol stable.

The prepared workspace also contains `arena_kit/arena_kit.py`, the visible fixture under
`resources/`, paper material, and an empty `submission/`. You may copy, vendor, or rewrite starter
code. The final `submission/` must be self-contained because sealing copies only that directory.

Before sealing, create:

- the task-native entry point and all code or weights it needs;
- `reproduce.sh`, which writes `result.json`, `metrics.json`, and `preview.png` beneath
  `$REPRO_OUTPUT_DIR`;
- `REPORT.md`, explaining the method, validation, deviations, failures, and what the visual
  evidence demonstrates;
- `demo.sh` when the task requests an interactive or replayable demonstration.

Use the visible fixture repeatedly while developing. Hidden evaluation changes seeds, geometry, and
nuisance parameters represented by the same schema. Do not hard-code the visible answer.
