---
proposal: drop-doctor-from-spec-target-enumeration.md
decision: accept
revised_at: 2026-05-06T17:23:20Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: livespec-bootstrap-phase12
---

## Decision and Rationale

Drift between contracts.md prose enumeration (over-includes doctor) and the wrapper-CLI table directly above it (correctly lists --spec-target only on propose-change, critique, revise). The shipped bin/doctor_static.py impl agrees with the table; the prose paragraph is the lone divergent text. Accept the proposal as written; the new wording removes doctor from the enumeration and adds a clarifying sentence pointing readers at the doctor-specific multi-tree enumeration documented in §"Per-sub-spec doctor parameterization".

## Resulting Changes

- contracts.md
