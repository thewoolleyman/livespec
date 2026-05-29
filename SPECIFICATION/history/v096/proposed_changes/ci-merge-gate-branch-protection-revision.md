---
proposal: ci-merge-gate-branch-protection.md
decision: accept
revised_at: 2026-05-29T05:00:50Z
author_human: E2E Test <e2e-test@example.com>
author_llm: livespec-orchestrate
---

## Decision and Rationale

Accepted as filed. Adds the family-wide 'CI as a merge gate (branch protection)' non-functional-requirement modeled on the canonical commit-refuse-hook infra NFR: declares the required-check branch-protection mandate uniformly across livespec, every livespec-impl-* plugin, livespec-dev-tooling, livespec-runtime, and every copier-template-generated sibling; requires enforce_admins + strict; states the rationale that branch protection is GitHub repo settings (not a committed file, so it does not propagate via copier and must be enabled per-repo); and names branch_protection_alignment (shipped from livespec-dev-tooling's shared inventory) as the mechanical enforcer completing the NFR-rule + bootstrap + doctor-invariant triad. Added as a '### ' (H3) sub-section under '## Constraints', immediately after '### Commit-refuse hook bootstrap procedure'; no tests/heading-coverage.json co-edit is required because the shared heading_coverage check tracks '## ' (H2) headings only.

## Resulting Changes

- non-functional-requirements.md
