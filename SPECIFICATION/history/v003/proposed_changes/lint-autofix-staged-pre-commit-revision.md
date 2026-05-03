---
proposal: lint-autofix-staged-pre-commit.md
decision: accept
---

## Decision and Rationale

Accept as proposed. Sharpens the developer-tooling spec to explicitly describe the new pre-commit step ordering and the autofix step's interaction with the v034 D3 test-file-checksum invariant. Implementation (justfile lint-autofix-staged recipe + lefthook.yml step) lands in the same commit per the v035 D5a / v033 D5b spec-then-implementation precedent. Highest leverage of the five mini-track items: every subsequent commit (sub-step 1.c cycles 2-4 + the rest of sub-step 2) avoids the ~5min retry tax on auto-fixable lint trivia.
