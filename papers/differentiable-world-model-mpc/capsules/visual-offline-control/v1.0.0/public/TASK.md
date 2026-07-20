# Visual Offline World-Model Control

Use supplied offline trajectories, a baseline policy, and a differentiable learned model to build a
strong rocket-landing or docking controller. Reproduce the paper's central inference-time adaptation
idea, or beat it with a better justified method. You may use any normal tools or public code.

The true hidden evaluator dynamics differ from the learned model. Winning therefore requires actual
control rather than maximizing an exploitable imagined reward.

## Evaluation

The verifier scores landing or docking success, terminal pose and velocity, collision, fuel, and
return across hidden masses, winds, actuator changes, delays, and initial states. It also measures
the gap between predicted and realized performance. The supplied offline baseline establishes zero
improvement; stronger search, robust MPC, uncertainty handling, or policy refinement can continue
improving the score.

## Candidate interface

Provide a persistent JSON-lines `submission/agent.sh` receiving reset and observation records and
returning bounded thrust commands. Store any trained weights in submission/. Provide train.sh when
applicable and reproduce.sh for visible episodes.

Required visuals show real and imagined trajectories, baseline versus final controller, numeric
overlays, and representative crashes. REPORT.md must distinguish offline data, learned model,
planning objective, validation simulator, and true-evaluation assumptions.
