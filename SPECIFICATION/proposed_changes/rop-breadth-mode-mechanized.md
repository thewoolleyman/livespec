---
topic: rop-breadth-mode-mechanized
author: claude-opus-4-8
created_at: 2026-07-22T19:00:28Z
---

## Proposal: ROP breadth + main()-boundary marker gate is mechanically enforced; align the spec to ruling 8

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Ruling 8 (rop-sweep-fleet-policy) makes `check-no-except-outside-io` breadth-aware in every governed repo, layered or flat, and it shipped in livespec-dev-tooling PR #516 (merged `2be20e19`). The merged check MECHANICALLY enforces three things: a NARROW, ENUMERATED catch is PERMITTED anywhere; a BROAD catch at a `main()` boundary MUST carry one of the closed-set `# noqa: BLE001` markers; and where a layered `io/` tree exists, that tree is wholesale exempt. What the check does NOT yet enforce — and what therefore remains REVIEW-enforced — is the `sole` cardinality, the pairing of each boundary with its correct marker flavor, and exact marker wording beyond the closed-set substring the check matches. This proposal aligns `SPECIFICATION/non-functional-requirements.md` with that reality: it re-scopes the §"ROP composition" breadth rule to bind uniformly, records the mechanically-enforced subset (retiring the "still no-ops" / "MUST NOT be described as already enforced" clauses), states the accurate REVIEW-enforced residual, disambiguates that a narrow seam lift is permitted regardless of package shape, and re-derives the now-stale enforcement-split sentence and review-enforced list in §"Supervisor discipline".

### Motivation

The spec at §"ROP composition" currently (a) scopes the breadth-not-position rule to "a repo without an `io/` layered tree (`io_trees` unset)", but ruling 8 makes the breadth rule bind uniformly, layered branch included; (b) asserts "the shipped check still no-ops when `io_trees` is unset", which `qm5` removed; and (c) states the breadth mode "is a spec rule enforced by REVIEW today ... mechanizing it is tracked follow-up work and MUST NOT be described as already enforced" — a clause that, now that the check ships, instructs readers to DENY enforcement that exists. Separately, the preceding hand-rolled-catch bullet says narrow catches "remain available in an entry artifact's helper functions in a repo without an `io/` layered tree", which reads as permitting narrow catches ONLY in flat repos, contradicting the repo-agnostic "sanctioned hand-rolled form" rule in the same bullet. And §"Supervisor discipline" (the enforcement-split paragraph) still says "ruff `BLE001` polices catch BREADTH; `check-no-except-outside-io` polices catch POSITION" and lists "the marker-wording closed set" among REVIEW-enforced rules — both stale once the check polices breadth and closed-set marker presence, producing a cross-section contradiction if left untouched.

Two precision points this proposal deliberately holds. First, it states the spec CONTRACT (which broad positions are permitted), NOT the check's current algorithm: the check exempts only `main()`-boundary catches, so it currently over-flags the sanctioned loop-iteration (supervision-loop body) and foreign-code-isolation (extension surface) broad catches — but those are PERMITTED by contract, and the check's over-flagging of them is a tracked check defect (livespec-dev-tooling), not a spec offense. Writing "broad is an offense unless `main()`-direct-child" into the spec would ratify the defect as contract and would go false when the check is fixed; the amendment instead carves those two forms out to their own governing clauses. Second, it does NOT touch the sanctioned marker SET or marker POSITIONING; those two inert markers are the same check defect, tracked in livespec-dev-tooling, not a spec gap.

Sequencing (satisfied): livespec-dev-tooling PR #516 merged to master (`2be20e19`, 2026-07-22), so this amendment neither claims enforcement that does not exist nor may be left denying enforcement that does. Per the fleet rule, an independent Fable review is a precondition for the revise accept.

### Proposed Changes

Four edits, all to `SPECIFICATION/non-functional-requirements.md`: three to the §"ROP composition" bullets, one (two spans) to the §"Supervisor discipline" enforcement-split paragraph. No `## ` heading is added, removed, or renamed, so no `tests/heading-coverage.json` co-edit is required.

EDIT 1 — re-scope the §"ROP composition" `io_trees`-unset span to state the contract uniformly, mechanization included, without calling the sanctioned non-`main()` forms offenses. REPLACE the verbatim span:
"In a repo without an `io/` layered tree (`io_trees` unset — e.g. a hook-only Driver), that check MUST still run rather than no-op, but in that mode it polices catch BREADTH rather than Try-node POSITION: a BROAD catch outside the `supervisor_entry_files` / `commands_trees` exemptions is an offense, while a NARROW, ENUMERATED catch in an entry artifact's helper function is PERMITTED and MUST NOT be flagged. Position-policing is a layered-architecture concern that does not apply to a flat package, and conflating the two would flag the very seam lifts this section prescribes."
WITH:
"This restriction is MECHANICALLY enforced uniformly, regardless of package shape: a NARROW, ENUMERATED catch is PERMITTED anywhere and MUST NOT be flagged, and a BROAD catch at a `main()` boundary in a `supervisor_entry_files` / `commands_trees` entry artifact MUST carry one of the closed-set `# noqa: BLE001` markers (§\"Linter rule set\") — the check flags such a boundary catch when the marker is absent. Where a layered `io/` tree exists that tree is wholesale exempt; the io-tree exemption is a layered-architecture concern that does not apply to a flat package, so conflating it with catch breadth would flag the very seam lifts this section prescribes. The loop-iteration and foreign-code-isolation broad catches sanctioned above sit OUTSIDE a `main()` boundary and are governed by their own clauses (§\"Supervisor discipline\"; the foreign-code catch below), not by this `main()`-boundary marker gate. In a repo without an `io/` layered tree (`io_trees` unset — e.g. a hook-only Driver) the check MUST still run rather than no-op; the rule binds there identically."

EDIT 2 — replace the stale "enforced by REVIEW today / still no-ops" span with the mechanically-enforced subset and the accurate REVIEW-enforced residual. REPLACE the verbatim span:
"That breadth mode is a spec rule enforced by REVIEW today — the shipped check still no-ops when `io_trees` is unset; mechanizing it is tracked follow-up work and MUST NOT be described as already enforced."
WITH:
"The breadth rule and the requirement that a broad `main()`-boundary catch carry a closed-set marker are MECHANICALLY enforced by `check-no-except-outside-io`, which runs whether or not `io_trees` is declared. What REMAINS review-enforced is the per-artifact / per-supervision-loop `sole` cardinality, the pairing of each boundary with its correct marker flavor, and exact marker wording beyond the closed-set substring the check matches (§\"Linter rule set\")."

EDIT 3 — disambiguate the preceding hand-rolled-catch bullet so a narrow seam lift is permitted regardless of package shape. REPLACE the verbatim span:
"Both forms remain available in an entry artifact's helper functions in a repo without an `io/` layered tree: what is policed there is catch BREADTH, not the presence of a `try/except` (§\"ROP composition\", the `io_trees`-unset clause below)."
WITH:
"Both forms remain available in an entry artifact's helper functions regardless of package shape: a NARROW, ENUMERATED `try/except` is the sanctioned seam lift and MUST NOT be flagged in a flat OR a layered package. What is policed is catch BREADTH, not the presence of a `try/except`; the io-tree exemption (a broad catch inside a layered `io/` tree) is the only layered-only part (§\"ROP composition\", the breadth clause below)."

EDIT 4 — re-derive the two now-stale spans in the §"Supervisor discipline" enforcement-split paragraph so it no longer contradicts EDITs 1–2.

EDIT 4a. REPLACE the verbatim span:
"ruff `BLE001` polices catch BREADTH; `check-no-except-outside-io` polices catch POSITION (which trees, and which `main()` direct-children are exempt)"
WITH:
"ruff `BLE001` polices catch BREADTH at the construct level; `check-no-except-outside-io` polices catch BREADTH and POSITION together — which trees are exempt, which `main()` direct-children are exempt, and whether a broad catch at a `main()` boundary carries one of the closed-set markers"

EDIT 4b. REPLACE the verbatim span:
"The per-artifact cardinality rule, the marker-wording closed set, and the requirement that each handler discharge its flavor's contract are therefore spec rules enforced by REVIEW today"
WITH:
"The per-artifact / per-supervision-loop `sole` cardinality rule, the pairing of each boundary catch with its correct marker flavor, exact marker wording beyond the closed-set substring the check matches, and the requirement that each handler discharge its flavor's contract are therefore spec rules enforced by REVIEW today"
