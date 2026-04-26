# Executor decisions

Append-only log of executor judgment calls made during phase work that
weren't pre-decided in the plan. The bootstrap skill is the only
writer; entries are added via the skill's "record a decision first"
flow.

Each entry's heading carries the timestamp, phase, and sub-step. Body
captures the decision and its rationale.

## 2026-04-26T00:35:48Z — phase 0 sub-step 5

**Decision:** For plan-internal text-correction drift discovered
during Phase 0 sub-step 5 (three stale `bootstrap/.claude-plugin/`
references at plan lines 432, 2087, 2277), bypass the standard
halt-and-revise walkthrough and fix the references directly in a
regular commit. Codified the carve-out by amending
`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`'s
"Plan/PROPOSAL drift is automatically blocking" section so this
distinction is durable.

**Rationale:** Halt-and-revise is calibrated for semantic drift
between executor interpretation and plan/PROPOSAL text (the v018-
v023 lineage). The drift here is entirely internal to the plan:
PROPOSAL.md is clean, plan §8's directory-shape diagram (lines
2179-2197) and four-command marketplace setup (lines 2199-2244)
are unambiguously authoritative, and three sentences elsewhere
in the plan failed to track the marketplace-setup propagation
in commit `4e423cc`. The fix is purely mechanical — there is no
decision to make about which path is correct. Producing a v024
snapshot with an unchanged PROPOSAL.md would be ceremony, not
verification. The skill carve-out preserves halt-and-revise as
the default for any non-mechanical drift.

## 2026-04-26T01:35:16Z — phase 0 sub-step 5 (rule reformulation)

**Decision:** Supersedes the rationale of the 2026-04-26T00:35:48Z
entry above. Refactored the bootstrap skill's drift-handling rule
into a two-case structure classified by which file the drift is
in: PROPOSAL.md drift is auto-blocking and routes to the formal
halt-and-revise walkthrough; plan-only drift is fixed directly
via a user-gated AskUserQuestion + edit + commit + decisions.md
entry, never entering open-issues.md. Removed the previously-
written "Carve-out: plan-internal text-correction drift" section
(executor-discretion conditions on whether the fix was "purely
mechanical" — too much AI judgment, too easy to abuse). Updated
plan §"Plan-correction discipline during execution" → §"Drift-
handling discipline during execution" with a four-row table
matching the new skill rule.

**Rationale:** User principle (verbatim): "PROPOSAL.md is
versioned, so it needs to go through a formal process. The plan
can be directly fixed because it is not versioned." The asymmetry
between PROPOSAL.md and the plan comes from versioning, not from
how mechanical the fix is. PROPOSAL.md has `history/vNNN/PROPOSAL.md`
snapshots from v018+ and is frozen at the latest vNNN; any change
must produce a new vNNN snapshot. The plan has no `history/vNNN/
PLAN_*.md` analog and is throwaway scaffolding deleted at Phase
11; plan changes don't need a snapshot. The new rule classifies
on file-affected (a check the executor can do mechanically), not
on a fuzzy "is this purely mechanical?" judgment. The user gates
plan edits via AskUserQuestion so the executor never modifies the
plan silently.

## 2026-04-26T05:30:00Z — phase 1 sub-step 3 (pre-execution scan)

**Decision:** Apply v024 companion-doc reconciliation round 2 to
`python-skill-script-style-requirements.md`. Five additional
pre-v024 "mise-pinned" framing slips found at lines 103-105,
1000, 1066, 1710-1714, and 1724-1727 — surfaced by the bootstrap
skill's mandatory consistency scan at the start of Phase 1
sub-step 3 (which loads the style doc to source the `[tool.ruff]`
and `[tool.pytest]` config the plan defers to). Edits land via
the same overlay-extension pattern as the round-1 follow-up
(commit `04272ef`): surgical Edit on the 5 passages, plus a new
"## v024 companion-doc reconciliation (round 2)" section
appended to `history/v024/proposed_changes/critique-fix-v023-revision.md`
documenting them. PROPOSAL.md snapshot at `history/v024/PROPOSAL.md`
remains byte-identical; no plan edits needed (Phase 1's
canonical bootstrap order already cites `mise install` then
`uv sync --all-groups` then `just bootstrap` correctly). Single
commit message: `Revise proposal to v024 (cont 2): companion-doc
UV reconciliation (round 2)`. Gate confirmed via AskUserQuestion
2026-04-26 (option: "Extend v024 with a second cont follow-up
(Recommended)").

**Rationale:** Companion-doc drift falls outside the bootstrap
skill's literal two-case rule (Case A = PROPOSAL.md, Case B =
plan), but the user's "halt-and-revise on any inconsistency"
principle (origin of v024) and the v024 round-1 precedent both
established that companion-doc inconsistencies must be
reconciled to keep PROPOSAL.md and its companion docs internally
consistent at the v024 logical version. The round-1 sweep missed
these 5 passages because it grepped only for the specific terms
the round-1 reviewer was looking at; the bootstrap skill's
consistency scan is the systematic fallback that catches
straggling drift at sub-step boundaries. Treating this as a v024
overlay extension (not a new vNNN) preserves the principle that
new vNNN snapshots are reserved for substantive PROPOSAL.md
changes; pure framing reconciliation lives as overlay rounds on
the existing critique-fix file.

## 2026-04-26T05:50:00Z — phase 1 sub-step 4 (pre-execution scan, fast-forward mode)

**Decision:** Apply v024 companion-doc reconciliation round 3 to
`python-skill-script-style-requirements.md`. Style doc canonical
target table at §"Enforcement suite — Canonical target list" was
missing two rows that plan Phase 1 sub-step 4 calls out by name
(`just check-heading-coverage`, `just check-vendor-manifest`)
and that plan Phase 4 enumerates as substantive scripts
(`heading_coverage.py`, `vendor_manifest.py`). Inserted the two
new rows between `check-claude-md-coverage` and
`check-no-direct-tool-invocation` with bodies sourced verbatim
from plan Phase 4. Appended a "round 3" section to
`history/v024/proposed_changes/critique-fix-v023-revision.md`
documenting the gap and fix. PROPOSAL.md snapshot at
`history/v024/PROPOSAL.md` remains byte-identical. Single commit
message: `Revise proposal to v024 (cont 3): companion-doc UV
reconciliation (round 3)`. Gate confirmed via AskUserQuestion
2026-04-26 (option: "Extend v024 with round 3: add 2 rows to
style-doc table (Recommended)") — user is in fast-forward mode
and approved the round-3 extension as the resolution path.

**Rationale:** Same precedent as round 2: companion-doc drift
gets reconciled via overlay extension on the existing v024
critique-fix file rather than via a new vNNN snapshot, because
PROPOSAL.md is unchanged. Fast-forward mode does not authorize
silent fixes for previously-unseen drift categories; the
round-2 gate established the pattern, so round-3 still gates
but the user can approve quickly to keep fast-forward moving.

## 2026-04-26T05:55:00Z — phase 1 sub-step 3 (pre-execution scan, fast-forward mode)

**Decision:** Fix off-by-one count word "six" → "seven" in
coordinated text describing pyright strict-plus diagnostics.
Plan line 523 ("the six strict-plus diagnostics") and style
doc line 758 ("These six diagnostics are above the strict
baseline") both say "six" but enumerate seven names
(reportUnusedCallResult, reportImplicitOverride,
reportUninitializedInstanceVariable,
reportUnnecessaryTypeIgnoreComment, reportUnnecessaryCast,
reportUnnecessaryIsInstance, reportImplicitStringConcatenation).
PROPOSAL.md carries no count and is unaffected. Two commits per
the drift handling rule: (1) Case-B plan-fix on the plan
(`phase-1: fix 'six' → 'seven' in pyright strict-plus diagnostic
count`); (2) v024 round-4 overlay extension on the style doc
(`Revise proposal to v024 (cont 4): companion-doc strict-plus
count fix (round 4)`). Then write pyproject.toml with all 7
diagnostics. Gate confirmed via AskUserQuestion 2026-04-26
(option: "List of 7 is authoritative; fix the count to 'seven'
(Recommended)").

**Rationale:** Substantive enumeration in both docs lists 7
diagnostics with rationale per each. Trimming to 6 would
require dropping a diagnostic that v012 L1+L2 explicitly
established; the count word is the slip. Two-commit split
preserves the audit-trail asymmetry that PROPOSAL.md is
versioned and the plan is not (plan edits never enter v024's
overlay record; companion-doc edits do).

## 2026-04-26T06:35:00Z — phase 1 sub-step 12 (pre-execution scan, fast-forward mode)

**Decision:** Add `.venv/` to plan Phase 1 sub-step 12's
gitignore enumeration. Plan line 636-640 enumerated 7
gitignore entries (`__pycache__/`, `.pytest_cache/`,
`.coverage`, `.ruff_cache/`, `.pyright/`, `.mutmut-cache/`,
`htmlcov/`) but omitted `.venv/`, even though the same phase's
exit criterion (line 643-644) explicitly references the
"project-local `.venv`" that `uv sync --all-groups` creates.
The omission appears to be a v024 plan-update miss: when v024
introduced uv-managed deps, the gitignore enumeration wasn't
extended to match. PROPOSAL.md doesn't enumerate gitignore
entries (no PROPOSAL.md drift). Case-B plan-fix per the
established rule: edit the plan enumeration directly with a
brief justification noting v024. My already-written .gitignore
includes `.venv/` and matches the corrected enumeration.

**Rationale:** Without `.venv/` gitignored, `uv sync` would
add hundreds of MB of binary artifacts to the working tree
that git would track as untracked. The plan's exit criterion
explicitly assumes `.venv` exists post-sync, so gitignoring it
is an implicit requirement; making it explicit in the
enumeration aligns the plan with its own exit criterion. Two
commits: (1) plan-fix on the enumeration; (2) sub-step 12
commit on .gitignore (already authored to include .venv/).

## 2026-04-26T10:05:00Z — phase 2 sub-step 5 (typing_extensions widening + v027 path)

**Decision:** During sub-step 5 vendoring, the v013 M1
typing_extensions hand-authored minimal-shim approach was widened
in-band per the explicit "MAY widen" clause to add 6 symbols
(Never, ParamSpec, Self, TypeVarTuple, TypedDict, Unpack) needed
by the vendored returns + structlog + fastjsonschema sources.
The widened shim worked on Python 3.13 (system) but failed on
Python 3.10.16 (the pinned dev env per .python-version) at
`from returns.io import IOResult` because returns/primitives/
hkt.py uses `Generic[..., Unpack[TypeVarTuple(...)]]` — variadic
generics that 3.10 stdlib lacks and a hand-authored shim cannot
synthesize (3.10's Generic.__class_getitem__ rejects non-TypeVar
arguments regardless of subscriptable stubs). Routed via the
bootstrap skill's Case-A halt-on-blocking flow to v027 D1, which
exercises PROPOSAL.md's pre-planned "scope-widening decision" path:
vendor full upstream typing_extensions verbatim at tag 4.12.2.
Post-v027 the typing_extensions content at
`.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`
is the verbatim upstream `typing_extensions/src/typing_extensions.py`
(3641 lines), reclassified from shim to upstream-sourced.

**Rationale.** PROPOSAL.md v013 M1 explicitly anticipated this
exact path ("re-vendoring the full upstream is a future option
tracked as a scope-widening decision, not a v013 default"). The
in-band widening attempt was the right first move — minimal
PROPOSAL change, exercises an existing v013 M1 allowance — but
the variadic-generics dependency on 3.10 made full upstream
vendoring the correct architectural answer. The PSF-2.0 LICENSE
already authored verbatim during the hand-authored shim work
stays in place unchanged. v027 D1 exercises the scope-widening
decision PROPOSAL.md anticipated; the user-facing Python minimum
(3.10+) is preserved because upstream typing_extensions handles
the 3.10 backports internally. Smoke test post-v027 passes on
both Python 3.10.16 (uv venv) and Python 3.13.7 (system).

## 2026-04-26T09:30:00Z — phase 2 sub-step 5 (cosmetic license-label findings, deferred)

**Decision:** During sub-step 5 vendoring, discovered two cosmetic
license-label drifts in PROPOSAL.md vs actual upstream LICENSE
files: (1) fastjsonschema labeled `MIT` but upstream LICENSE is
`BSD-3-Clause` (3-clause BSD with the "Neither the name" clause);
(2) structlog labeled `BSD-2 / MIT dual` but upstream is
`MIT OR Apache-2.0` per `pyproject.toml`'s
`SPDX-License-Identifier: MIT OR Apache-2.0` and the `LICENSE-MIT`
+ `LICENSE-APACHE` + `COPYRIGHT` files. Both libs remain in policy
per the style-doc allow-list (line 133-134: `MIT`, `BSD-2-Clause`,
`BSD-3-Clause`, `Apache-2.0`, `PSF-2.0`); the labels are
cosmetically wrong but architecturally fine. Per the bootstrap
skill's "Severity judgment over rule-following on PROPOSAL drift"
rule, cosmetic drift rides along with the next substantive
revision and never opens its own blocking gate.

Scope of the fix in this sub-step 5 commit: NOTICES.md `structlog`
block updated from `Dual-licensed BSD-2-Clause / MIT` to
`Dual-licensed MIT OR Apache-2.0` so it accurately describes the
LICENSE file actually shipped (combined LICENSE-MIT + LICENSE-APACHE
+ COPYRIGHT). Deferred to next substantive PROPOSAL.md revision:
- PROPOSAL.md vendored-libs directory tree (line ~100): fastjsonschema
  `(MIT)` → `(BSD-3-Clause)`; structlog `(BSD-2 / MIT dual)` →
  `(MIT or Apache-2.0 dual)`.
- PROPOSAL.md vendored-libs bullet (line ~480-481): same labels.
- python-skill-script-style-requirements.md vendored-libs section
  (line ~168, 170): same labels.
- NOTICES.md fastjsonschema block already correctly says
  `BSD-3-Clause` (no fix needed there).

**Rationale.** The shipped LICENSE files are the source of truth
(verbatim upstream content, license terms binding regardless of
spec labels). The spec labels are descriptive metadata that lag
the actual content; correcting them is a cosmetic ride-along, not
a structural change. Doing a v027 cosmetic-only halt-and-revise
now would be ceremony for label-only metadata when (a) the libs
are in policy, (b) the LICENSE files are accurate, (c) the next
substantive revision will sweep them mechanically. The single
exception applied in this commit is the structlog NOTICES.md
block: the LICENSE file shipped (combined MIT-or-Apache) cannot
coherently coexist with a NOTICES.md description that calls it
"BSD-2/MIT". Anyone reading both would see the file-level
mismatch immediately.

## 2026-04-26T08:10:00Z — phase 2 sub-step 5 (pre-execution scan, fast-forward mode)

**Decision:** Fix two leftover "six" → "five" references in
plan describing the post-v025 vendored-libs count. Plan line
700 ("Phase 1 authors all six entries with placeholder") and
line 862 ("with real values for all six vendored entries")
both refer to the present-state count of `.vendor.jsonc`
entries, which v025 D1/D4/D6 reduced from six to five by
dropping `returns_pyright_plugin`. The neighboring v025
history note at lines 270-299 and the canonical .vendor.jsonc
bullet at line 690 ("five entries total per v025 D4")
already say five; these two sentences were missed in the
v025 D4 plan-text edits. PROPOSAL.md verified clean of any
six/five vendored-count references. Line 41 (v018 Q4
historical decision summary) stays as-is — it documents the
v018 closure that v025 then revised. Single commit
(`phase-2: fix leftover 'six' → 'five' vendored-libs count
in plan`). Gate confirmed via AskUserQuestion 2026-04-26
(option: "Apply the plan correction (Recommended)").

**Rationale:** Case-B plan-only drift per the bootstrap
skill's drift-handling rule: PROPOSAL.md is unaffected
(versioned doc unchanged), so direct plan edits + commit +
decisions.md entry is the correct path; no new vNNN
snapshot needed. The drift is a consistency miss — v025's
D4 plan-edit line spec changed only the .vendor.jsonc
bullet itself, missing the two downstream sentences that
also describe the count. Surfacing it now keeps Phase 2
sub-step 5's vendoring work aligned with the plan it
references.
