# critique-fix v030 → v031 revision

## Origin

Phase 5 sub-step 3 implementation work surfaced a literal-text
gap in PROPOSAL.md's §"Testing approach" structural-exclusion
enumeration (lines 3372-3375).

PROPOSAL.md states:

> the only structural exclusions are
> `if TYPE_CHECKING:`, `raise NotImplementedError`, and
> `@overload` blocks via
> `[tool.coverage.report].exclude_also`.

A test for `livespec/parse/jsonc.py` at Phase 5 sub-step 3
demonstrated that the `case _: assert_never(<subject>)` arm
mandated universally by the style doc (lines 1054-1066) plus
enforced at AST level by
`dev-tooling/checks/assert_never_exhaustiveness.py` is
structurally unreachable in correctly-typed code. Reaching it
in tests requires a contrived monkeypatch that constructs an
off-protocol value purely to drive coverage — not a behavior
under test. Repeating that pattern across the ~15-20 remaining
match-statement-bearing modules (io/, commands/, doctor/static/,
dev-tooling/checks/) would add 150-300 lines of contrived test
scaffolding that test-drives nothing.

Commit `abd0cdd` extended `[tool.coverage.report].exclude_also`
in `pyproject.toml` from 3 patterns to 4 (added `case _:`) and
paired the style-doc enumeration at lines 1479-1480 with the
same 4-pattern listing. The intended reasoning was the
established companion-doc-overlay precedent (v028 D1, v024
rounds 1-4, decisions.md 2026-04-26T08:33:35Z): companion-doc
edits ride freely with implementation when PROPOSAL.md is
unaffected. The pre-commit verification that PROPOSAL.md was
unaffected was incomplete — grep on `exclude_also` alone did
not pick up the literal 3-pattern enumeration on the adjacent
lines, which uses the pattern names directly without the
keyword on the same line.

The post-abd0cdd state is: pyproject.toml carries 4 patterns,
style doc enumerates 4, but PROPOSAL.md still says "the only
structural exclusions are" three. Three sources, two values.

The exclusion-set change is substantive (it changes coverage-
gate semantics, not a label/typo), so the cosmetic-rides-along
carve-out for PROPOSAL.md drift does NOT apply per the
"severity judgment over rule-following" rule. v031 reconciles
PROPOSAL.md to match the implementation + style doc.

## Decisions captured in v031

### D1 — Extend PROPOSAL.md `exclude_also` enumeration from 3 patterns to 4

**Decision.** Update PROPOSAL.md §"Testing approach" lines
3372-3375 to enumerate 4 structural exclusions instead of 3,
adding `case _:` with a one-sentence rationale referencing the
universal-assert_never mandate and AST-level enforcement.

**Old text (PROPOSAL.md lines 3372-3375):**

```
the only structural exclusions are
`if TYPE_CHECKING:`, `raise NotImplementedError`, and
`@overload` blocks via
`[tool.coverage.report].exclude_also`.
```

**New text:**

```
the only structural exclusions are
`if TYPE_CHECKING:`, `raise NotImplementedError`,
`@overload`, and `case _:` blocks via
`[tool.coverage.report].exclude_also`. The fourth pattern
(`case _:`) reflects the universal `case _: assert_never(
<subject>)` mandate at companion style-doc lines 1054-1066
plus the AST-level enforcement at
`dev-tooling/checks/assert_never_exhaustiveness.py`: every
`case _:` arm in the codebase is the structurally-unreachable
assert-never sentinel, and coverage.py's compound-statement
exclusion rule excludes the arm body
(`assert_never(<subject>)`) in the same sweep as the
`case _:` line.
```

**Source-doc impact.**

- PROPOSAL.md lines 3372-3375 — the substance change.
- Companion `python-skill-script-style-requirements.md` lines
  1473-1494 — already updated at commit abd0cdd via the
  companion-doc-overlay path; the v031 revision file documents
  the PROPOSAL-side reconciliation and the abd0cdd reference
  as the implementation commit.
- `pyproject.toml` `[tool.coverage.report].exclude_also` —
  already updated at commit abd0cdd.
- No additional companion-doc impact: the only documents that
  enumerate `exclude_also` patterns are PROPOSAL.md and the
  style doc. Plan and other companion docs reference the
  policy by pointer ("structural exclusions only; see the
  style doc") without re-enumerating.

### D2 — Plan-level edits (Version basis + Phase 0 byte-identity + Execution prompt)

**Decision.** Standard plan-level v031-bump edits.

- Plan §"Version basis" preamble adds a v031 decision block
  capturing D1 + D2 + the abd0cdd-as-implementation
  reference.
- Plan Phase 0 step 1 byte-identity reference bumps to
  `history/v031/PROPOSAL.md`.
- Plan Phase 0 step 2 frozen-status header literal bumps to
  "Frozen at v031".
- Plan Execution-prompt block authoritative-version line
  bumps to v031.

No Phase-N body edits required: the v031 substance change is
contained in PROPOSAL.md §"Testing approach"; phase work
references the rule by pointer rather than enumerating
patterns.

## Origin commit (implementation already shipped)

`abd0cdd` — `phase-5: add `case _:` to coverage exclude_also
(Case-B + style-doc overlay)`. The v031 PROPOSAL revision
brings PROPOSAL.md to alignment with the
already-shipped pyproject + style-doc edits. The originating
open-issues entry at `bootstrap/open-issues.md` (timestamp
2026-04-29T02:44:18Z) gets `Status: resolved` upon v031 commit
landing.
