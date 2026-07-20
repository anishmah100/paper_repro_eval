# Exact executable contract: compact multi-pole control proxy

This v1 capsule uses a deterministic, coupled cart/multi-pole dynamics kernel supplied in
`arena_kit.py`. It is paper-inspired and visually analogous to dm_control; it does not launch the
official MuJoCo environment during scoring.

The harness starts `bash agent.sh` once per hidden case. Standard input is JSON Lines. First comes a
`reset` record containing `task: "multipole"` and the case. Each subsequent `observation` contains
`x`, `velocity`, `angles`, `angular_velocities`, and `step`. Reply with one flushed JSON line
`{"action": SCALAR}`. Actions are clipped to `[-10,10]`. The first response may take up to ten
seconds for initialization; later responses have a 0.25-second deadline.

The trusted simulator scores survival multiplied by an exponential penalty on pole-angle RMS.
Hidden cases vary pole count, lengths, initial angles, wind, and difficulty. Protocol errors,
non-finite output, process exit, or any missed deadline score zero. Training, MuJoCo experiments,
and richer viewers are allowed educational extensions but must not be required by the sealed agent.
