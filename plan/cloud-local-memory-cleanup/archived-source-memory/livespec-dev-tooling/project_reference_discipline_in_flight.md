---
name: project-reference-discipline-in-flight
description: "Reference-discipline invariant (no cross-spec refs in spec; no §\"...\" citations from code) is NOT codified anywhere in the livespec family as of 2026-05-25; propose-change in flight upstream"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0a93c99b-d007-4563-80cc-64737c65cdc3
---

As of 2026-05-25, the livespec family lacks any invariant governing reference discipline. Specifically:

- `SPECIFICATION/*.md` files freely cite sibling-repo spec files, external work-item IDs (`li-fgqgnk`, etc.), epic phase identifiers (`Phase G.2/G.4/G.6`), and impl-tree paths — with no rule forbidding it.
- Source code (Python modules, skill prose) freely cites spec sections via `§"<heading>"` in docstrings — with no rule forbidding it.

The user surfaced this gap during a `/livespec:doctor` LLM-objective phase run on dev-tooling. The static-phase `doctor-anchor-reference-resolution` check is intentionally scoped to same-file Markdown link anchors (`[text](#slug)`) per its docstring at `livespec/doctor/static/anchor_reference_resolution.py:17-20`; cross-file `§"…"` prose references are out of scope and currently caught only by the LLM-objective phase opportunistically.

**Why:** Heading renames and revise-pass content reshuffling silently rot `§"…"` citations in both directions (spec→spec and code→spec). The user has been bitten by this pattern before — concrete examples found in this run: `livespec/doctor/static/depends_on_ref_wellformedness.py:14-15` cites `§"Doctor cross-boundary invariants"`; `livespec/SPECIFICATION/contracts.md:208` and `non-functional-requirements.md:592` carry leftover proposal-stage `"this proposal"` language inside ratified content.

**How to apply:**

1. The in-flight upstream propose-change `livespec/SPECIFICATION/proposed_changes/reference-discipline-invariant.md` codifies the rule with a carve-out: `.livespec.jsonc` carries an `external_references` block declaring the allowlist of permitted cross-repo `§"…"` citations. Two new static checks (`doctor-no-cross-spec-reference` + `doctor-no-spec-section-citation-in-code`) enforce it.
2. Until the upstream invariant lands and the static checks ship, audit cross-spec references and code `§"…"` citations during any livespec-family work — flag instances to the user; don't auto-fix in-place edits that would mass-rewrite content.
3. Related: `livespec-dev-tooling/SPECIFICATION/proposed_changes/spec-amendments-from-doctor-objective-findings.md` (filed in the same investigation) addresses three concrete instances in dev-tooling's spec: a dangling `§"Coordination-surface bootstrap procedure"` reference, stale §"Migration notes" proposal-stage language, and seven `Phase G.x` external-identifier citations.
4. Linked memories: [[project-livespec-sibling-family-cross-repo-coordination]] for the broader family context.
