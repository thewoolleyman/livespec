---
topic: python-style-subcommand-lifecycle
author: Claude Sonnet 4.6 (1M context)
created_at: 2026-05-06T15:30:00Z
---

## Proposal: Migrate style-doc §"Sub-command lifecycle composition" into `SPECIFICATION/spec.md`

### Target specification files

- SPECIFICATION/spec.md

### Summary

Cycle 7 of Plan Phase 8 item 2 per-section migration. Lands the source doc's §"Sub-command lifecycle composition" content (lines 645-696, ~52 lines of substantive content) as an INSERT into the existing `## Sub-command lifecycle` in `SPECIFICATION/spec.md`. The existing section already covers the lifecycle rule in detail; the style doc adds three pieces not yet in the spec: (1) a compact per-sub-command applicability table (seed exempt from pre-step, help/doctor no pre/post, prune-history no post-step LLM, propose-change/critique/revise both); (2) a clarification that the LLM-driven flag pairs (`--skip-doctor-llm-*`) are LLM-layer only and MUST NOT reach Python wrappers; (3) an explicit composition-freedom note (Python mechanism is implementer choice under the architecture-level constraints in `SPECIFICATION/constraints.md`). Inserted between the general lifecycle paragraph and the per-sub-command detail paragraphs (before `**`critique` payload validation.**`). BCP-14-restructured. Cross-references cycle 1's deviation rationale.

### Motivation

The existing `## Sub-command lifecycle` in spec.md specifies the detailed per-sub-command contracts (critique delegation, revise file-shaping, prune-history procedure, pre-step skip control) but lacks a compact per-sub-command applicability summary at the top. Future implementors reading the section must infer which sub-commands have pre-step / post-step / LLM-driven phases from the individual contract paragraphs. The style doc's compact table and the LLM-flag clarification make this explicit upfront. The composition-freedom note anchors the spec's intent to allow any `dry-python/returns` composition primitive for the lifecycle chain.

The destination is `SPECIFICATION/spec.md` (not `constraints.md`) because `## Sub-command lifecycle` is the existing heading and the content is behavioral (lifecycle rules) rather than purely implementation-constraint.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md**: insert a compact applicability paragraph + LLM-flag clarification + composition-freedom note AFTER the general lifecycle rule paragraph and BEFORE `**`critique` payload validation.**`:

> Sub-command applicability for the pre-step / post-step wrapper lifecycle:
>
> - **`seed`** is exempt from pre-step `doctor` static (see PROPOSAL.md). Runs sub-command logic + post-step only.
> - **`help` and `doctor`** have no pre-step and no post-step wrapper-side static.
> - **`prune-history`** has pre-step and post-step static but no post-step LLM-driven phase.
> - **`propose-change`, `critique`, `revise`** have both pre-step and post-step static.
>
> The post-step LLM-driven phase, where applicable, runs from skill prose AFTER the Python wrapper exits; Python MUST NOT invoke the LLM. The `--skip-doctor-llm-objective-checks` / `--run-doctor-llm-objective-checks` and `--skip-doctor-llm-subjective-checks` / `--run-doctor-llm-subjective-checks` flag pairs are LLM-layer only — they gate the two post-step LLM-driven phases (both skill prose) and MUST NOT reach Python wrappers.
>
> Python composition mechanism for the lifecycle chain (pre-step + sub-command logic + post-step) is implementer choice under the architecture-level constraints in `SPECIFICATION/constraints.md`.
