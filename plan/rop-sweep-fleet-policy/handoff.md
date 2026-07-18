# rop-sweep-fleet-policy — COMPLETE (planning done; 6 children READY for the factory)

**This planning thread's work is DONE.** Spec + template landed; the backfill epic
+ 6 per-repo children are filed and all at `ready`. The only remaining work is the
FACTORY implementation of those 6 children — NOT a planning-session task. If the
overseer restarts this session, there is nothing to plan here.

## ⛔ DO NOT run `groom livespec-y2lkf4`

The epic is ALREADY decomposed (its 6 children were filed during the plan step).
The `groom` operation decomposes a `backlog` epic into FRESH slices and then closes
the epic — running it here would file 6 DUPLICATE slices and orphan the originals.
The children were advanced `pending-approval → ready` via the admission valve
(`drive --action approve:<id>`), which is the correct operation — not groom.

## What landed (all merged / filed)

- **Spec** — livespec PR [#1321](https://github.com/thewoolleyman/livespec/pull/1321),
  merged. `non-functional-requirements.md` revise **v165**: §"ROP composition"
  observability pass-through-tap rule; §"Linter rule set" ruff `BLE` (27→28);
  §"Shared content provenance" the full-ROP fleet+adopter-wide bar (fail-open hooks
  conform via their silent pass-through; sole exemption = zero-first-party-Python).
- **Template** — same PR: `templates/orchestrator-plugin/…pyproject.toml.jinja` now
  emits the parameterized `[tool.livespec_dev_tooling]` block (Part D drift-prevention;
  pairs with the already-landed `source_trees_scoped_to_consumer` detection) + `BLE`.
- **Handoff bookkeeping** — livespec PR #1331, merged.
- **Epic + children** — in livespec CORE's ledger (single coordinating tenant; the
  factory dispatches each child into its target repo). Status is READ from the ledger
  (`list-work-items` / `next`), never stored here.

## The epic (verify with `bd dep tree livespec-y2lkf4` under the credential wrapper)

`livespec-y2lkf4` (epic, `backlog`) `tracks` 6 children, all `ready`:

- `livespec-ftbvgc` — livespec (core): add `"BLE"` to ruff select; `# noqa: BLE001`
  the legit supervisor bug-catcher(s) (`commands/*/main`, doctor `run_static.py`).
  `.claude/hooks/**` + `.claude/skills/overseer/**` already ruff-excluded.
- `livespec-unc45o` — livespec-orchestrator-git-jsonl: vendor `dry-python/returns`;
  put product logic on the Result/IOResult railway; add `"BLE"`. Heaviest slice.
- `livespec-apiiwc` — livespec-runtime: narrow `cross_repo/retry.py:49`'s broad
  `except Exception` to named transport exceptions; add `"BLE"`; decide vendoring `returns`.
- `livespec-heejvw` — livespec-driver-claude: add `"BLE"` + `reportUnusedCallResult`;
  fail-open hooks keep `# noqa: BLE001 — fail-open by contract`.
- `livespec-kumh3e` — livespec-driver-codex: same as driver-claude.
- `livespec-qgp2jt` — livespec-dev-tooling: add `"BLE"`; audit its own product catches
  (`green_token.py`, `agent_hooks/*`, `install_no_shadow_ledger.py`) — narrow or noqa each.
- livespec-console-beads-fabro: NO child (Rust, zero first-party Python = the exemption).

## Next action (if any) — FACTORY, not planning

The 6 children are `ready`, i.e. factory-dispatchable. To implement:
`drive --action impl:<id>` per child, or let the Dispatcher drain `ready` items — under
the janitor gate (`just check` + `/livespec:doctor`). Do NOT implement in-session.
`git-jsonl` (`unc45o`) is the heaviest (railway adoption).

## Close-out

When all 6 children are `done`, the epic `livespec-y2lkf4` can close, and this plan
thread archives to `plan/archive/rop-sweep-fleet-policy/` (per the plan operation's
epic-close → archive rule). Until then, nothing here needs a planning session.

## Reference — 2026-07-18 maintainer decisions (context for the backfill)

1. **Fleet bar = "flat: full ROP everywhere"** — every Python-carrying fleet repo
   vendors `returns` + is on the railway, Drivers included (chosen over the tiered rec).
2. **ruff `BLE` = "add to template + backfill fleet."**
Both sibling `rop-sweep-*` plans had already merged before this slice ran
(`rop-sweep-consumer-cleanup` in beads-fabro `3d2ff13`; `rop-sweep-library-checks` in
dev-tooling, archived `0b0125e`).
