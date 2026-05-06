---
proposal: template-files-strict-enumeration-roadmap.md
decision: accept
revised_at: 2026-05-06T17:26:05Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: livespec-bootstrap-phase12
---

## Decision and Rationale

Accept the v1.0 acceptance + post-v1.0 roadmap as documented. The v1 built-in templates' `specification-template/` subtrees are `.gitkeep`-only at canonical state, so loose enumeration is functionally identical to strict enumeration in current operating conditions. Strict tightening is a future correctness improvement requiring DoctorContext widening + sub-spec template-name resolution + an io/template_files.py helper — all out of Phase 12 cleanup scope. Acceptance lands as a no-spec-edit revise (v046 spec files byte-identical to v045 per v038 D1 Statement B); the roadmap text is preserved in v046/proposed_changes/ for future implementer reference.

## Resulting Changes

(none)
