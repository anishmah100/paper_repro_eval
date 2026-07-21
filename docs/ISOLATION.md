# Isolation and open-world policy

Models may search the web, install tools, use official implementations, and otherwise operate at
full native-agent power. These are useful research-tool capabilities and are equally available to
all compared agents.

The one prohibited information flow is reading another candidate's local workspace, submission,
artifacts, logs, verification, or review. prepare therefore creates physical copies and an
independent Git repository for every candidate. There are no symlinks or shared worktrees. Initial
tree digests are compared automatically.

For ordinary use, run the bare `paper_repro_eval` dashboard, choose a model and task, and launch the
assistant in the workspace shell it opens. The dashboard never combines candidate workspaces and
hides framework-only smoke/test labels, but directory isolation still depends on the operator and
agent honoring the rule. Where adversarial enforcement matters, run each agent in a container or VM
that mounts only its workspace. Network access need not be disabled. Never mount the outer runs/
tree or private capsule directories into a candidate container.
