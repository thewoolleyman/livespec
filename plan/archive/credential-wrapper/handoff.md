# Handoff — credential-wrapper · ✅ CLOSED (epic 100% complete, thread archived)

The completion record for the **wrapper-agnostic credential injection** epic
(`livespec-zd8h`, CORE) — making secret-backed skill/CLI access bulletproof and
backend-generic across the fleet. **This thread is CLOSED and archived**; there is
no next action here. Any residual follow-up lives in the `fleet-followups` thread
(pointer below). A fresh session reading this file alone learns the epic is done,
what shipped, and where the tail went — no chat history required.

## Status — DONE (100%)

Epic **`livespec-zd8h`** closed 2026-07-01 with **all 4 children complete** and the
core bulletproofing **PROVEN by execution** (a bare `next.py` re-execs through the
configured `credential_wrapper` → valid result; one `op run`, no infinite loop,
no-op when the secret is already present). Read live status from the ledger, never
from this file:

```bash
source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zd8h
```

## What shipped (sourced from the ledger epic notes + verified on master)

- **Contract** (crit-path 1) — `/livespec:propose-change` → `/livespec:revise`
  (revise v152, PR #731) blessed the backend-generic `credential_wrapper` +
  conforming-wrapper contract. `SPECIFICATION/contracts.md` §"Spec-side CLI
  contract" / §"Doctor cross-boundary invariants" / §"Fleet agent-instruction core"
  and `non-functional-requirements.md` §"Fleet secrets …" now describe it
  (1Password becomes the *reference default*, not a hard coupling).
- **Schema triplet** (crit-path 2, `livespec-zd8h.1`) — `credential_wrapper`
  (`list[str]`, optional, default `[]`) added to the schema→dataclass→validator
  triplet + mirror tests (PR #732 / master `97b3d00`).
- **Self-heal helper** (crit-path 3, `livespec-zd8h.2`) — `ensure_credentials` /
  `decide_credentials` shipped in **`livespec_runtime` v0.6.0**; orchestrator
  `_bootstrap` re-exec wiring landed (beads-fabro #232). git-jsonl self-heal was
  REVERTED as mis-scoped (#155 → #157: the JSONL plugin needs no secret), keeping
  only its config key.
- **Doctor callability** (crit-path 4, `livespec-zd8h.3`) — `credential_wrapper`
  added to `config-named-cli-callability` WITH a **warn-vs-fail severity lever**
  (present+executable = pass; present+non-executable = fail; unresolvable = warn,
  non-fail for CI-absent runners; absent = no-op) (PR #746, master `47f8977`).
- **Guard template** (crit-path 5, `livespec-zd8h.4`) — the `beads_access_guard`
  template drives wrapper-recognition from the configured `credential_wrapper`
  first token (`with-*-env.sh` fallback), blocked set `bd`/`dolt`/`mysql` (PR #739,
  master `7b4f5c7`; earlier `1cfbd24`).
- **Config rollout** — `credential_wrapper` added to every fleet repo's
  `.livespec.jsonc` (console #77, dev-tooling #230, driver-claude #70,
  driver-codex #43, runtime #106, CORE root `ca0d22b` / PR #747).
- **Side-fix** — a broken master (the README mermaid single-source test forbade a
  deliberate lifecycle diagram) + a CI-masking bug (`check-coverage` swallowed the
  pytest exit → CI falsely green) were found and fixed in PR #738; master is now
  honestly green.

The finalized design + full surface map remain in the read-first chain below
(frozen reference).

## Deferred tail — RELOCATED to `plan/fleet-followups/` (relocate-never-drop)

The epic's non-blocking tail was moved into the `fleet-followups` inventory
(`plan/fleet-followups/research/01-followup-inventory.md`; recorded in that
thread's handoff §"Session 5"). Nothing here is a live queue — status is read from
the ledger:

- **`C15`** — CORE spec-side: `contracts.md` callability warn-vs-fail lever prose
  refinement (impl→spec drift; the exact drop-in clause is captured verbatim in the
  inventory entry). File via `/livespec:propose-change` → `/livespec:revise`.
- **`C16`** — adopters (openbrain, dolt-server): `credential_wrapper` config +
  guard, from each adopter's own session; gated on `D17`.
- **`D17`** — fleet/core decision: reconcile `.livespec-fleet-manifest.jsonc`
  `adopters: []` (do openbrain/dolt-server register as adopters?).
- **`D18`** — livespec-runtime: refresh the stale `uv.lock` (self-pin 0.4.0 → 0.6.0).
- **Disposed (not relocated):** fleet CORE-pin bumps to carry the callability check
  outward are **auto-resolving** via `bump-pin` fan-out on the next CORE
  `feat:`/`fix:` release (self-heal does not need them).

## Read-first chain (frozen reference)

1. **`research/01-design.md`** — finalized architecture, self-heal algorithm,
   wrapper contract + conformance, self-resolved decisions.
2. **`research/02-surface-inventory.md`** — every file touched, per repo, guard
   blind spots, fleet rollout table, co-edit disciplines.

## Next action

**None — thread CLOSED and archived to `plan/archive/credential-wrapper/`.**
Residual follow-ups live in `plan/fleet-followups/` (`C15`/`C16`/`D17`/`D18`).
Reopening the epic (`bd update livespec-zd8h --status …`) unarchives this thread
(move it back out of `plan/archive/`).
