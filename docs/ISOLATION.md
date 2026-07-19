# Isolation and open-world policy

Models may search the web, install tools, use official implementations, and otherwise operate at
full native-agent power. These are useful research-tool capabilities and are equally available to
all compared agents.

The one prohibited information flow is reading another candidate's local workspace, submission,
artifacts, logs, verification, or review. prepare therefore creates physical copies and an
independent Git repository for every candidate. There are no symlinks or shared worktrees. Initial
tree digests are compared automatically.

For ordinary use, open the assistant directly at the printed workspace path. Directory isolation
depends on the operator honoring the rule. Where adversarial enforcement matters, run each agent
in a container or VM that mounts only its workspace. Network access need not be disabled. Never
mount the outer runs/ tree or private capsule directories into a candidate container.
