# Capsule design

A capsule is a bounded, verifiable slice of a paper. Categories are tags, not mutually exclusive
classes. Supported shapes include exact mathematics, formal proof, algorithmic properties,
comparative methods, fixed-data analyses, small training runs, interpretability, visual/graphics,
simulation/physics, systems engineering, and ordinary research software conformance.

Describe two independent axes:

- Verification form: deterministic equality, properties/invariants, comparative advantage,
  numerical/statistical agreement, end-to-end artifact, software conformance, or visual/interactive.
- Fidelity: full fidelity, faithful scale reduction, or proxy.

A proxy requires an explicit transfer argument and limitations. A small run is valuable only when
the tested mechanism is expected to survive the reduction. Prefer several independent checks,
hidden or counterfactual cases, a passing reference, and calibrated failing mutants. Visible
examples should teach the contract but not exhaust it.

Maturity is draft, benchmark-ready, or audited. Publication requires a positive reference,
repeatability, mutants, hidden-case coverage, and review of the human packet. Published versions
are immutable; revision creates a new version.
