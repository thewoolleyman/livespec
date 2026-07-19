# rop-sweep-fleet-policy — full-ROP railway backfill; briefs rewritten; EXECUTING autonomously

**State (2026-07-19).** Planning is refined and the maintainer authorized **in-session
autonomous execution** (overriding the earlier "do not implement in-session" guard). The
epic `livespec-y2lkf4` + its 6 per-repo children are filed; all `ready`. The children's
briefs were **rewritten** to mandate the full ROP railway everywhere (see below) after a
code-level audit showed the earlier "thin repo / decide vendoring returns" framing was
factually wrong. Status is READ from the ledger (`bd dep tree livespec-y2lkf4` /
`list-work-items` / `next`), never stored here.

## ⛔ DO NOT run `groom livespec-y2lkf4` (the EPIC)

The epic is ALREADY decomposed into its 6 children. Epic-level `groom` re-decomposes a
`backlog` epic into FRESH slices and closes it — that would duplicate/orphan the 6.
Children were admitted `pending-approval → ready` via `drive --action approve:<id>`.
**Individual-child groom IS allowed and expected** for the oversized children (`qgp2jt`,
possibly `apiiwc`): `groom <child-id>` slices ONE child — a different operation from the
forbidden epic groom.

## What the flat-full-ROP decision actually means here (code-audited 2026-07-19)

Ref #1 (below) mandates: every Python-carrying fleet repo vendors `returns` + is on the
`Result`/`IOResult` railway, **Drivers and dev-tooling included**, sole exemption =
zero-first-party-Python (the Rust console). A code audit of every target repo:

| Child | Repo | first-party Python | on railway now? | slice |
|---|---|---|---|---|
| `ftbvgc` | livespec (core) | returns vendored, 83 files on railway, reportUnusedCallResult | ✅ reference | add `BLE` only (HIGH) |
| `unc45o` | livespec-orchestrator-git-jsonl | not on railway | ❌ | vendor returns + railway + `BLE` (MEDIUM) |
| `apiiwc` | livespec-runtime | ~3,900 LOC / 31 files, 27 tests | ❌ | vendor returns + railway + narrow `retry.py:49` + `BLE` (MEDIUM) |
| `heejvw` | livespec-driver-claude | ~800 LOC / 4 hooks, 9 tests | ❌ | vendor returns + railway (hook bodies) + `BLE` + reportUnusedCallResult (MEDIUM) |
| `kumh3e` | livespec-driver-codex | ~1,073 LOC / 6 hooks, 12 tests | ❌ | same as driver-claude (MEDIUM) |
| `qgp2jt` | livespec-dev-tooling | **~23,700 LOC / 122 files** | ❌ (returns in 2 files) | **LARGE — groom into slices first**; adopt returns + railway + `BLE` |
| — | livespec-console-beads-fabro | Rust, zero first-party Python | — | no child (sole exemption) |

**Two corrections the rewrite fixed:** (1) `apiiwc`/`heejvw`/`kumh3e` said "decide vendoring
returns" — now MUST, per Ref #1. (2) The "noqa the fail-open/supervisor catchers" step in
`ftbvgc`/`heejvw`/`kumh3e` was moot — those catchers sit in ruff-EXCLUDED dirs
(`.claude/hooks/**`, `.claude-plugin/hooks/**`, `livespec/hooks/**`,
`.claude/skills/overseer/**`), so `BLE` never flags them. For the Driver hooks the
substantive guard is pyright `reportUnusedCallResult` (pyright DOES include the hook dirs);
the real work is the railway adoption, not noqa.

## Scale caveat (surfaced to the maintainer)

"Full ROP everywhere" is ~29k LOC of railway conversion fleet-wide. `dev-tooling` (23.7k)
and `runtime` (3.9k) are real library conversions, not config tweaks. Execution order:
land the bounded wins first (`ftbvgc` add-BLE), then the Driver/git-jsonl railway slices,
and GROOM `qgp2jt` (and slice `apiiwc` if a single run proves too big) before running them.

## What landed earlier (all merged / filed)

- **Spec** — livespec PR #1321, merged. nfr.md v165: §"ROP composition" observability
  pass-through-tap; §"Linter rule set" ruff `BLE` (27→28); §"Shared content provenance"
  full-ROP fleet+adopter-wide bar (Drivers/dev-tooling included; sole exemption =
  zero-first-party-Python).
- **Template** — same PR: `templates/orchestrator-plugin/…pyproject.toml.jinja` emits the
  parameterized `[tool.livespec_dev_tooling]` block + `BLE`.
- **Handoff bookkeeping** — livespec PRs #1331, #1344 (finalize), merged.
- **Epic + children** — livespec CORE ledger (single coordinating tenant; factory
  dispatches each child into its target repo).

## Next action — EXECUTE (in-session, autonomous — authorized 2026-07-19)

Drive each `ready` child to `done` under the hard janitor gate (`just check` +
`/livespec:doctor`), each in its own worktree/sandbox, PR → merge, then re-verify. Order:
1. `ftbvgc` (core add-BLE — bounded, validates the cycle).
2. `heejvw`, `kumh3e`, `unc45o`, `apiiwc` (railway slices; slice `apiiwc` if too big).
3. `qgp2jt` — `groom` into per-subpackage slices, then run the slices.
Do NOT run epic-level groom. Do NOT `--no-verify`. Cross-repo work-item edits land in the
Dolt ledger (not git); the only git artifact for THIS plan is this handoff.

## Close-out

When all children (and any groomed slices) are `done`, the epic `livespec-y2lkf4` closes
and this thread archives to `plan/archive/rop-sweep-fleet-policy/`.

## Reference — maintainer decisions

1. **Fleet bar = "flat: full ROP everywhere"** (2026-07-18) — every Python-carrying fleet
   repo vendors `returns` + is on the railway, Drivers included (chosen over the tiered
   rec). Re-affirmed 2026-07-19 after the code audit: these are real, substantial,
   tested repos, so all owe the full railway + discipline stack.
2. **ruff `BLE` = "add to template + backfill fleet."**
3. **Execution = in-session, autonomous** (2026-07-19) — override of the earlier
   factory-only / do-not-implement-in-session posture.

Both sibling `rop-sweep-*` plans merged before this slice
(`rop-sweep-consumer-cleanup` beads-fabro `3d2ff13`; `rop-sweep-library-checks` dev-tooling
archived `0b0125e`).
