---
topic: claude-opus-4-7-critique
author: claude-opus-4-7
created_at: 2026-05-10T07:49:03Z
---

## Proposal: template-files-present check is silent on the mandated 6-file set

### Target specification files

- SPECIFICATION/templates/livespec/constraints.md

### Summary

templates/livespec/constraints.md §"Spec-file-set well-formedness" mandates the 6-file set `{README.md, spec.md, contracts.md, constraints.md, non-functional-requirements.md, scenarios.md}` at every livespec-template-rooted spec tree's root and explicitly states that missing any of these files is a doctor static-phase `template-files-present` failure. The actual implementation at `.claude-plugin/scripts/livespec/doctor/static/template_files_present.py` is currently scoped to checking only `<spec_root>/spec.md`. The constraint and the implementation are inconsistent: the constraint promises a wider failure surface than the implementation delivers.

### Motivation

The constraint's normative MUST and the implementation's actual behavior are inconsistent. A reader of `constraints.md` would conclude that omitting `non-functional-requirements.md` or `scenarios.md` from a livespec-template-rooted tree triggers a `template-files-present` failure; in fact the static check is silent on those files today, so the violation goes undetected. The constraint and the implementation MUST be brought into alignment, but the right direction (tighten the impl vs relax the constraint vs add an explicit known-gap note) is the user's architectural call at revise time.

### Proposed Changes

Surface the spec/impl drift in `SPECIFICATION/templates/livespec/constraints.md` §"Spec-file-set well-formedness" and choose one of the following at revise time. Option (a) — tighten the impl: leave the constraint as-is and widen `.claude-plugin/scripts/livespec/doctor/static/template_files_present.py` to enumerate every file in the mandated 6-file set and emit a `fail` Finding for each missing file. Option (b) — relax the constraint: rewrite the constraint to acknowledge that `template-files-present` MAY only enforce a subset (e.g., `spec.md` alone) and document the broader 6-file set as a SHOULD-level recommendation rather than a doctor-static-phase contract. Option (c) — explicit known-gap note: leave both the constraint and the impl as-is but add a one-line note in the constraint stating that the doctor static check currently only enforces `spec.md` and that the broader file-set enforcement is tracked elsewhere (a beads issue or follow-up propose-change). The choice between these options is non-mechanical and SHOULD be made at revise time.
