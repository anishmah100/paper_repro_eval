# Progressive Multi-Pole Control

> **Read `EXECUTABLE_CONTRACT.md` first.** It defines the exact v1 process protocol, JSON schema,
> scored behavior, and fidelity boundary. The broader paper-oriented goals below describe valuable
> educational extensions; they do not override the compact executable contract.

Build the strongest controller you can for a procedurally generated chain of poles on a cart. The
environment and viewer use the official dm_control MuJoCo model. You may use RL, model-predictive
control, trajectory optimization, system identification, evolutionary search, analytic control, or
any combination. Internet access and public code are allowed. Do not inspect another candidate's
workspace or output.

This is a capability frontier rather than a binary CartPole task. Visible development environments
range from one-pole balance through multi-pole swing-up. Hidden evaluation changes pole count,
lengths, masses, friction, initial state, impulses, observation noise, and action latency.

## Competition

The primary score aggregates standardized return across the ladder, with deliberate weight on the
hardest hidden levels. Secondary measurements include survival time, uprightness, cart excursion,
control energy, recovery after impulses, and the highest level solved reliably. A controller must
execute successfully on ordinary visible levels to qualify.

## Candidate interface

Provide `submission/agent.sh`, a persistent JSON-lines process. It receives a reset record followed
by observation records and must return one bounded scalar action per observation. It may load
checkpoints stored in submission/. It must not open the simulator process or evaluator files.

Provide `submission/train.sh` if training is required. `submission/reproduce.sh` must run or
replay visible evaluation episodes into `REPRO_OUTPUT_DIR`.

## Visual artifacts

Emit deterministic replay data, a montage spanning easy and hardest attempted levels, angle traces,
return overlays, and a failure/recovery reel. Candidate-selected episodes are illustrative only;
the verifier renders canonical visible and hidden episodes from the sealed controller.

In REPORT.md explain the method, training budget, reward or objective, validation distribution,
failure boundary, and any use of existing implementations.

## Executable contract (v1.0.0)

`EXECUTABLE_CONTRACT.md` is authoritative for commands, fields, deadlines, scored measurements,
and what is or is not mechanically verified. Use `resources/visible-case.json`, `starter/`, and
`arena_kit/` for development. The sealed `submission/` must be self-contained. Three deterministic
hidden seeds vary only fields represented by the public schema. The verifier preserves per-case JSON
and PNG evidence, geometrically aggregates quality, and assigns zero to malformed, non-finite,
missing, failed, timed-out, or protocol-invalid results.
