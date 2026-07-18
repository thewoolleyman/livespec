# rop-sweep-fleet-policy — core slice DONE; full-ROP + BLE backfill epic is next

**Status: the core slice is implemented in livespec PR
[#1321](https://github.com/thewoolleyman/livespec/pull/1321) (branch
`rop-sweep-fleet-policy-core`).** The two sibling `rop-sweep-*` plans already
merged before this slice ran. What remains is the fleet **backfill epic** (below),
which the "full ROP everywhere" decision expanded into.

---

## Landscape at execution time (2026-07-18)

The audit found the coordination had already advanced since this plan was drafted
(2026-07-16):

- **`rop-sweep-consumer-cleanup` — MERGED** in `livespec-orchestrator-beads-fabro`
  (commit `3d2ff13`): that repo now vendors `returns`, enables ruff `BLE`, and
  routed its expected failures through effects. Zero product blind-catches.
- **`rop-sweep-library-checks` — MERGED** in `livespec-dev-tooling` (plan archived
  `0b0125e`): shipped `livespec_dev_tooling/checks/source_trees_scoped_to_consumer.py`,
  the drift **detection** guardrail (fails on a `missing` declared path or a
  non-`livespec` consumer retaining core's `.claude-plugin/scripts/livespec` scope).

Per-repo ROP audit (product code = the `source_trees` package, excluding synced
`.claude/` host-machinery hooks):

| Repo | product blind-catches | `returns` | `BLE` | `reportUnusedCallResult` | on railway |
|---|---|---|---|---|---|
| `livespec` (core) | 0 | yes | **no** | yes | full (reference) |
| `livespec-orchestrator-beads-fabro` | 0 | yes | yes | yes | full (cleaned up) |
| `livespec-orchestrator-git-jsonl` | 0 | **no** | **no** | yes | **not on railway** |
| `livespec-runtime` | 1 (documented `retry.py`) | **no** | **no** | yes | **not on railway** |
| `livespec-driver-claude` / `-codex` | 0 (fail-open hooks) | no (n/a) | **no** | **no** | hook-only |
| `livespec-dev-tooling` | few (fail-open, noqa'd) | **no** | **no** | yes | library (special) |
| `livespec-console-beads-fabro` | — (Rust) | — | — | — | zero-Python exemption |

## Maintainer decisions (2026-07-18)

1. **Fleet bar = "flat: full ROP everywhere"** — every Python-carrying fleet repo
   vendors `returns` and is on the railway, INCLUDING the thin driver plugins
   (stronger than the tiered recommendation; chosen with the "forces the railway
   onto hook-only code" trade-off stated).
2. **ruff `BLE` = "add to template + backfill fleet."**

## What the core slice landed (PR #1321)

- **Spec (nfr.md, revise v165)** — accepted after an independent Fable-model
  NO-BLOCKERS review:
  - §"ROP composition": the **observability pass-through-tap rule** (Part B) —
    side-effects are value-preserving `.map`/`tap` steps, never a reason to catch;
    "the call can throw" is never itself a reason to lift; a critical step is
    protected from an observability failure by **ordering**, not catching.
  - §"Linter rule set": ruff **`BLE`** added to the enumerated set (27 → 28).
  - §"Shared content provenance": the **full-ROP fleet+adopter-wide bar** (sibling
    to the red-green-replay bullet). The only permitted broad `except Exception`
    is a single outermost boundary — a CLI supervisor bug-catcher OR a
    never-wedge-the-agent hook's fail-open pass-through (grounded in
    `contracts.md`'s hook fail-open discipline). Sole exemption: zero-first-party-
    Python (the Rust console).
- **Template (`templates/orchestrator-plugin/…pyproject.toml.jinja`)** —
  - **Part D (prevention):** now EMITS a `[tool.livespec_dev_tooling]` block with
    `source_trees` parameterized to the consumer's own package. Root cause of the
    beads-fabro dormancy: `load_config` falls back to core's `livespec` layout
    ONLY when the block is absent, so an omitted/hand-written block silently
    scoped the ROP checks at a package the consumer lacks. Emitting the block is
    prevention; `source_trees_scoped_to_consumer` is detection.
  - **Part C:** adds ruff `BLE` to the template select.

---

## NEXT: the full-ROP + BLE backfill epic — FILED

The backfill is filed under **epic `livespec-y2lkf4` — "Full-ROP + ruff BLE fleet
backfill"** in livespec CORE's ledger. Per the fleet convention the coordinating
epic and ALL child work-items live in the one core tenant (the factory dispatches
each child into the right repo's sandbox; the child titles name their target repo).
The epic `tracks` its 6 children. **Status is READ from the ledger** via
`list-work-items` / `next` — never stored here (no-shadow-ledger).

**Next action:** `groom livespec-y2lkf4` to decompose/tier the epic's children into
`ready`, then dispatch each via the FACTORY path — the `drive` operation
(`impl:<id>`) or the Dispatcher drain — under the janitor gate. Do NOT implement
these in-session (the retired inline anti-pattern).

Per-repo children (the ledger holds their ids; each child's title names its repo).
Design record: livespec nfr.md v165 §"Shared content provenance" fleet-bar +
§"Linter rule set" BLE:

1. **`livespec` (core)** — add `"BLE"` to pyproject `[tool.ruff.lint].select`.
   `.claude/hooks/**` + `.claude/skills/overseer/**` are already ruff-excluded, but
   the legit supervisor bug-catcher(s) (`commands/*/main`, doctor `run_static.py`)
   need `# noqa: BLE001 — <reason>`. Verify `just check` green.
2. **`livespec-orchestrator-git-jsonl`** — vendor `dry-python/returns`; put product
   logic on the Result/IOResult railway; add `"BLE"`. Largest slice (clean of
   blind-catches today but never adopted the railway).
3. **`livespec-runtime`** — narrow `livespec_runtime/cross_repo/retry.py:49`'s broad
   `except Exception` to named expected transport exceptions (it currently converts
   bugs → None/UNKNOWN by documented design — the exact anti-pattern the Part B
   observability rule targets); add `"BLE"`; decide vendoring `returns` (library).
4. **`livespec-driver-claude`** — add `"BLE"` + `reportUnusedCallResult = "error"`;
   fail-open hooks keep `# noqa: BLE001 — fail-open by contract`; decide vendoring
   `returns` (hook bodies are minimal — the fail-open handler IS the single boundary).
5. **`livespec-driver-codex`** — same as driver-claude.
6. **`livespec-dev-tooling`** — add `"BLE"`; audit its own product catches
   (`green_token.py`, `agent_hooks/*`, `install_no_shadow_ledger.py`) — narrow or
   noqa each; it already has `reportUnusedCallResult`.
7. **`livespec-console-beads-fabro`** — N/A (Rust, zero first-party Python = the
   sole spec exemption). The fixed template scaffolds it correctly when it gains Python.

Sequencing: independent per-repo self-contained slices. `git-jsonl` (item 2) is the
heaviest (railway adoption). Each closes with `just check` green + the repo's
`/livespec:doctor`.
