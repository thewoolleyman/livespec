# Handoff — credential-wrapper

The single resumable entry point for the **wrapper-agnostic credential
injection** epic: make secret-backed skill/CLI access bulletproof and
backend-generic across the fleet. A fresh session executes the next action from
this file alone — no chat history required.

## For a fresh session — read first

- **What this is.** A `/…:next` invocation failed because a thin-transport
  SKILL.md drove a **bare** `bd`-backed CLI with no credential wrapper, so
  `BEADS_DOLT_PASSWORD` was absent → Dolt "Access denied", then ~12 wasted tool
  calls. Fix = self-injecting CLIs + a backend-generic `credential_wrapper`
  config key + a generalized guard, fleet-wide. Full design in
  **`research/01-design.md`**; concrete file-by-file map in
  **`research/02-surface-inventory.md`**.
- **Epic anchor:** `livespec-zd8h` (CORE tenant, filed 2026-07-01). Status READ
  from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zd8h
  ```
- **Working model (bd cwd-tenant trap).** THIS CORE session **coordinates** and
  carries only **CORE ledger children**. Every **cross-tenant** item
  (orchestrator wiring, each repo's config+guard, adopters) is **prose-linked**
  below and filed + dispatched from **its owning repo's OWN session** (the `bd`
  cwd selects the tenant). No shadow queue; compose status from the ledger.
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready, factory-safe
  slices through the factory (`/livespec-orchestrator-beads-fabro:orchestrate`)
  — NEVER hand-code inline. Every repo change: worktree → PR → merge → cleanup;
  never `--no-verify`.
- **Any `bd` call here runs through the wrapper** — that is the very thing this
  epic makes automatic, but until self-heal ships, prefix manually:
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C … <args>`.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan credential-wrapper`.

## The critical path (dependency-ordered)

1. **Contract (CORE, spec-side, no beads).** `/livespec:propose-change` →
   `/livespec:revise` to bless `credential_wrapper` + the generic wrapper
   contract. Edits: `SPECIFICATION/non-functional-requirements.md` L1006/L1008,
   `contracts.md` L250/L258/L59-63/L133-135, `docs/installation.md` L200-203,
   root `AGENTS.md` L305-313. Drop-in contract text is in `research/01-design.md`.
2. **Schema (CORE, `.py`+JSON, Red-Green-Replay).** Add `credential_wrapper`
   (optional `list[str]`, default `[]`) to the schema→dataclass→validator
   triplet + mirror tests. Files in `research/02-surface-inventory.md` §Schema.
3. **Self-heal helper (CORE lib → vendored into orchestrator).** Pure
   `ensure_credentials(required, credential_wrapper, environ)` per design §1,
   home `livespec_runtime`.
4. **Doctor (CORE).** Add `credential_wrapper` to
   `config_named_cli_callability._named_clis`.
5. **Guard template (CORE).** Drive `beads_access_guard.py` wrapper-recognition
   from the configured wrapper (keep `with-*-env.sh` as fallback); scaffold the
   key in `templates/impl-plugin/.livespec.jsonc.jinja`; add to root
   `.livespec.jsonc`.
6. **Release CORE** (a `feat:`/`fix:` cuts a release the fleet pins to).
7. **Orchestrator wiring (F session).** `_bootstrap.bootstrap()` calls
   `ensure_credentials`; secondary raise in `_beads_client._invoke`; generalize
   F's guard; review SKILL.md prose (+ Codex twins). Bump F's `compat.pinned` to
   the new CORE release.
8. **Fleet rollout (each repo's OWN session).** Add `credential_wrapper` to the
   repo's `.livespec.jsonc`; install the generalized guard. Table in
   `research/02-surface-inventory.md` §Fleet rollout.
9. **Adopters + manifest.** openbrain (`with-openbrain-env.sh`), dolt-server;
   reconcile `.livespec-fleet-manifest.jsonc` `adopters: []` drift.

## CORE ledger children (this thread — filed 2026-07-01, all `open` P1/P2)

- `livespec-zd8h.1` — schema triplet + mirror tests (crit-path 2)
- `livespec-zd8h.2` — self-heal helper `ensure_credentials` in livespec_runtime
  (3); depends_on `.1`
- `livespec-zd8h.3` — doctor callability extension (4); depends_on `.1`
- `livespec-zd8h.4` — guard-template generalization + jinja/root config (5);
  depends_on `.1`
- (contract via `/livespec:propose-change` lifecycle, not a ledger child)
- **Move `.1`–`.4` to `backlog` before grooming** (filed = `open`; the fleet
  pattern grooms from `backlog`).

## Cross-tenant items (prose-linked; file from each owning repo's session)

- **orchestrator-beads-fabro:** `_bootstrap` self-heal wiring; `_invoke`
  secondary raise; guard generalization; SKILL.md + Codex-twin prose; CORE pin
  bump.
- **each fleet repo (git-jsonl, dev-tooling, driver-claude, driver-codex,
  runtime, console, + CORE-self):** add `credential_wrapper` key; install
  generalized guard. driver-codex additionally: fix jsonc↔beads-config tenant
  drift.
- **adopters:** openbrain, dolt-server config + guard; manifest `adopters:[]`
  reconcile.

## Read-first chain (in order)

1. **`research/01-design.md`** — finalized architecture, self-heal algorithm,
   wrapper contract + conformance, self-resolved decisions.
2. **`research/02-surface-inventory.md`** — every file to touch, per repo, guard
   blind spots, fleet rollout table, co-edit disciplines.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan credential-wrapper
```
