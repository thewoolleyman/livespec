---
topic: rop-breadth-mode-mechanized
author: claude-opus-4-8
created_at: 2026-07-22T19:00:28Z
---

## Proposal: ROP breadth-and-position is mechanically enforced; align the spec to ruling 8

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Ruling 8 (rop-sweep-fleet-policy) makes `check-no-except-outside-io` breadth-aware in every governed repo, layered or flat: a NARROW, ENUMERATED catch passes anywhere and MUST NOT be flagged, while a BROAD catch outside `io/**` is an offense unless it holds a sanctioned boundary position AND carries a closed-set marker. That enforcement ships in livespec-dev-tooling PR #516. Three clauses in the §"ROP composition" `io_trees`-unset bullet become FALSE on merge, and one sentence in the preceding hand-rolled-catch bullet reads ambiguously. This proposal corrects all four: it re-scopes the breadth rule to bind uniformly, records that the rule is now MECHANICALLY enforced (removing the "still no-ops" / "MUST NOT be described as already enforced" clauses), narrows what remains REVIEW-enforced to marker wording and `sole` cardinality, and disambiguates that a narrow seam lift is permitted regardless of package shape.

### Motivation

The spec at §"ROP composition" currently (a) scopes the breadth-not-position rule to "a repo without an `io/` layered tree (`io_trees` unset)", but ruling 8 extends breadth-awareness to the LAYERED branch too; (b) asserts "the shipped check still no-ops when `io_trees` is unset", which `qm5` removed; and (c) states the breadth mode "is a spec rule enforced by REVIEW today ... mechanizing it is tracked follow-up work and MUST NOT be described as already enforced" — a clause that, once the check ships, actively instructs readers to DENY enforcement that exists. Separately, the hand-rolled-catch bullet says narrow catches "remain available in an entry artifact's helper functions in a repo without an `io/` layered tree", which reads as permitting narrow catches ONLY in flat repos, contradicting the repo-agnostic "sanctioned hand-rolled form" rule stated in the same bullet. Leaving the spec unamended after merge makes it deny enforcement that exists; ratifying before merge makes it claim enforcement that does not yet exist — so this proposal MUST NOT be accepted via the revise operation until PR #516 has merged to livespec-dev-tooling master. The marker set and marker positioning are deliberately NOT touched: the two structurally-inert markers (`foreign-code isolation`; `sole loop-iteration bug-catcher`) are a check defect tracked in livespec-dev-tooling, not a spec gap.

### Proposed Changes

Three edits to the §"ROP composition" `io_trees`-unset bullet (currently one bullet beginning "**BROAD catching** outside `io/**` is restricted to the boundary handler") and one edit to the preceding hand-rolled-catch bullet.

EDIT 1 — re-scope the breadth rule to bind uniformly. REPLACE the verbatim span:
"In a repo without an `io/` layered tree (`io_trees` unset — e.g. a hook-only Driver), that check MUST still run rather than no-op, but in that mode it polices catch BREADTH rather than Try-node POSITION: a BROAD catch outside the `supervisor_entry_files` / `commands_trees` exemptions is an offense, while a NARROW, ENUMERATED catch in an entry artifact's helper function is PERMITTED and MUST NOT be flagged. Position-policing is a layered-architecture concern that does not apply to a flat package, and conflating the two would flag the very seam lifts this section prescribes."
WITH:
"`check-no-except-outside-io` polices catch BREADTH uniformly, regardless of package shape: a NARROW, ENUMERATED catch is PERMITTED anywhere and MUST NOT be flagged, while a BROAD catch outside `io/**` is an offense UNLESS it is BOTH at a sanctioned boundary position — a direct child of `main()` in a `supervisor_entry_files` / `commands_trees` entry artifact — AND carries one of the closed-set `# noqa: BLE001 — sole …` markers (§"Linter rule set"). It additionally polices catch POSITION where a layered `io/` tree exists (which trees are wholesale exempt); position-policing is a layered-architecture concern that does not apply to a flat package, so conflating breadth with position would flag the very seam lifts this section prescribes. In a repo without an `io/` layered tree (`io_trees` unset — e.g. a hook-only Driver) the check MUST still run rather than no-op, and the breadth rule above binds there identically."

EDIT 2 — record that the rule is now mechanically enforced. REPLACE the verbatim span:
"That breadth mode is a spec rule enforced by REVIEW today — the shipped check still no-ops when `io_trees` is unset; mechanizing it is tracked follow-up work and MUST NOT be described as already enforced."
WITH:
"This breadth-and-position rule is MECHANICALLY enforced by `check-no-except-outside-io`: the check runs whether or not `io_trees` is declared, and it flags a BROAD catch outside `io/**` that lacks a sanctioned boundary position or a sanctioned marker. What remains REVIEW-enforced is the marker-wording closed set and the per-artifact / per-supervision-loop `sole` cardinality; mechanizing those is tracked follow-up work (§"Linter rule set") and MUST NOT be described as already mechanically enforced."

EDIT 3 — disambiguate the hand-rolled-catch bullet so a narrow seam lift is permitted regardless of package shape. REPLACE the verbatim span:
"Both forms remain available in an entry artifact's helper functions in a repo without an `io/` layered tree: what is policed there is catch BREADTH, not the presence of a `try/except` (§"ROP composition", the `io_trees`-unset clause below)."
WITH:
"Both forms remain available in an entry artifact's helper functions regardless of package shape: a NARROW, ENUMERATED `try/except` is the sanctioned seam lift and MUST NOT be flagged in a flat OR a layered package. What is policed is catch BREADTH, not the presence of a `try/except`; position-policing (which trees a BROAD catch may sit in) is the only layered-only part (§"ROP composition", the breadth clause below)."

No `## ` heading is added, removed, or renamed by these edits, so no `tests/heading-coverage.json` co-edit is required. RATIFICATION SEQUENCING: the revise operation MUST NOT accept this proposal before livespec-dev-tooling PR #516 has merged to master, and SHOULD accept it promptly thereafter so the spec neither claims nor denies enforcement out of step with the shipped check.
