---
proposal: detect-impl-gaps-thin-transport-skill.md
decision: accept
revised_at: 2026-05-24T09:22:18Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Factor the read-only spec→impl gap-detection phase out of the heavyweight capture-impl-gaps skill into a new thin-transport sibling detect-impl-gaps (parallel naming). The detection logic is mechanical and belongs on the thin-transport side; the interactive filing workflow remains the heavyweight skill's contract. Doctor's gap-detection-dependent invariants consume the new surface uniformly. Eliminates the architecturally awkward 'non-mutating dry-run mode' framing on a heavyweight skill. Accept as proposed.

## Resulting Changes

- contracts.md
- constraints.md
- ../tests/heading-coverage.json
