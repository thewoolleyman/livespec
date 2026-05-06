---
proposal: seed-wrapper-per-tree-emission.md
decision: accept
---

## Decision and Rationale

Accept as proposed. The two spec edits sharpen the seed-wrapper file-emission contract to enumerate the per-tree skill-owned files (proposed_changes/README.md, history/README.md, .gitkeep marker for empty history/v001/proposed_changes/) that Phase 6 patched imperatively under the v018 Q2 / v019 Q1 imperative-window carve-out. Wrapper implementation work in livespec/commands/_seed_railway_emits.py lands in a follow-up commit on this branch under v033 D5b mechanical guardrails (Red→Green per behavior, mirror-paired tests, per-file 100% coverage) per the Phase 7 dogfooding rule.
