# Executable starter: pathtracer

This directory contains a deliberately weak public baseline. The prepared workspace also contains
`arena_kit/arena_kit.py`: deterministic fixture generation, public dynamics, scoring diagnostics,
and PNG rendering. You may copy or modify it without restriction.

Batch arenas expose `python solve.py INPUT.json OUTPUT.json`. Lightcycle instead exposes a persistent
`python bot.py` process using one JSON request and response per line. The required result schema is:
`image: 32x40x3 linear RGB floats`.

The sealed `submission/` must be self-contained. It must include `reproduce.sh`, `REPORT.md`, the
candidate entry point, and any vendored runtime code. `reproduce.sh` writes `result.json`,
`metrics.json`, and `preview.png` under `$REPRO_OUTPUT_DIR`. Start by running the baseline on
`../resources/visible-case.json`; replace the research method, not the protocol.
