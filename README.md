# paper_repro_eval

`paper_repro_eval` is a reusable, filesystem-native framework for evaluating
native coding assistants on verifiable research-paper reproduction capsules.
It is designed for two equally important outcomes:

1. compare complete coding-assistant systems under realistic, open-world use;
2. preserve trustworthy, explorable reproductions as educational artifacts.

Candidate assistants may use normal internet access, public implementations,
documentation, packages, and model checkpoints. The sole fairness boundary is
that a candidate must not see another candidate's local workspace or output.

The framework separates:

- paper-level metadata, source material, and shared resources;
- multiple versioned capsules owned by each paper;
- capsule-specific public tasks and private verifiers;
- isolated per-assistant workspaces;
- immutable sealed submissions;
- clean reproduction;
- private objective verification;
- human-oriented evidence and review packets;
- curated long-term learning artifacts.

## Quick start

```bash
uv sync --extra dev
uv run paper_repro_eval suites validate synthetic-smoke
uv run paper_repro_eval prepare synthetic-smoke -a model-a -a model-b
```

See the [human system guide](docs/HUMAN_GUIDE.md), [task catalog](docs/TASK_CATALOG.md),
[agent-running and review guide](docs/RUNNING_AGENTS.md), [architecture](docs/ARCHITECTURE.md),
and [CLI reference](docs/CLI.md). The included synthetic suite
validates the harness independently of the visual arenas.

## Development setup

```bash
uv sync --extra dev
uv run paper_repro_eval --help
uv run pytest
```

The installed console command is always `paper_repro_eval`.


## Visual Research Arcade

The benchmark-ready first-round catalog contains ten competitive, visually verifiable research
arenas across graphics, control, simulation, games, applied mathematics, and ML. Start with the
[arena index](docs/VISUAL_ARENAS.md), [calibration record](docs/CALIBRATION.md), and
[competition contract](docs/COMPETITIONS.md).

```bash
uv run paper_repro_eval suites validate visual-research-arcade-v0
uv run paper_repro_eval prepare visual-research-arcade-v0 -a model-a -a model-b
```

The capsules have passed local calibration and end-to-end lifecycle smoke tests but have not been
independently audited. Follow the [complete operating procedure](docs/RUNNING_AGENTS.md) before
interpreting or presenting model comparisons.
