# Handoff — fleet-plugin-currency

The single resumable entry point for the **fleet plugin currency** root-cause
investigation + permanent fix. A fresh session can execute the next action
from this file alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** Root-cause investigation and permanent fix for the
  stale-plugin-build failure class: fleet repos keep starting sessions on
  outdated livespec-ecosystem plugin snapshots (concrete trigger 2026-07-03:
  `livespec-console-beads-fabro`'s `/next` routed to stale cache build
  `06e3e080ae19` lacking the credential self-heal while the fixed `0.4.0`
  build sat in cache). Target invariant + phased plan:
  `plan/fleet-plugin-currency/research-plan.md` — read it before acting.
- **Epic anchor:** `livespec-c1k9` (core tenant, P0). Status is READ from
  the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-c1k9
  ```
- **⚑ Golden rules.**
  - Investigation phases (0–3) are **READ-ONLY toward every plugin cache,
    registry, marketplace cache, and settings file** — no updates,
    reinstalls, or pruning until Phase 3 closes; controlled experiments run
    only in scratch projects. Evidence first; a "helpful fix" destroys it.
  - Ready, factory-safe implementation is **factory-dispatched**
    (`/livespec-orchestrator-beads-fabro:orchestrate`) — never hand-coded
    inline. Host-only self-machinery stays maintainer-side.
  - Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
  - The overseer session **rotates before ~50% context**: refresh THIS file
    (state, in-flight agents, next action), print the resume command
    verbatim as the recap's last line.
- **Evidence home.** Raw Phase 0 capture:
  `tmp/fleet-plugin-currency/evidence/` (untracked maintainer-scratch,
  agent-scoped subdir). Curated, durable findings get committed under
  `plan/fleet-plugin-currency/research/` as phases close.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-plugin-currency`.

## The next action

1. **Collect Phase 0.** A `phase0-evidence` sub-agent was dispatched
   (Session 1, 2026-07-03) to freeze cache/registry/config state into
   `tmp/fleet-plugin-currency/evidence/` (+ `SUMMARY.md`). If its output is
   not yet in the evidence dir, re-dispatch per the capture list in
   `research-plan.md` §"Phase 0" — still read-only.
2. **Run Phase 1** (empirical resolution semantics) building on the Phase 0
   fact table: confirm/refute H1–H7 mechanism-level → commit
   `plan/fleet-plugin-currency/research/semantics.md`.
3. **Then Phase 2** (fleet audit matrix) → `research/fleet-audit.md`, and
   onward per the research plan.

## Session log

### Session 1 (2026-07-03) — thread opened

- Trigger: maintainer-reported failure in `livespec-console-beads-fabro`
  (`/next` → stale `06e3e080ae19`, raw `Access denied`, self-heal absent);
  maintainer directive: root-cause deeply and make staleness structurally
  impossible — every new session, every fleet repo, every surface, latest
  released pin, 100%.
- Filed epic `livespec-c1k9` (core, P0).
- Authored this thread scaffold (`research-plan.md` + `handoff.md`).
- Dispatched `phase0-evidence` agent (read-only forensic capture →
  `tmp/fleet-plugin-currency/evidence/`).
- Observed live corroboration of H1 in core: this session's own
  SessionStart hook updated `livespec` f79a→db76 and orchestrator
  6df3→1954 with "Restart to apply changes" — the running session stayed
  on the previous fetch.
