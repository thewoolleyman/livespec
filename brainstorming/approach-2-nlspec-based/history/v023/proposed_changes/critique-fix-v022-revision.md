# v023 — critique-fix overlay against v022

## Origin

v023 lands as a direct critique-fix during the very first execution
of the bootstrap plan. Phase 0 sub-step 3 ("`tmp/` is deleted
(empty; was working directory for earlier passes)") was based on a
false premise: the user reports `tmp/` is in active personal use as
scratch space and must not be deleted.

The bootstrap skill's then-newly-added cascading-impact scan (skill
hardening commit `398bfa8`, "Harden bootstrap skill: auto-halt on
plan/PROPOSAL drift") detected that the plan still carried the
contradictory text at lines 401 and 412 even after the
`bootstrap/open-issues.md` entry at 2026-04-25T23:33:20Z had been
logged. That detection auto-routed to the halt-and-revise
walkthrough; this file is the resulting overlay.

This overlay records one decision (the `tmp/bootstrap/` ownership
convention) and its paired plan-text corrections.

## Decisions captured in v023

1. **`tmp/` ownership convention.** The repo-root `tmp/` directory
   is user-owned scratch space and must never be deleted, cleared,
   or treated as transient by any bootstrap sub-step, dev-tooling
   script, or other automation. Any tooling-owned scratch needs are
   scoped under `tmp/bootstrap/` (creatable on demand, freely
   deletable by the bootstrap), or an analogous per-tool
   subdirectory. Rationale: the plan's original premise — that
   `tmp/` was empty stale scaffolding from earlier brainstorming
   passes — was wrong; `tmp/` is git-untracked precisely so the user
   can keep personal scratch there without polluting the repo. The
   convention is also recorded in `bootstrap/open-issues.md` entry
   `2026-04-25T23:33:20Z` (now mutated to `Status: resolved` with a
   `**Resolved:**` line pointing at this revision) and in
   cross-session memory `project_tmp_directory_ownership.md`.

## PROPOSAL.md changes

None. PROPOSAL.md has no `tmp/` references and is unaffected by
this revision's substantive content. The `history/v023/PROPOSAL.md`
snapshot copies the live PROPOSAL.md (which carries the Phase 0
sub-step 2 frozen-status header and gets the
v022→v023 active-pointer bump described under "Plan-level decisions"
below); no decision in v023 modifies the brainstorming substance.

## Plan-level decisions paired with v023

The bootstrap plan is edited in the same commit:

- **Plan Phase 0 step 3** (line 401-403) — original text "`tmp/` is
  deleted (empty; was working directory for earlier passes)" is
  replaced with the new convention: "`tmp/` is left untouched. The
  repo-root `tmp/` is git-untracked user-owned scratch space; the
  bootstrap MUST NOT delete or modify it. Any bootstrap-owned
  scratch needs go under `tmp/bootstrap/` (creatable on demand,
  freely deletable by the bootstrap)."

- **Plan Phase 0 exit criterion** (line 411-412) — original text
  "a single commit `freeze: v022 brainstorming` containing only the
  header-note addition and `tmp/` removal" is rewritten to a
  byte-identity-based criterion: "PROPOSAL.md carries the
  frozen-status header in its committed state; the latest
  history/vNNN snapshot is byte-identical to live PROPOSAL.md; the
  plan's active version pointers reference the latest snapshot."
  Two changes: (a) drop the `tmp/` removal clause per the
  convention above; (b) drop the "single commit ... containing
  only the header-note addition" framing because the v023
  revision commit naturally contains more (history snapshot,
  revision file, plan-text edits) and any future in-flight
  halt-and-revise (v024+) would similarly broaden the commit.
  The new criterion is durable across future halt-and-revises.

- **Plan "Version basis" — active pointer bumps** (lines 138-139) —
  "PROPOSAL.md v022 is now the frozen basis ... Phase 0 freezes at
  v022" updated to point at v023 as the latest snapshot. Historical
  narrative referencing v022's lineage (lines 9, 141-177, 2015-2026)
  stays unchanged — those describe v022 as a historical event.

- **Plan "Version basis" — v023 decision block** — new block
  appended after the v022 block summarizing v023 D1 and pointing at
  this overlay.

- **Plan Phase 0 step 1** (line 387) — byte-identity check
  reference bumped from `history/v022/PROPOSAL.md` to
  `history/v023/PROPOSAL.md`. Future fresh-start bootstrap
  invocations will check identity against the v023 snapshot.

- **Plan Phase 0 step 2** (line 397) — frozen-status header
  literal text bumped from "Frozen at v022" to "Frozen at v023".

- **Plan Execution prompt block** (line 2042) — "Treat PROPOSAL.md
  v022 as authoritative" bumped to v023.

- **Live PROPOSAL.md** — frozen-status header (added in Phase 0
  sub-step 2 of the in-flight session) updated from "Frozen at v022"
  to "Frozen at v023" to match the bumped plan instruction. The
  v023 snapshot copies the post-bump live file.

## Why no formal critique-and-revise

Same rationale as v022's overlay: a single uncontested decision,
narrowly scoped to plan-text correction (no PROPOSAL substance
change). Spinning up a full critique-and-revise paperwork cycle
would be ceremonial overhead disproportionate to scope. The
disciplined version-snapshot lives at `history/v023/PROPOSAL.md`;
this file documents the decision provenance.
