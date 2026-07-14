---
name: reference_beads_tenant_access
description: How to read/write the livespec-runtime beads tenant — wrap bd/orchestrator calls in with-livespec-env.sh to inject BEADS_DOLT_PASSWORD.
metadata: 
  node_type: memory
  type: reference
  originSessionId: db4fe3bd-c210-4624-b143-857675bb0685
---

The `livespec-runtime` beads/Dolt tenant lives on the shared dolt
sql-server (`127.0.0.1:3307`, tenant/prefix/db/user all
`livespec-runtime`). The tenant PASSWORD is never in `.livespec.jsonc`
or the shell env; it is injected at call time via the 1Password env
wrapper `/usr/local/bin/with-livespec-env.sh` (root:livespec, exec via
the `livespec` group — the `ubuntu` user is a member).

Run any orchestrator/`bd` operation that touches the real tenant behind
it, e.g.:

```bash
with-livespec-env.sh python3 <plugin-root>/scripts/bin/list_work_items.py --json
```

It sets `BEADS_DOLT_PASSWORD` (and friends). Without it, the store call
fails / falls back. `LIVESPEC_BEADS_FAKE=1` forces a hermetic in-memory
backend (CI/tests only — NOT the real tenant). The active orchestrator
plugin root resolves under
`/home/ubuntu/.claude/plugins/cache/livespec-orchestrator-beads-fabro/.../<hash>/`.
See [[reference_livespec_repo_is_bare]].
