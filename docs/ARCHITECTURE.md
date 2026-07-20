# Architecture

The filesystem is authoritative and paper-first. A paper owns shared metadata and source material,
then a clean list of one or more versioned capsules:

    papers/PAPER/
      paper.yaml
      paper/
      resources/
      capsules/CAPSULE/VERSION/
        capsule.yaml
        public/
        private/

A suite references paper ID, capsule ID, and version explicitly. prepare makes one independent Git
repository for every capsule/agent/attempt. Runtime state mirrors scientific ownership:

    runs/SUITE/papers/PAPER/capsules/CAPSULE/agents/AGENT/attempt-NNN/

Paper files are copied to workspace/paper and workspace/paper_resources. Capsule task material is
copied to WORK_PLAN.md, EXECUTABLE_CONTRACT.md, TASK.md, resources/, and starter/. No candidate sees private checks, hidden inputs,
references, or another model's output.

The lifecycle is:

1. Prepare an identical public workspace for each model.
2. Run the native assistant normally in that directory, with its usual tools and internet access.
3. Seal submission/ into an immutable revision with its digest and Git provenance.
4. Reproduce from a fresh sealed copy. Artifacts go to a separate directory.
5. Run the private verifier through a language-agnostic JSON protocol.
6. Let the core apply check dependencies and weighted objective scoring.
7. Build a static packet for human scientific and educational review.
8. Compare runs in portable Markdown, HTML, CSV, and JSON reports; optionally curate a learning copy.

Candidate failure and evaluator failure are separate states. Verification code is capsule-specific;
copying, lifecycle, scoring, provenance, isolation, and review presentation remain framework code.
No database, frontend framework, cloud SDK, or mandatory model judge is involved.

The local backend deliberately encodes no hardware requirement in scientific capsule manifests.
The same repository may be placed on a workstation or cluster. A future remote backend can stage
the same immutable inputs and return the same protocol records without changing capsules.
