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
  2026-07-01); every **cross-tenant** item is **prose-linked** in the inventory
  and its status is composed from the ledger (no shadow queue).
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
3. **Groom** each filed item (`/livespec-orchestrator-beads-fabro:groom <id>`)
   into ready, dependency-layered slices — in the owning repo's session. Ripe
   CORE items to groom next: `livespec-jcc6.1/.2/.3`, `livespec-yc8e`,
   `livespec-127o`, `livespec-m0xu` (move `m0xu` to `backlog` first).
4. **Dispatch** ready, factory-safe slices via
   `/livespec-orchestrator-beads-fabro:orchestrate run --action impl:<id>`
   (Codex/Fabro), or let the Dispatcher drain the ready queue. Confirm the
   janitor + App-token loop stays green (it proved out on `zgd`/PR #74).
5. **Client-side ops** (inventory group **E**) are operator actions, not factory
   work — do them directly.
6. **Cross-links** (group **F**) resume in their own repo's thread, not here.
7. **Close `livespec-jcc6`** when the gathered items are groomed + dispatched (or
   reassigned) and nothing lingers → archive this thread to `plan/archive/`.

## Already-filed items to fold in (cite read-only; details in the inventory)

Core epic children (this thread): `livespec-jcc6.1` (B2), `livespec-jcc6.2`
(B3), `livespec-jcc6.3` (C6) — all `backlog`.
Other core: `livespec-127o` (README), `livespec-m0xu` (template rename, still
`open`), `livespec-yc8e` + `livespec-mpkaz4` (reaper bugs), `livespec-aava` (B5,
Codex skill-picker).
Cross-tenant: `bd-ib-2wq` (beads-fabro); `livespec-dev-tooling-9j8` +13 children
(dev-tooling, `9j8.1` + `livespec-gnjb` ready).

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
