---
topic: comment-discipline-why-not-what
author: claude-opus
created_at: 2026-05-07T07:45:42Z
---

## Proposal: Codify comment discipline: WHY-not-WHAT, no version/decision/phase cruft

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add a new top-level section `## Comment discipline` to `SPECIFICATION/constraints.md` codifying two rules for every comment in the repo's first-party trees (justfile, lefthook.yml, .github/workflows/*.yml, .claude-plugin/scripts/livespec/**, .claude-plugin/scripts/bin/**, dev-tooling/**, and tests/**, excluding _vendor/**): (1) comments MUST explain WHY non-obvious behavior exists; comments MUST NOT explain WHAT the code does (well-named identifiers and BCP14 prose already convey WHAT); (2) comments MUST NOT cite version numbers (`v033`, `v034 D2`), decision IDs (`Per v036 D1`, `v037 D1`), phase numbers (`Phase 4`, `Phase 6 self-application`), cycle numbers (`cycle 117`, `cycle 61`), or any other historical bookkeeping marker — git history, commit messages, and revision snapshots already carry that audit trail. Existing comments in scope MUST be retroactively cleaned to comply.

### Motivation

The codebase currently carries dense historical-reference cruft in comments: `justfile` alone has ~25 occurrences of `Per v0NN <X>`, `Phase N`, or `cycle NNN` markers (e.g., `# v033 D5a Option-3 (cycle 61) + v034 step 3 (this commit):`, `# Per v036 D1: Red-mode-aware pre-commit aggregate`, `# v037 D1 broadened from --diff-filter=A`); `lefthook.yml` has another ~10; `.github/workflows/` adds more. These comments document HOW the rule was decided, not WHY the rule exists today. Every such reference: (a) bit-rots the moment a subsequent revision changes the underlying decision, leaving comments that contradict the live spec; (b) duplicates audit-trail data already preserved in `SPECIFICATION/history/vNNN/`, `git log`, and commit-message trailers; (c) imposes archeology cost on every reader who has to decode `v036 D1` to understand whether the comment is current. WHY-only comments survive revisions because they explain a constraint that holds independent of when the decision was made (e.g., `# pytest-cov defaults --cov-config to .coveragerc, which bypasses pyproject.toml's [tool.coverage.run]; pass the config path explicitly so the vendored-tree exclusion takes effect.` — explains a non-obvious tooling quirk; survives any future revision that doesn't change pytest-cov's behavior). The discipline aligns with the existing convention `# noqa: <CODE> — <reason>` (line 382) and `# type: ignore[<specific-code>] — <reason>` (line 303), both of which already require WHY-justification.

### Proposed Changes

ADD a new top-level section `## Comment discipline` to `SPECIFICATION/constraints.md`, positioned between the existing `## Linter and formatter` (line 360) and `## Complexity thresholds` (line 384) sections, with the following content:

```
## Comment discipline

Comments in first-party trees (`justfile`, `lefthook.yml`, `.github/workflows/*.yml`, `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `dev-tooling/**`, `tests/**`) MUST follow two rules:

**Rule 1 — WHY-not-WHAT.** A comment MUST explain WHY a section, recipe, or block exists when the WHY is non-obvious to a future reader: a hidden constraint, a subtle invariant, a workaround for a specific tooling bug, or behavior that would surprise a reader. A comment MUST NOT explain WHAT the code does — well-named identifiers, BCP14 normative prose, and the surrounding spec already convey WHAT. If removing the comment would not confuse a future reader who can read the code, the comment MUST be deleted.

**Rule 2 — No historical-bookkeeping references.** Comments MUST NOT cite version numbers (`v033`, `v034 D2`), decision IDs (`Per v036 D1`, `v037 D1`), phase numbers (`Phase 4`), cycle numbers (`cycle 117`), commit references (`this commit`, `the previous PR`), or any other temporal/historical bookkeeping marker. The audit trail of decisions lives in `SPECIFICATION/history/vNNN/`, `git log`, the v034 D3 replay-hook trailers, and per-revision proposed-change files; duplicating it in source-file comments creates bit-rot risk and reader-archeology cost. Comments MUST state the live constraint in present tense without reference to when, why-historically, or by-which-decision the constraint was adopted.

**Scope exemptions.** The two rules DO NOT apply to: (a) `_vendor/**` (vendored upstream code; comments are inherited as-is); (b) the YAML front-matter and Markdown body of files under `SPECIFICATION/` (the spec IS the historical record; cross-references to other spec sections are acceptable); (c) `SPECIFICATION/history/vNNN/` snapshots (immutable); (d) `archive/` (frozen historical artifacts). Inside in-scope trees, the per-line escapes `# noqa: <CODE> — <reason>` (per §"Linter and formatter") and `# type: ignore[<code>] — <reason>` (per §"Typechecker constraints") are already WHY-formed and remain compliant.

**Retroactive cleanup.** As part of accepting this proposal, every comment in the in-scope trees that violates Rule 1 or Rule 2 MUST be either rewritten to a WHY-form (when the comment carries a still-relevant non-obvious WHY) or deleted (when the comment is pure historical bookkeeping or pure WHAT). Reference checklist for the cleanup pass: every match for the regex `(?i)\b(v\d{3}\s*[A-Z]\d|per v\d{3}|phase\s+\d+|cycle\s+\d+|this commit|the previous (commit|PR))\b` in the in-scope trees MUST be reviewed and either rewritten or deleted.

**Enforcement.** A new `dev-tooling/checks/comment_no_historical_refs.py` script MUST be added to the `just check` aggregate (alongside `check-comment-line-anchors`) that greps every in-scope file for the historical-reference regex above and exits non-zero with structured findings naming each violation site. Rule 1 (WHY-not-WHAT) is judgment-based and MUST NOT be mechanically enforced — code review is the gate. Rule 2 is mechanically grep-able and MUST be enforced by the new check.
```

ADD a corresponding entry to the canonical target list in `python-skill-script-style-requirements.md` §"Enforcement suite — Canonical target list" naming `check-comment-no-historical-refs` as a python-code check (it greps Python sources too) and add it to the `check` aggregate in `justfile`. Categorize it as a python-code check per the companion proposal (`claude-opus-critique.md`) so it is skipped when zero `.py` files change.
