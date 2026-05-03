---
proposal: file-lloc-soft-warn-hard-fail.md
decision: accept
---

## Decision and Rationale

Accept as proposed. The two-tier policy (SOFT 200 LLOC warn, HARD 250 LLOC fail) matches the developer-experience reality of mid-Green-amend refactors that briefly exceed 200 LLOC before settling. Implementation lands atomically per the v035 D5a / v033 D5b spec-then-implementation precedent.
