---
proposal: tests-mirror-pairing-exempt-private-helpers.md
decision: accept
---

## Decision and Rationale

Accept as proposed. The pure-declaration heuristic (no FunctionDef anywhere) is principled and mechanical; it generalizes the v033 D1 boilerplate-__init__.py exemption to its natural superset (pure dataclass modules + the registry + the error hierarchy). Re-aggregation lands alongside the impl per the v035 D5a / v033 D5b spec-then-implementation precedent.
