---
proposal: heading-coverage-narrow-and-orphan.md
decision: accept
---

## Decision and Rationale

Accept as proposed. Sharpens §"Heading taxonomy" to codify the (spec_root, spec_file, heading) triple per PROPOSAL.md lines 3771-3813, the narrowed walk to template-declared NLSpec files at each tree root only (excludes proposed_changes/, history/, templates/<name>/history/, and the skill-owned README.md), the three failure directions (uncovered, orphan, missing-reason-on-TODO), and the Scenario:-prefix skip rule. Implementation lands atomically per the v035 D5a / v033 D5b spec-then-implementation precedent: rewrite of dev-tooling/checks/heading_coverage.py, paired test rewrite, and rebuild of tests/heading-coverage.json (prune ~168 → ~81 entries; add spec_file to each).
