# Handoff — fleet-followups

The single resumable entry point for the **fleet follow-ups & lingering cleanup**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The coordination anchor that gathers ALL post-lifecycle
  follow-ups + lingering cleanup across the fleet into one runnable point. It
  succeeds the (closed + archived) `work-item-state-machine` fleet epic. Items
  span multiple tenants (core, beads-fabro, dev-tooling, driver-codex,
  git-jsonl, runtime), so — per the fleet pattern — this anchor carries only a
  few **same-tenant (core) ledger children** (`livespec-jcc6.1/.2/.3`, filed
  2026-07-01; `.1` and `.2` are now `ready`, `.3` held at `backlog` — see
  §"Session 2"); every **cross-tenant** item is **prose-linked** in the
  inventory and its status is composed from the ledger (no shadow queue).
- **Epic anchor:** `livespec-jcc6` (core tenant, `backlog`). Status is READ from
  the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-jcc6
  ```
- **Working model.** THIS core session **coordinates**; per-tenant grooming +
  factory dispatch happen in **each owning repo's own session** — launch the
  session from the repo that owns the work (its tenant selects via cwd, its
  `plan/` threads, its code + `just check`). Core is the anchor because the set
  is cross-tenant, not because the work lives here.
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready, factory-safe
  slices through the factory (`/livespec-orchestrator-beads-fabro:orchestrate`
  → Codex/Fabro under the janitor gate) — NEVER hand-code inline.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-followups`.

## The next action

1. **Read `research/01-followup-inventory.md`** — the full grouped catalog (ids,
   tenants, one-line actions, and each item's live ledger id / FILED marker). It
   is the map for everything below.
2. **CORE filing of the unfiled inventory items is DONE** (2026-07-01): B2 →
   `livespec-jcc6.1`, B3 → `livespec-jcc6.2`, C6 → `livespec-jcc6.3` (all
   `backlog`); B1 was already `livespec-yc8e` (+ `livespec-mpkaz4`, + the B1(b)
   sub-bug in `yc8e`'s notes); B5 ≈ `livespec-aava`. (Note: `livespec-m0xu` is
   filed but still `open` — filed ≠ backlog-ready; move it to `backlog` before
   grooming, per step 3.) **Still-unfiled items are CROSS-TENANT** — they are
   NOT fileable from THIS core session (the `bd` cwd-tenant trap); file each
   from its owning repo's OWN session: **B4** (beads-fabro/runtime
   `migrate-tenant` CLI), **C7** (driver-codex "DEFERRED" wording), **C8**
   (git-jsonl §6 doc-reconcile), **D9** (fleet/dev-tooling `hydrate`
   worktree-pack), **D10** (fleet/core review-policy decision). **In THIS core
   session the only immediately-runnable action is grooming (step 3).**
3. **Dispatch the two `ready` core items** — `livespec-jcc6.1` (propose/revise
   cwd resolution) and `livespec-jcc6.2` (doctor_static `--spec-target`) are
   staged `ready` with acceptance + autonomy tier (§"Session 2"); the impl `next`
   ranker surfaces both. Let the **Dispatcher drain them** (dedicated dispatch
   env with App-token + Fabro creds) or run
   `/livespec-orchestrator-beads-fabro:orchestrate run --action impl:<id>` from a
   session that HAS those creds. They are NOT dispatchable from this interactive
   coordination session (creds absent — see §"Session 2"). Confirm the janitor +
   App-token loop stays green (it proved out on `zgd`/PR #74).
4. **Groom the remaining core items** (`/livespec-orchestrator-beads-fabro:groom
   <id>` in a session that owns the tenant): `livespec-127o` (README — epic-shaped:
   a spec-contract slice → `/livespec:propose-change` + a README-authoring slice
   → factory), `livespec-m0xu` (template rename — ripples across copier refs; now
   at `backlog`), `livespec-yc8e` (reaper — two bugs; may split). `livespec-jcc6.3`
   (prose refresh) stays `backlog` until it has a human-verifiable acceptance
   (its "prose is correct" acceptance is not autonomously checkable). The two
   `needs-regroom` items `livespec-nylyhi` + `livespec-rmew4k` are CROSS-TENANT
   (route to driver-codex / orchestrator-beads-fabro / spec) — groom them from
   those repos' sessions, not here.
5. **Client-side ops** (inventory group **E**) are operator actions, not factory
   work — do them directly.
6. **Cross-links** (group **F**) resume in their own repo's thread, not here.
7. **Close `livespec-jcc6`** when the gathered items are groomed + dispatched (or
   reassigned) and nothing lingers → archive this thread to `plan/archive/`.

## Already-filed items to fold in (cite read-only; details in the inventory)

Core epic children (this thread): `livespec-jcc6.1` (B2, **`ready`**),
`livespec-jcc6.2` (B3, **`ready`**), `livespec-jcc6.3` (C6, `backlog` — held).
Other core: `livespec-127o` (README, `backlog`), `livespec-m0xu` (template
rename, now `backlog`), `livespec-yc8e` + `livespec-mpkaz4` (reaper bugs),
`livespec-aava` (B5, Codex skill-picker).
Cross-tenant: `bd-ib-2wq` (beads-fabro); `livespec-dev-tooling-9j8` +13 children
(dev-tooling, `9j8.1` + `livespec-gnjb` ready).

## Session 2 (2026-07-01) — DoR triage + factory-boundary findings

Ran Revise / Gap / Groom / Orchestrate over the thread; the durable outcomes:

- **Revise — no-op.** `SPECIFICATION/proposed_changes/` holds only the README
  placeholder; spec-side `next` surfaces only `prune-history` (151 history
  versions, low urgency). No pending proposal to revise.
- **DoR triage (the effective "make items dispatchable" step).** The clean,
  single-coherent-done, autonomously-test-verifiable core items were promoted to
  dispatchable `ready` with acceptance + autonomy tier: **`livespec-jcc6.1`** and
  **`livespec-jcc6.2`**. `impl next` went 0 → 2 candidates. `livespec-jcc6.3`
  (prose refresh) was **held at `backlog`** — its acceptance ("the rewrite is
  correct") is not autonomously verifiable (a grep confirms old terms dropped,
  not that the new prose is right), so its honest DoR verdict is
  `not-yet-actionable`. `livespec-m0xu` moved `open` → `backlog`.
- **Gap — detection ran, capture deferred (scope).** `detect-impl-gaps` emits
  **~370 mechanical candidate gap-ids** and **0** are captured (`origin:gap`
  is empty). Blind-capturing 370 over 151 accreted spec versions would be noisy;
  capture needs a scoped pass (e.g. `--since-version <recent>` or a focused
  subtree). Deferred, not skipped.
- **Groom — targets are cross-tenant.** The only two `needs-regroom` items,
  `livespec-nylyhi` (fixes land in `livespec-driver-codex` +
  `livespec-orchestrator-beads-fabro`) and `livespec-rmew4k` (cross-repo,
  spec-gated; overlaps `livespec-4dzbcv`), groom into route-out slices, not
  core-local dispatchable work — groom them from those repos' sessions.
- **Orchestrate — dispatch runs in the dedicated Dispatcher env, not here.** The
  GitHub App-token + Fabro API creds are ABSENT in this interactive session (0
  bytes, even under the env wrapper) and no dispatcher daemon is running, though
  the `fabro` binary is present. Real dispatch (Fabro sandbox → janitor gate →
  merge) runs in the Dispatcher environment with its own secrets — the
  interactive `/plan` session coordinates + stages `ready` work; it does not fire
  the factory inline (the retired-inline-overseer boundary).

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
