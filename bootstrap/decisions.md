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

## 2026-04-26T11:00:00Z — phase 2 sub-step 6 (Phase-2 exit-criterion correction)

**Decision:** Remove the three dev-tooling-backed checks
(`check-wrapper-shape`, `check-main-guard`,
`check-claude-md-coverage`) from plan Phase 2's exit-criterion
sentence (lines 1020-1031). Replace with: `ruff check` only, plus
an explicit pointer at Phase 3's existing deferral list ("every
target backed by a Phase-4 `dev-tooling/checks/*.py` script"),
plus a manual file-existence verification block (CLAUDE.md
coverage, `.vendor.jsonc` placeholder absence, `__all__`
declaration in every `livespec/**` module). Plugin-loading smoke
check stays verbatim. Single Edit on Phase 2's exit-criterion
paragraph; no other plan sections needed amendment (Phase 3's
deferral already correctly includes these targets; Phase 4's
authoring list owns the backing scripts; Phase 5's exit criterion
already implies full `just check` passes once the scripts land).
PROPOSAL.md verified unaffected — it references
`check-wrapper-shape` and `check-claude-md-coverage` only in
passing (lines 418, 3796), not in any phase-exit-criterion
context. Gate confirmed via AskUserQuestion 2026-04-26 (option:
"Apply the plan correction (Recommended)").

**Rationale:** Plan-internal contradiction discovered during
Phase 2 sub-step 6 work. Phase 2 line 1020 listed three checks as
exit gates whose backing scripts (`wrapper_shape.py`,
`main_guard.py`, `claude_md_coverage.py`) are authored at Phase 4
(plan line 1361, 1369). Phase 3 line 1339-1346 explicitly defers
"every target backed by a Phase-4 `dev-tooling/checks/*.py`
script" to Phase 5's exit. The Phase 2 → Phase 3 advance gate
would have failed because `python3 dev-tooling/checks/<name>.py`
returns no-such-file: `dev-tooling/` does not exist as of this
sub-step. Case-B plan-only fix per the bootstrap skill's
drift-handling rule (PROPOSAL.md unaffected; plan is unversioned
throwaway scaffolding deleted at Phase 11). The corrected exit
criterion is enforceable today (`ruff check` is the only
non-deferred mechanical check at Phase 2; plugin-loading smoke
check is manual; file-existence verification is `find`/`ls`).

## 2026-04-26T08:33:35Z — phase 2 sub-step 9 (pyproject.toml ruff config fix at exit-criterion check)

**Decision:** Add the missing ruff configuration to pyproject.toml
that the spec already mandates: (1) `[tool.ruff].extend-exclude =
["**/_vendor/**", "**/__pycache__/**"]` per
`python-skill-script-style-requirements.md` line 294-296 ("`_vendor/`
is **excluded** from livespec's own style rules, type checking
strictness, coverage measurement, and CLAUDE.md coverage
enforcement"); (2) `[tool.ruff.lint.per-file-ignores]` for
`.claude-plugin/scripts/bin/*.py = ["I001", "E402", "E501"]` per
the wrapper-shape contract (style doc lines 1664-1668: each wrapper
MUST be the 6-statement shape `shebang → docstring → from _bootstrap
import bootstrap → bootstrap() → from livespec.<...> import main →
raise SystemExit(main())` — the post-`bootstrap()` import is
structurally I001/E402, and the docstring template overflows 100
chars for longer module names triggering E501); (3) per-file-ignores
for `.claude-plugin/scripts/bin/_bootstrap.py = ["UP036"]` per the
bootstrap mechanism (style doc lines 1697-1700: the `if
sys.version_info < (3, 10): raise SystemExit(127)` check is the
canonical bootstrap-time version assertion even though
`target-version = "py310"`). Discovered during the Phase 2 exit-
criterion check at sub-step 9: `uv run ruff check .` returned 1151
errors (1132 in `_vendor/`, 19 in `bin/*.py`); after fix, returns
"All checks passed!". Sub-step 6's STATUS-asserted "ruff clean"
was scoped to `livespec/` only, never validated against the broader
repo-wide scope mandated by the exit criterion. Fix gated via
AskUserQuestion 2026-04-26 (option: "Hold here; add sub-step 9 to
fix pyproject.toml (Recommended)").

**Rationale:** Implementation drift in pyproject.toml — Phase 1
sub-step 3 authored the ruff config without the spec-mandated
`_vendor` exclude or wrapper-shape per-file-ignores. The spec is
correct (style doc explicitly mandates both); pyproject.toml just
missed them. Not PROPOSAL.md drift (no PROPOSAL change needed) and
not plan drift (plan is silent on per-file-ignore specifics —
appropriately, per the "specify architecture, not mechanism"
principle). Pure implementation bug fix; no v028 PROPOSAL
revision and no plan edit required. The companion-doc precedent
for "spec-says-X-but-config-says-Y" is to fix the config to match
the spec, not to add overlay extensions to the spec.

**Side observation (deferred for sweep at next substantive PROPOSAL
revision).** `python-skill-script-style-requirements.md` line 1820
(`check-vendor-manifest` row of the canonical-target table) carries
stale wording: "the `shim: true` flag is present on `typing_extensions`
and absent on every other entry". Post-v026 D1 + v027 D1
reclassifications, the shim is `jsoncomment` (NOT `typing_extensions`).
Cosmetic label drift only; the `check-vendor-manifest` script
authored at Phase 4 will validate against `.vendor.jsonc`'s actual
shape, not against this stale table row. Rides along with the next
substantive PROPOSAL revision per the bootstrap skill's "Severity
judgment over rule-following on PROPOSAL drift" rule and the
established companion-doc-overlay precedent (v024 round 1-4).

## 2026-04-26T08:59:00Z — phase 3 sub-step 3 (companion-doc gap, deferred)

**Decision:** Author `livespec/context.py` per the plan's explicit
directive (line 1059-1071), which includes `template_name: str` on
`DoctorContext`. Note the companion-doc gap on
`python-skill-script-style-requirements.md` §"Context dataclasses"
(line 422-430): the canonical `DoctorContext` code snippet has 8
fields and is missing `template_name`. PROPOSAL.md line 2574 and
plan Phase 3 sub-step 3 both carry the field, so the implementation
matches PROPOSAL/plan; only the style-doc snippet lags. Defer the
style-doc reconciliation as a companion-doc overlay item to ride
along with the next substantive PROPOSAL revision (per the
established precedent: v024 rounds 1-4 and the 2026-04-26T08:33:35Z
side-observation pattern). No vNNN snapshot opened for this gap
alone.

**Rationale:** Style-doc snippet drift is documentation-only;
PROPOSAL is correct, the plan is correct, the implementation is
correct. The "Severity judgment over rule-following on PROPOSAL
drift" feedback rule applies: cosmetic drift never blocks on its
own and rides along with whatever revision happens for substantive
reasons. Opening a v028 overlay round purely to add one missing
field to a code snippet would be ceremony for documentation lag
that the next real revision will sweep mechanically. Implementation
already includes the field; downstream Phase 3 work consuming
`ctx.template_name` (run_static.py orchestrator at sub-step 18) is
unblocked.

## 2026-04-26T09:07:28Z — phase 3 sub-step 4 (pyproject.toml ruff TRY003 per-file-ignore)

**Decision:** Add per-file-ignore for `TRY003` (tryceratops:
"Avoid specifying long messages outside the exception class")
scoped to `.claude-plugin/scripts/livespec/io/**.py`. Discovered
during Phase 3 sub-step 4 while authoring `livespec/io/fs.py`:
`raise PreconditionError(f"file not found: {path}")` and 14 sibling
raise-sites all triggered TRY003 because the messages embed runtime
context as f-strings rather than living inside per-context
exception subclasses. Same precedent as sub-step 9's pyproject.toml
ruff config fix at the Phase 2 exit-criterion check: pure
implementation bug fix in pyproject.toml (no PROPOSAL revision and
no plan edit required) when the spec mandates a configuration that
the initial pyproject.toml authoring at Phase 1 sub-step 3 missed.

**Rationale:** v013 M5 mandates a flat one-level `LivespecError`
hierarchy: `UsageError`, `PreconditionError`, `ValidationError`,
`GitUnavailableError`, `PermissionDeniedError`, `ToolMissingError`
all subclass `LivespecError` directly; further subclassing is
forbidden (`check-no-inheritance` enforces direct-parent
allowlist). `LivespecError` raise-sites are restricted to
`livespec/io/**` (`check-no-raise-outside-io`). Domain-meaningful
messages MUST embed runtime context (which path/value/operation
failed) so the operator can act on them, but with the flat
hierarchy mandated by M5, that context can ONLY be embedded at
the raise-site as an f-string argument to the existing
`PreconditionError` / `PermissionDeniedError` / etc. constructors
— there is no per-context subclass to put the message template
in. TRY003 wants raise-sites to look like `raise FileNotFound(path)`
where `FileNotFound` embeds the message template; v013 M5 forbids
authoring such a class. The two rules are architecturally
incompatible at the io/ raise-site location, so per-file-ignoring
TRY003 in that exact subtree is the minimal reconciliation. The
TRY family's other rules (TRY002, TRY004, TRY200, TRY201, TRY300,
TRY301, TRY400, TRY401) remain active everywhere — only TRY003 is
ignored, and only in the one subtree where it conflicts. The
pyproject.toml comment block documents the rationale for future
readers per the established companion-doc-overlay precedent.

## 2026-04-26T09:23:07Z — phase 3 sub-step 11 (validate/ make_validator factory shape)

**Decision:** The `make_validator()` factory in
`livespec/validate/<name>.py` accepts a pre-compiled fastjsonschema
validator (typed `Callable[[dict[str, Any]], Result[dict[str,
Any], ValidationError]]`) as its keyword-only argument, NOT the
schema dict. The compile happens upstream in
`commands/<cmd>.py` or `doctor/run_static.py` via
`livespec.io.fastjsonschema_facade.compile_schema`; the validate/
closure captures the compiled validator and adds dataclass
construction on top.

**Rationale:** The style doc has an internal contradiction
between two of its sections:

- §"Skill layout" lines 343-352 state "Validators invoke
  `livespec.io.fastjsonschema_facade.compile_schema` for the
  actual compile" — implying validate/ imports from io/.
- §"Import-Linter contracts (minimum configuration)" lines
  715-727 declare a `forbidden` contract on
  `livespec.parse, livespec.validate` that lists `livespec.io`
  as a forbidden import target.

The two rules cannot both be satisfied if make_validator imports
compile_schema. The CLAUDE.md hint at
`livespec/validate/CLAUDE.md` describes the factory as "with the
fastjsonschema-compiled validator captured" — pre-compiled, not
compiled-internally. Choosing the import-linter-compatible
interpretation (CLAUDE.md-aligned): validate/ stays strictly pure,
imports zero io modules, and the compiled validator is passed in
by the caller. The contradicting style-doc text at lines 346-348
is a companion-doc gap to be reconciled at the next substantive
PROPOSAL revision via overlay extension on the appropriate
critique-fix file (precedent: v024 rounds 1-4); the implementation
matches the import-linter contract and the CLAUDE.md hint, both of
which align with the pure-validate architectural intent.

## 2026-04-26T20:18:52Z — phase 3 sub-step 23 (Phase-3 exit-criterion correction)

**Decision:** Drop `just check-wrapper-shape`,
`just check-main-guard`, and `just check-schema-dataclass-pairing`
from plan Phase 3's exit-criterion sentence (lines 1358-1360).
The corrected sentence keeps `just check-lint` (the only
tool-backed gate available at Phase 3) plus the manual
tmp_path round-trip test (main + sub-spec routing per v019 Q1
+ v020 Q3) and adds an explicit pointer at Phase 3's existing
deferral list (lines 1397-1405) noting the dropped checks are
deferred to Phase 5. PROPOSAL.md verified unaffected — it
references `check-wrapper-shape` and `check-schema-dataclass-pairing`
only in passing (lines 418, 3607), not in any phase-exit-criterion
context. Single Edit on Phase 3's exit-criterion paragraph; no
other plan sections needed amendment. Gate confirmed via
AskUserQuestion 2026-04-26 (option: "Apply the plan correction
(Recommended)").

**Rationale:** Plan-internal contradiction discovered at the
Phase 3 → Phase 4 advance gate. Phase 3 line 1358 listed three
checks as exit gates whose backing scripts (`wrapper_shape.py`,
`main_guard.py`, `schema_dataclass_pairing.py`) are authored at
Phase 4 (plan §"Phase 4"). Phase 3 line 1397-1405 explicitly
defers "every target backed by a Phase-4 `dev-tooling/checks/*.py`
script" to Phase 5's exit. The Phase 3 → Phase 4 advance gate
would have failed because `python3 dev-tooling/checks/<name>.py`
returns no-such-file: `dev-tooling/` does not exist as of this
sub-step. Case-B plan-only fix per the bootstrap skill's
drift-handling rule (PROPOSAL.md unaffected; plan is unversioned
throwaway scaffolding deleted at Phase 11). Same shape as the
Phase 2 sub-step 6 fix (decisions.md 2026-04-26T11:00:00Z) which
made the same correction for Phase 2's exit criterion. The
corrected exit criterion is enforceable today (`ruff check`
clean) plus the tmp_path round-trip exercise (sub-step 23
itself).

## 2026-04-26T20:25:13Z — phase 3 sub-step 23 (revise.py path-resolution bugfix at exit-criterion check)

**Decision:** Fix a path-resolution bug in
`livespec/commands/revise.py::_apply_resulting_files`. The helper
was using `spec_target.parent / rf.path` as the base for
resolving `resulting_files[].path` — which works coincidentally
for the main spec tree (where `spec_target.parent == project_root`
under the v1 built-in livespec template) but produces a doubled
path for sub-spec trees (where `spec_target.parent ==
project_root/SPECIFICATION/templates`, and the prepended
`SPECIFICATION/templates/<name>/<file>` rf.path produces
`project_root/SPECIFICATION/templates/SPECIFICATION/templates/<name>/<file>`).
Fix: thread `project_root` through `_process_with_vnnn` →
`_shape_history` → `_apply_resulting_files`, and resolve via
`project_root / rf.path` directly. Per the prompt convention
(prompts/revise.md), `resulting_files[].path` values are
project-root-relative regardless of `--spec-target`.

**Rationale:** Implementation drift surfaced by the v020 Q3
sub-spec routing smoke-cycle test at the Phase 3 exit-criterion
check (sub-step 23 itself). Same precedent as decisions.md
2026-04-26T08:33:35Z (pyproject.toml ruff config fix at the
Phase 2 exit-criterion check): pure implementation bug fix; no
PROPOSAL revision required; no plan edit required. The bug was
masked by the main-tree happy path because, for the v1 built-in
livespec template, `spec_target.parent` happens to equal
`project_root` — the bug is only visible when `--spec-target`
points at a sub-spec tree. Test fixture under
`tmp/bootstrap/phase3-test/` confirms the fix: 4 successful
round-trips (seed → propose-change/main → revise/main →
propose-change/sub-spec → revise/sub-spec), no misdirected files
under `SPECIFICATION/templates/SPECIFICATION/...`. The earlier
Phase 3 sub-step 16 commit's `_apply_resulting_files`
implementation passed ruff but contained the latent bug; only the
Phase 3 sub-step 23 integration test surfaces the divergence
between main-tree and sub-spec-tree resolution semantics — the
intended use of the integration test per plan line 1390-1395
("Catches `--spec-target` sub-spec routing bugs at the Phase 3
boundary, where recovery is imperative-landing (cheap), instead
of Phase 7's dogfood boundary where recovery would require the
broken governed loop.").

## 2026-04-27T22:04:27Z — phase 4 sub-step 4 (supervisor refactor — inline _dispatch into main())

**Decision:** Refactor the 5 `livespec/commands/*.py` supervisors
+ `livespec/doctor/run_static.py` to inline their `_dispatch`
helper into `main()` directly. The style doc's `sys.stdout.write`
exemption (lines 1474-1481) is per-supervisor "the function named
`main` at module top-level", explicitly NOT per-helper inside
commands/**. My Phase 3 supervisor pattern split the bug-catcher
(in `main()`) from the dispatch logic (in `_dispatch()`), placing
`sys.stdout.write` calls in a non-exempted helper. The refactor
folds them back into `main()`, so the exemption applies.

Surfaced by Phase 4 sub-step 4's authoring of
`dev-tooling/checks/no_write_direct.py`, which detected 8
violations across the 6 affected files. After the refactor, the
check passes against the shipped repo.

Side outcome: `no_write_direct.py` itself originally inherited
from `ast.NodeVisitor`, which the no_inheritance check correctly
flags (v013 M5 direct-parent allowlist excludes `ast.NodeVisitor`).
Refactored to a plain recursive `_walk` function that threads the
`inside_main` boolean through the AST traversal — no class
inheritance.

**Rationale:** Same precedent as decisions.md 2026-04-26T20:25:13Z
(revise.py path-resolution bug surfaced by Phase 3 exit-criterion
smoke): Phase 3 implementation drift caught by Phase 4 enforcement
work. Pure code refactor; no PROPOSAL revision; no plan edit. The
inlined supervisor is structurally identical to the prior
`main() → _dispatch()` split — same try/except bug-catcher, same
match dispatch, same return values. The split was an unnecessary
helper introduction that conflicted with a pre-existing style-doc
rule. Phase 3 exit-criterion tmp_path round-trip re-run
post-refactor confirms identical end-to-end behavior (seed →
propose-change → revise → propose-change-subspec → revise-subspec
→ resolve_template, all exit 0 with correct file shaping and
stdout output).

## 2026-04-26T21:32:08Z — phase 4 sub-step 2 (pyproject.toml fixes surfaced by first pytest run)

**Decision:** Two pyproject.toml fixes landed alongside the
first dev-tooling script + paired test:

1. **Add `tests/**.py = ["S101"]` per-file-ignore.** S101
   (flake8-bandit "use of `assert` detected") flags every
   bare `assert` in tests, but pytest's idiomatic pattern is
   bare `assert`. The S discipline applies to shipped code,
   not test-time assertions. Per-file-ignore scoped to
   `tests/**.py`.
2. **Remove `--icdiff` from `[tool.pytest.ini_options].addopts`.**
   pytest-icdiff registers as the `icdiff` pytest11 plugin via
   entry_points.txt and produces nicer diffs by default — it
   does NOT add a `--icdiff` flag. The plugin's only two flags
   are `--icdiff-cols` and `--icdiff-show-all-spaces` for
   tuning. The `--icdiff` line in addopts caused
   `pytest: error: unrecognized arguments: --icdiff` on every
   pytest run. Phase 1 pyproject.toml authoring bug surfaced by
   the first actual pytest invocation in Phase 4 sub-step 2.

**Rationale:** Same precedent as decisions.md 2026-04-26T08:33:35Z
(pyproject.toml ruff config fix at Phase 2 exit-criterion) and
2026-04-26T09:07:28Z (TRY003 per-file-ignore at Phase 3 sub-step
4): pure pyproject.toml bug fixes; no PROPOSAL revision required;
no plan edit required. Both fixes surfaced when Phase 4's first
script test attempted to actually run pytest, exercising config
that Phase 1's authoring had not yet been validated against. The
S101 per-file-ignore matches the standard pytest convention
across the Python ecosystem; the `--icdiff` removal aligns the
config with pytest-icdiff's actual API surface.

## 2026-04-26T21:23:48Z — phase 4 sub-step 1 (plan vendor_manifest description fix)

**Decision:** Edit plan line 1443-1444's `vendor_manifest.py`
description to swap `typing_extensions` → `jsoncomment` as the
shim entry (post-v026 D1 + v027 D1 reclassifications). Old text:
"the `shim: true` flag is present on `typing_extensions` and
absent on every other entry." Corrected: "the `shim: true` flag
is present on `jsoncomment` (the v026 D1 hand-authored shim) and
absent on every other entry (post-v027 D1 `typing_extensions` is
upstream-sourced, NOT a shim)." Same shape as the style-doc line
1820 drift already deferred at decisions.md 2026-04-26T08:33:35Z.
Case-B plan-only fix per the bootstrap skill's drift-handling rule
(PROPOSAL.md unaffected — its v026/v027 reclassifications already
land jsoncomment as the shim and typing_extensions as
upstream-sourced; actual `.vendor.jsonc` correctly carries
`"shim": true` on jsoncomment). Gate confirmed via AskUserQuestion
2026-04-26 (option: "Apply the plan correction (Recommended)").

**Rationale:** Sub-step 1 of Phase 4 is the start of the
dev-tooling enforcement scripts. The first script that consumes
this plan-text guidance is `vendor_manifest.py` itself: if the
executor implements the validator per the plan's literal stale
text, the script would VALIDATE THAT typing_extensions has
`shim: true`, which is wrong post-v027 D1 and would fail against
the actual `.vendor.jsonc`. Surfacing and fixing the drift now
unblocks Phase 4 implementation cleanly. The style-doc line 1820
companion-doc drift remains deferred (per the established
companion-doc-overlay precedent) — a separate companion-doc
overlay round can sweep it whenever the next substantive
PROPOSAL revision lands.

## 2026-04-27T00:26:40Z — phase 4 sub-step 15

**Decision:** Apply Case-B direct-fix to the style-doc canonical
target list line 1884 (`just check-public-api-result-typed`)
rather than halt-and-revise to v030. Expand the line to capture
four implementation-level realities surfaced while authoring
`dev-tooling/checks/public_api_result_typed.py`: (1) `@impure_safe`
/ `@safe` decorator recognition (the source-level annotation
shows the inner type but the runtime return is the wrapped
carrier); (2) four additional name-based factory exemptions
(`make_validator` in `validate/**`, `get_logger` in
`io/structlog_facade.py`, `compile_schema` in
`io/fastjsonschema_facade.py`, `rop_pipeline` in `types.py`); (3)
`build_parser` exemption widened to include `doctor/run_static.py`
(matching the supervisor-discipline pattern that already covers
both scopes); (4) package-private helper modules (`_*.py` filename)
are skipped — applies to `commands/_seed_helpers.py` and
`commands/_revise_helpers.py` introduced at sub-step 14a/14b.
Initial open-issues entry at `2026-04-27T00:26:40Z` mis-classified
this as PROPOSAL.md drift; superseded with a backref pointer
since the actual divergence is purely in the style doc and
PROPOSAL.md line 3503's parenthetical describes the public-API
detection mechanism (still `__all__`-based) rather than the
exemption set.

**Rationale:** v029 D1's revision file explicitly codified the
convention: "style doc edits ride freely with the implementation
— not gated by halt-and-revise per the established style-doc-
drift convention". That convention applied at sub-step 13 when
the new ROP pipeline shape rule was added to the style doc
without a halt-and-revise (the v029 bump was for an unrelated
PROPOSAL.md directory-listing drift). The same convention applies
here: the canonical target list rule wording is style-doc text,
not PROPOSAL.md text. Halt-and-revise to v030 with a byte-
identical PROPOSAL.md snapshot would be ceremony without spec
movement. User confirmed via AskUserQuestion gate after pushback
on my initial Case-A recommendation.

## 2026-04-27T02:26:43Z — phase 4 sub-step 17

**Decision:** Land `dev-tooling/checks/newtype_domain_primitives.py` +
paired unit tests in sub-step 17 WITHOUT the standard
`test_main_passes_against_real_repo` test. Defer the
implementation-drift cleanup (23 NewType violations across 9 files
in `livespec/**`) to a dedicated Phase-4-exit cleanup sub-step.
Document the deferred scope in the test file's module docstring and
in this decisions.md entry so the cleanup can be picked up cleanly.

The 23 violations as of commit `ed77546`:

| File | Field/Param | Current | Expected |
|---|---|---|---|
| `commands/_revise_helpers.py` line 67 | `template` | `str` | `TemplateName` |
| `commands/_revise_helpers.py` line 143 | `author_llm` | `str` | `Author` |
| `commands/propose_change.py` lines 161, 183, 247, 330, 340, 360, 384 | `topic` | `str` | `TopicSlug` |
| `commands/propose_change.py` lines 248, 341, 361, 385 | `author` | `str` | `Author` |
| `commands/propose_change.py` line 330 | `template` | `str` | `TemplateName` |
| `commands/resolve_template.py` line 239 | `template` | `str` | `TemplateName` |
| `commands/revise.py` lines 114, 300 | `author_llm` | `str` | `Author` |
| `doctor/run_static.py` lines 141, 148 | `template` | `str` | `TemplateName` |
| `doctor/run_static.py` line 415 | `spec_root` | `Path` | `SpecRoot` |
| `io/fastjsonschema_facade.py` line 84 | `schema_id` | `str` | `SchemaId` |
| `schemas/dataclasses/finding.py` line 44 | `spec_root` | `str` | `SpecRoot` |
| `schemas/dataclasses/revision_front_matter.py` line 31 | `author_human` | `str` | `Author` |
| `schemas/dataclasses/template_config.py` line 36 | `spec_root` | `str` | `SpecRoot` |

**Rationale:** Authoring the check correctly catches real
implementation drift — that IS the value of the check. Fixing
all 23 sites inline within sub-step 17 would conflate "land the
enforcement script" with "do a 9-file repo-wide NewType refactor"
in one commit, obscuring the audit trail. The plan's Phase 4 exit
criterion (`just check` passes against the current code base)
catches the violations naturally; a dedicated cleanup sub-step
(or roll-in alongside the next refactor that touches these files)
lands the fixes with a focused commit message. The
`test_main_passes_against_real_repo` omission is documented in
the test file's module docstring with a backref to this entry.

## 2026-04-27T03:23:13Z — phase 4 sub-step 26 (plan exit-criterion drift)

**Decision:** Apply Case-B plan-only correction to Phase 4's
exit criterion. The plan text "`just check` passes against the
current code base" is incompatible with the by-design fact that
several `just check` targets cannot pass at Phase 4 exit:
`check-coverage` (requires Phase 5 test suite to reach 100%),
`check-tests` (requires Phase 5 test infrastructure), `check-types`
(pyright strict against the Phase-2/3 stubs in `livespec/**`,
explicitly deferred by Phase 3), `e2e-test-claude-code-mock`
(requires `tests/e2e/`, Phase 5 skeleton + Phase 9 content), and
`check-prompts` (requires `tests/prompts/`, Phase 5 skeleton +
Phase 7 content). Phase 3 already enumerates its deferred
targets explicitly; Phase 4's exit criterion is now updated to
mirror that pattern, carrying forward the still-deferred targets
and explicitly enumerating the active-at-Phase-4 targets that
sub-step 26 must make pass: `check-lint`, `check-format`,
`check-complexity`, `check-imports-architecture`, `check-tools`,
and every `dev-tooling/checks/*.py`-backed canonical target.

**Rationale:** PROPOSAL.md is unaffected (verified via grep:
PROPOSAL specifies what targets EXIST and what each does, never
when each must pass at which bootstrap-plan phase — phasing is
plan scaffolding only). The drift is entirely within
`brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
Phase 4 §"Exit criterion" (lines 1502-1504). Routed through the
Case-B direct-fix path with explicit user gate confirmation.
The fix mirrors Phase 3's existing deferral pattern (lines
1449-1457) and Phase 5's "now including" enumeration (lines
1577-1583), bringing Phase 4 into alignment with the rest of
the plan's phasing semantics. STATUS.md's prior-session
interpretation ("every canonical-list target green
simultaneously") is now codified in plan text. No companion-doc
or PROPOSAL.md impact; no v030 PROPOSAL bump required.

## 2026-04-27T06:43:45Z — phase 4 sub-step 26 (import-linter contract overlay)

**Decision:** Drop `returns.io` and `pathlib` from the realized
`[tool.importlinter]` `parse-and-validate-are-pure` contract's
`forbidden_modules` list, with explanatory comments in
`pyproject.toml` and a paired implementation-overlay section
appended to
`brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
§"Import-Linter contracts (minimum configuration)". Both forbids
are unenforceable as written by Import-Linter v2:

- `returns.io` — Import-Linter v2 rejects subpackages of external
  packages. The IOResult / IOFailure ban in pure layers is
  enforced at raise-site by `check-no-raise-outside-io`.
- `pathlib` — `livespec.types` defines `SpecRoot = NewType(
  "SpecRoot", Path)`, forcing a runtime pathlib import that
  flows transitively into pure layers via the wire dataclasses
  under `livespec.schemas.dataclasses/`. Importing the `Path`
  class is not I/O; method calls are. The no-I/O-at-runtime
  intent is caught by `check-no-write-direct`,
  `check-supervisor-discipline`, and `check-no-raise-outside-io`,
  which fire on actual misuse rather than on type-only imports.

Five reasonable resolutions were evaluated (drop both with
overlay [chosen]; split `livespec.types` into pure +
Path-dependent halves; defer the entire `check-imports-architecture`
target to Phase 5; PathLike Protocol in pure types; PROPOSAL
revision). The chosen path is the smallest reversible change
that preserves the runtime safety guarantee and lets Phase 5/7
revisit with full context once stub-to-implementation widening
provides better signal for choosing among the IoC patterns.

**Rationale:** Per the style doc's architecture-vs-mechanism
principle (lines 805-808): "the two rules above are the
contract; the TOML is one valid way to express them." When
the TOML cannot express the rule cleanly, alternative
mechanisms (here: AST-level checks) are licensed. PROPOSAL.md
is unaffected (Import-Linter contract module enumeration is
companion-doc material, not PROPOSAL-versioned). The companion-
doc edit follows the v028 D1 / 2026-04-26T08:33:35Z precedent
(style doc edits ride freely with implementation; no PROPOSAL
bump). Verified via `just check-imports-architecture`: both
contracts (`parse-and-validate-are-pure` and
`layered-architecture`) now KEEP cleanly against the current
codebase.

## 2026-04-27T08:50:00Z — phase 5 sub-step 1 (pre-execution scan)

**Decision:** Apply Case-B plan-only correction to align Phase 5's
exit criterion with the Phase 4 → Phase 5 deferral-handoff
convention established by the Phase 4 sub-step 26 cleanup
(decisions.md 2026-04-27T03:23:13Z). Two paired edits to
`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`:

1. **Phase 4 deferral list (lines 1509-1527).** Removed the
   internal contradiction in the `check-types` bullet ("activates
   at Phase 5 alongside the test suite, once livespec/** stubs
   widen toward their Phase-7 implementations" — the widening
   happens at Phase 7, not Phase 5). Restructured each deferred
   target to enumerate its actual reactivation phase: `check-tests`
   and `check-coverage` and `check-prompts` activate at Phase 5;
   `check-types` activates at **Phase 7**; `e2e-test-claude-code-mock`
   activates at **Phase 9**.

2. **Phase 5 exit criterion (lines 1604-1610).** Replaced the
   non-exhaustive "passes end-to-end including <subset>"
   formulation with the explicit Phase 3 / Phase 4 pattern:
   targets active at Phase 5 exit are enumerated; targets still
   deferred at Phase 5 exit (`check-types` to Phase 7,
   `e2e-test-claude-code-mock` to Phase 9) are enumerated
   immediately after.

PROPOSAL.md verified unaffected (grep on `check-types` /
`e2e-test-claude-code-mock` / `Phase 5` / `exit criterion`
returns only descriptive references to what each target does,
never phase-exit-criterion phasing semantics — phasing is plan
scaffolding only). Gate confirmed via AskUserQuestion 2026-04-27
(option: "Apply the plan correction (Recommended)").

**Rationale:** Same precedent as the Phase 2 sub-step 6 fix
(decisions.md 2026-04-26T11:00:00Z), the Phase 3 sub-step 23 fix
(decisions.md 2026-04-26T20:18:52Z), and the Phase 4 sub-step 26
fix (decisions.md 2026-04-27T03:23:13Z): plan-text drift in
phase-exit-criterion phasing semantics gets the lighter Case-B
direct-fix path because PROPOSAL.md doesn't carry phase-exit
phasing (the plan owns phasing, the spec owns target identity
+ behavior). The drift was caught by the bootstrap skill's
mandatory consistency scan at the start of Phase 5 sub-step 1
before any test-suite authoring landed; surfacing and fixing
the drift now keeps Phase 5's actual work aligned against the
plan it references and pre-empts a phase-exit gate failure
that would otherwise surface only at the very end of Phase 5.

## 2026-04-27T09:30:00Z — phase 5 sub-step 3 (pyproject.toml pythonpath fix surfaced by first livespec import test)

**Decision:** Add `pythonpath = [".claude-plugin/scripts",
".claude-plugin/scripts/_vendor"]` to pyproject.toml's
`[tool.pytest.ini_options]`. Discovered during Phase 5 sub-step 3
authoring `tests/livespec/test_init.py`: pytest collection failed
with `ModuleNotFoundError: No module named 'livespec'` because
the wrappers' `_bootstrap.bootstrap()` only manipulates sys.path
at runtime — pytest doesn't go through that path. The wrapper-
coverage tests under `tests/bin/` work without pythonpath because
they stub `sys.modules['_bootstrap']` and `sys.modules['livespec.<>']`
explicitly; everything else needs the same paths the runtime
bootstrap installs.

Same precedent as decisions.md 2026-04-26T08:33:35Z (ruff config
fix at Phase 2 exit), 2026-04-26T09:07:28Z (TRY003 per-file-ignore),
2026-04-26T21:32:08Z (S101 + --icdiff fixes at first pytest run):
pure pyproject.toml bug fix (no PROPOSAL revision and no plan edit
required) — Phase 1 sub-step 3's pyproject.toml authoring missed
configuration the spec implicitly requires, surfaced by the first
sub-step that exercises it.

**Rationale:** PROPOSAL.md §"Vendoring discipline" + the wrapper
contract together imply that `livespec` and the vendored libs are
on sys.path during execution. Pytest collection IS execution.
Adding the pythonpath aligns pytest's import mechanism with the
runtime mechanism `_bootstrap.bootstrap()` provides, without
requiring tests to redundantly do their own sys.path manipulation
(which would be duplicated boilerplate across every tests/livespec/**
test file). The bin-coverage stubbing pattern stays as-is — those
tests verify the wrapper's plumbing without needing the real
`livespec` package on sys.path.

## 2026-04-27T08:50:00Z — phase 5 sub-step 1 (pre-execution scan) — cascading-scan follow-up

**Cascading-scan follow-up (same finding).** Post-commit
cascading-impact scan surfaced two more plan-text references to
`check-types` as a Phase-5 gate that needed to align with the
Phase 7 reactivation:

- Phase 2 exit criterion (line ~1125): "`check-types` is a
  Phase-5 gate" → "Phase-7 gate, once `livespec/**` stubs widen
  toward their full implementations".
- Phase 3 deferral list (lines ~1449-1457): full restructure to
  enumerate per-target reactivation phases (Phase 4/5 for
  dev-tooling-backed targets and the test-suite gates;
  **Phase 7** for `check-types`; **Phase 9** for
  `e2e-test-claude-code-mock`).

Both edits are part of the same Case-B finding (the Phase 4 →
Phase 5 deferral-handoff convention not propagating across all
phase-exit-criterion / deferral-list references in the plan).
PROPOSAL.md remains unaffected. Landed as a follow-up commit
since the originating commit had already shipped before the
cascading scan ran; same Case-B audit trail.

## 2026-04-29T02:44:18Z — phase 5 sub-step 3 (assert_never coverage strategy)

**Decision:** Add `case _:` to `[tool.coverage.report].exclude_also`
in `pyproject.toml` and extend the style-doc enumeration of
structural exclusion patterns from 3 to 4. Coverage.py's
compound-statement exclusion rule treats the `case _:` line plus
its indented body as one block, dismissing the
`assert_never(<subject>)` body in the same sweep. After the
change, `parse/jsonc.py` drops from 22 stmts / 6 branches at 100%
to 20 stmts / 4 branches at 100% — the assert-never arm is now
structurally excluded rather than reached via contrived test
trigger.

The previously-shipped monkeypatch-trigger test in
`tests/livespec/parse/test_jsonc.py::test_assert_never_guards_unexpected_raw_load_result`
stays in place. It is no longer load-bearing for coverage but
asserts the runtime-guard behavior (an `AssertionError` is raised
if `_raw_load` is ever refactored to return something other than
`Success`/`Failure`). Future match-statement-bearing modules
(io/, commands/, doctor/static/, dev-tooling/checks/) skip the
contrived monkeypatch test and rely on the structural exclusion.

**Rationale:** The style doc lines 1054-1066 mandate
`case _: assert_never(<subject>)` as the universal match-statement
terminator, and `dev-tooling/checks/assert_never_exhaustiveness.py`
enforces the body shape at AST level. Every `case _:` arm in
this codebase is the assert-never sentinel — there is no
authorized non-assert-never use. The 100% line+branch coverage
gate combined with the v030 D2 prohibition on per-line
`# pragma: no cover` and the existing 3-pattern `exclude_also`
enumeration was structurally insolvable for match statements
without one of: (a) a per-test contrived monkeypatch trigger
(150-300 lines of test scaffolding across the remaining work);
(b) a 4th `exclude_also` pattern; (c) abandoning the
universal-assert_never mandate. Path (b) is the smallest
spec-aligned edit — it codifies what the existing AST check
already enforces and removes a recurring test-side tax across
~15-20 future test modules. PROPOSAL.md verified unaffected
(grep on `exclude_also` / `assert_never` / `pragma: no cover`
returns coverage policy under §"Testing approach" referencing
"structural patterns" without enumerating the specific 3 — the
enumeration lives entirely in the style doc). Same precedent as
v028 D1, v024 rounds 1-4, and 2026-04-26T08:33:35Z: companion-doc
overlay rides freely with implementation; no PROPOSAL revision
required. Gate confirmed via AskUserQuestion 2026-04-29 (option:
"Switch to exclude_also pattern (Recommended)") after the
parse/test_jsonc.py monkeypatch-trigger pattern shipped at
addcaac.

## 2026-04-29T07:35:42Z — phase 5 sub-step 2 (v032 retroactive-TDD redo)

**Decision:** Two paired fixes landed during sub-step 2
verification: (a) justfile config bug — five recipes
(`check-tests`, `check-coverage`, `e2e-test-claude-code-mock`,
`check-prompts`, `e2e-test-claude-code-real`) invoked bare
`pytest` rather than `uv run pytest`. With uv as the canonical
Python toolchain manager (v024 D1), every Python invocation
must go through uv; `pytest` isn't on system PATH. Pure config
fix per PROPOSAL §"Legitimate exceptions to test-first"
(configuration-only changes to justfile are exempt from
test-first). (b) plan-only drift (Case B) — Plan §"Retroactive
TDD redo of Phase 3 + Phase 4 work" sub-step 2 wording (just
authored at v032 commit time) predicted "errors with import
failures (intended)" which is not the actual post-deletion
outcome. With Phase-3-5 tests deleted, only the surviving
`tests/bin/test_bootstrap.py` collects and passes cleanly
(3 tests). Wording corrected to match actual outcome:
"runs cleanly but collects ONLY the surviving
`tests/bin/test_bootstrap.py`". PROPOSAL.md unaffected (the
plan section is bounded; PROPOSAL has no Phase-5-redo
description by reference or otherwise).

**Rationale:** Both fixes surfaced from the same sub-step 2
verification run; both are blocking the substantive sub-step 2
completion claim ("tree is empty of Phase 3-5 Python; verified
via just check-tests"). Without (a), `just check-tests`
errors with `pytest: not found` and verification can't run.
Without (b), the plan describes a different outcome than
reality. Path (a) is config-only, exempt from TDD per
PROPOSAL.md §"Legitimate exceptions to test-first" lines
3257-3265. Path (b) is plan-only Case-B drift, gate confirmed
via AskUserQuestion 2026-04-29 (option: "Fix both, single
commit (Recommended)"). Side observation NOT addressed in
this commit: 25+ `python3 dev-tooling/checks/*.py` invocations
in the justfile use bare `python3` rather than `uv run
python3` (only `check-tools` at line 194 uses the canonical
form); this is broader inconsistency that surfaces during the
dev-tooling/checks redo work and lands as part of that scope,
not bundled here per "one-finding-per-gate discipline".

## 2026-04-29T07:39:10Z — phase 5 sub-step 3 (v032 retroactive-TDD redo, direction choice)

**Decision:** Adopt **outside-in** TDD walking direction for the
v032 retroactive redo, instead of the plan's recommended
bottom-up dependency order. The first Red is the Phase 3
exit-criterion seed round-trip behavior (`livespec seed` against
a `tmp_path` fixture, propose-change + revise smoke cycle).
Each ImportError or failing assertion drives one new module/
behavior at a time. Modules are pulled into existence by
consumer pressure rather than authored speculatively.

**Rationale:** The user's stated goal for v032 is to force
loose coupling, high cohesion, and unnecessary-code
elimination through strict TDD. Bottom-up TDD (start at
`types.py`, walk up the dependency graph) is famously weaker on
all three: each module gets well-tested but speculatively
designed; consumer pressure that would constrain shape is
absent. Outside-in TDD makes consumer pressure the design
forcing function — modules only exist with the contract the
actual consumer demanded. Plan §"Retroactive TDD redo" sub-step
3 explicitly permits executor judgment on order ("Order is a
recommendation, not a contract — Red→Green discipline
determines the next module by which test the executor wants
to write next"); outside-in falls within that permission.

Risk acknowledged: outside-in commits may bundle multiple
"scaffolding" steps (an ImportError-driven Red can require
creating an empty module + adding one symbol + writing a real
assertion). Mitigation: commit per smallest test cycle, even
if "this commit's Red was an ImportError that drove creating
module X with one symbol"; the per-commit `## Red output`
block makes the iteration visible. Per PROPOSAL.md lines
3225-3228, iterating on test setup until the failure mode is
the behavior gap is itself part of the test-first cycle.

Gate confirmed via AskUserQuestion 2026-04-29 (option:
"Outside-in TDD, pause for now (Recommended)"). Session paused
here; next /bootstrap invocation resumes by authoring the
first failing test (Phase 3 exit-criterion seed round-trip).

## 2026-04-29T08:35:00Z — phase 5 sub-step 3 (Plan §propose-change minimum-viable description aligned with PROPOSAL --findings-json contract)

**Decision:** Apply Case-B direct-fix to PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md
lines 1389-1404 — the Phase-3 minimum-viable propose-change
description previously read "parses an inline-authored
proposed-change file's front-matter against
`proposed_change_front_matter.schema.json`" which contradicts
PROPOSAL.md §"`propose-change`" lines 2149-2161 (the wrapper
takes `--findings-json <path> <topic> [--author <id>]` and
validates against `proposal_findings.schema.json`, then composes
the markdown file from the findings via the field-copy mapping
on lines 2232-2242). Drift surfaced during cycle 10 of the v032
TDD redo via the `tdd-redo` sub-agent's pre-implementation
cascading-impact scan; the agent halted before committing
scaffolding. PROPOSAL.md verified internally consistent (literal
grep on `--findings-json` and `proposal_findings.schema.json`
returns the canonical descriptions in lines 237, 1170, 2138,
2149-2161, 2232-2242, etc.; no PROPOSAL section corroborates
the plan's "inline-authored markdown" framing). PROPOSAL.md is
unaffected; only the plan needed editing. Rewrote the plan
bullet to: "validates the inbound `--findings-json <path>`
payload against `proposal_findings.schema.json` (per PROPOSAL.md
lines 2149-2161), composes a proposed-change file from the
findings (one `## Proposal: <name>` section per finding via the
field-copy mapping in PROPOSAL.md lines 2232-2242), and writes
it to `<spec-target>/proposed_changes/<topic>.md`...". The
"out of Phase-3 scope" deferral list is preserved verbatim (it
applies equally to either input contract).

**Rationale:** Same precedent as the prior plan-only Case-B
direct-fixes during this bootstrap (decisions.md
2026-04-26T11:00:00Z, 2026-04-26T20:18:52Z, 2026-04-27T03:23:13Z,
2026-04-29T07:35:42Z): plan-only drift on plan-internal
phasing/wording gets the lighter Case-B path because the plan
is unversioned throwaway scaffolding deleted at Phase 11, while
PROPOSAL is the audit-versioned source of truth. PROPOSAL is
correct as-written; the plan was simply stale on this paragraph.
Per memory `feedback_only_ask_on_genuine_doubt.md` the executor
self-resolves wording fixes when there's no architectural
ambiguity (the architectural call here was already locked in
PROPOSAL by the original v019 Q1 / v015 O3 / v013 wrapper-CLI
design); no AskUserQuestion gate. User's standing autonomous-mode
authorization for the v032 redo session covers Case-B fixes that
align plan with already-decided PROPOSAL contracts. No
open-issues entry per Case-B rules (open-issues is
PROPOSAL-blocking only). Adjacent plan paragraphs for revise.py
(line 1417-1426) and critique.py (line 1405-1413) show similar
v019 Q1 wording but were not re-verified in this gate per
"one-finding-per-gate discipline"; if the cycle-15-ish revise
work surfaces matching drift, it'll get its own Case-B fix at
that time.
