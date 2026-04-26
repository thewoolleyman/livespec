---
name: prune-history
description: Destructively prune old vNNN/ snapshots from <spec-root>/history/ to bound history size. Requires explicit user invocation (model-driven invocation is disabled). Invoked only via /livespec:prune-history or an explicit "prune the livespec history" request from the user.
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# prune-history

Authoring deferred to `skill-md-prose-authoring` (Phase 7
agent-generated against the production livespec template).
