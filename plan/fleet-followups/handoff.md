# Handoff — fleet-followups

The single resumable entry point for the **fleet follow-ups & lingering cleanup**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The coordination anchor that gathers ALL post-lifecycle
  follow-ups + lingering cleanup across the fleet into one runnable point. It
  succeeds the (closed + archived) `work-item-state-machine` fleet epic. Items
  span multiple tenants (core, beads-fabro, dev-tooling, driver-codex,
  git-jsonl, runtime), so — per the fleet pattern — this anchor has few/no
  ledger children; cross-tenant items are **prose-linked** in the inventory and
  their status is composed from the ledger (no shadow queue).
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
   tenants, one-line actions). It is the map for everything below.
2. **Triage + file the UNFILED items** (inventory groups **B** tooling/dev-ex,
   **C** doc/config drift, **D** env/infra) into their named tenant as work-items
   (`--labels origin:freeform`, 2-step to `backlog`). Core-tenant items (B1, B2,
   B3, C6, D9, D10) can be filed from THIS session; others from their repo's
   session (the `bd` cwd-tenant trap).
3. **Groom** each filed item (`/livespec-orchestrator-beads-fabro:groom <id>`)
   into ready, dependency-layered slices — in the owning repo's session.
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

`livespec-127o`, `livespec-m0xu` (core); `bd-ib-2wq` (beads-fabro);
`livespec-dev-tooling-9j8` +13 children (dev-tooling, `9j8.1` + `livespec-gnjb`
ready).

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
