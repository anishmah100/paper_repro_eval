# Competitive Multi-Material MLS-MPM Simulator

Build an interactive C++/OpenGL MLS-MPM simulator. Reproduce the paper's particle/grid transfers
and stress update, then push the implementation across elastic, fluid-like, plastic, granular, and
rigid-coupled scenes. The official paper and public 88-line implementation may be used.

## Competition

The verifier runs canonical and hidden scenes with fixed initial particle states. It measures mass
and finite-state validity, transfer consistency, momentum behavior in isolated cases, penetration,
center-of-mass and shape trajectories, constitutive response, and throughput. The score rewards the
hardest material levels only after core transfer checks qualify.

## Candidate interface

Provide `submission/simulate.sh SCENE.json OUTPUT_DIR`. Write a deterministic replay containing
particle positions and required state samples, metrics.json, and rendered frames or a render command.
A CMake build and interactive `submission/demo.sh OUTPUT_DIR` are required.

The showcase should include an elastic drop, dam-break or jelly scene, plastic snow/sand impact,
and the hardest implemented interaction. REPORT.md must state the equations, transfer scheme,
constitutive models, timestep/stability choices, collision treatment, validation, and unsupported
paper features.
