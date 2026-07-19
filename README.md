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

- public paper-specific task material;
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

See [workflow](docs/WORKFLOW.md), [architecture](docs/ARCHITECTURE.md), and
[CLI reference](docs/CLI.md). The included synthetic suite validates the harness before real paper
capsules are onboarded.

## Development setup

```bash
uv sync --extra dev
uv run paper_repro_eval --help
uv run pytest
```

The installed console command is always `paper_repro_eval`.

