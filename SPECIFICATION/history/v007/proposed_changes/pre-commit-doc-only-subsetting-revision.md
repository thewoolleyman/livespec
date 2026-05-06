---
proposal: pre-commit-doc-only-subsetting.md
decision: accept
---

## Decision and Rationale

Accept as proposed. The strict zero-.py predicate is unambiguous and audit-clean; pre-push + CI safety net preserves end-to-end validation for any branch landing on master. Implementation lands atomically per the v035 D5a / v033 D5b spec-then-implementation precedent.
