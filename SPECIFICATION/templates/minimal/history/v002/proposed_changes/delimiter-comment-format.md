---
topic: delimiter-comment-format
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T00:55:05Z
---

## Proposal: Minimal-template delimiter-comment format finalization

### Target specification files

- SPECIFICATION/templates/minimal/contracts.md

### Summary

Finalize the `minimal` template's delimiter-comment format at SPECIFICATION/templates/minimal/contracts.md §"Delimiter-comment format". The current text says "the exact format is TBD in Phase 7"; this proposal codifies the format as `<!-- region:<name> -->` (open) + `<!-- /region:<name> -->` (close). The shared-dependency cycle MUST land before any per-prompt regeneration cycle that depends on it (per Plan §3531-3550) — propose-change / revise / critique against the minimal template's single-file SPECIFICATION.md output all need the format pinned for region-targeted edits to work.

### Motivation

Phase 7 sub-step (d).1 is the minimal-template-specific shared-dependency cycle that unblocks the (d).2-(d).5 per-prompt regeneration cycles + the (d).6 single-file starter cycle. The four invariants from the existing contracts.md text constrain the format: HTML comments, paired open+close markers, kebab-case alphanumeric region names, no nesting across boundaries. The `<!-- region:<name> -->` / `<!-- /region:<name> -->` shape satisfies all four with a single concrete regex pin: `<!--\s*(?:/)?region:([a-z0-9-]+)\s*-->`.

### Proposed Changes

One atomic edit to **SPECIFICATION/templates/minimal/contracts.md** §"Delimiter-comment format" (the entire section).

Replace the current section:

> ## Delimiter-comment format
>
> The `minimal` template's single-file `SPECIFICATION.md` end-user output MUST use HTML-comment delimiter markers to define named regions that propose-change/revise cycles can target precisely. The exact format is **TBD in Phase 7** — at this revision the contract carries a placeholder. The format MUST satisfy the following invariants:
>
> - Markers MUST be HTML comments (`<!-- ... -->`) so they are invisible in rendered Markdown.
> - Each region MUST have a paired open + close marker carrying the region name.
> - Region names MUST be kebab-case alphanumeric to match the propose-change topic-format constraint.
> - Nested regions MUST NOT cross boundaries (well-formed open/close balance).
>
> Phase 7's first propose-change against this sub-spec lands the concrete delimiter syntax. Until then, the `minimal` template's seed prompt SHOULD emit the `SPECIFICATION.md` body without delimiter markers; revise cycles MUST do whole-file replacement until the format is finalized.

with the following Phase-7-final section:

> ## Delimiter-comment format
>
> The `minimal` template's single-file `SPECIFICATION.md` end-user output uses HTML-comment delimiter markers to define named regions that propose-change/revise cycles can target precisely.
>
> ### Concrete syntax
>
> - **Open marker**: `<!-- region:<name> -->` on its own line.
> - **Close marker**: `<!-- /region:<name> -->` on its own line.
> - **Regex pin** (for parsers that need it): `<!--\s*(?:/)?region:([a-z0-9-]+)\s*-->` — the optional `/` distinguishes close from open; the captured group is the region name.
>
> ### Invariants
>
> - Markers MUST be HTML comments so they are invisible in rendered Markdown.
> - Each region MUST have a paired open + close marker carrying the same region name.
> - Region names MUST be kebab-case alphanumeric (`[a-z0-9-]+`) — matches the propose-change topic-format constraint so a region's name MAY directly mirror the topic that landed it.
> - Nested regions MUST NOT cross boundaries (well-formed open/close balance). A `region:foo` open MUST be closed before any enclosing `region:<other>` close.
> - Markers MUST appear on their own line (no inline text on the same line) to keep the parser regex single-line and to keep rendered Markdown clean.
>
> ### Worked example
>
> ```markdown
> # `<title>`
>
> <!-- region:project-intent -->
>
> The project ...
>
> <!-- /region:project-intent -->
>
> <!-- region:cadence -->
>
> The maintainer MUST review issues at least once per month.
>
> <!-- /region:cadence -->
> ```
>
> A propose-change targeting the `cadence` region replaces the body between `<!-- region:cadence -->` and `<!-- /region:cadence -->`; the rest of `SPECIFICATION.md` is byte-identical.
>
> ### Consumers
>
> The `minimal` template's `prompts/propose-change.md` and `prompts/revise.md` reference this format when emitting region-targeted edits. The Phase 9 `tests/e2e/fake_claude.py` mock harness parses against this same format. Future custom-template authors MAY adopt the same format unchanged or define their own; the format is not livespec-wide policy.

