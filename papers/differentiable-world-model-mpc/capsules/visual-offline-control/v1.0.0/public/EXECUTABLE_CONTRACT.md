# Exact executable contract: compact robust landing control proxy

This v1 capsule evaluates inference-time control in a deterministic 2D point-mass landing/docking
kernel with hidden dynamics changes. It is a proxy for world-model MPC: no particular learned model,
offline-training procedure, or differentiable planner is mechanically required.

The harness starts `bash agent.sh` once per case. Standard input is JSON Lines. A `reset` record
contains `task: "world_mpc"` and the case. Each `observation` contains four-dimensional `state`,
two-dimensional `target`, and `step`. Reply with one flushed line `{"action": [AX, AY]}`. Components
are clipped to `[-1,1]`. The first response may take ten seconds; later responses have a 0.25-second
deadline.

The trusted simulator scores final target distance and mean action energy. Hidden cases vary initial
state, target, wind, drag, and difficulty. Invalid shapes, non-finite values, process failure, or a
missed deadline score zero. Learned models and MPC are encouraged when they improve the result and
the report, but ranking depends on realized actions in the trusted kernel.
