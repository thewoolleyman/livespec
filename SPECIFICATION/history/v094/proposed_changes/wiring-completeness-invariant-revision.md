---
proposal: wiring-completeness-invariant.md
decision: accept
revised_at: 2026-05-28T02:32:40Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

Accept as-is. This PC codifies the Phase 2.1 design from epic li-univck (universal-check propagation across the livespec fleet). The four-point invariant + three-layer enforcement (in-repo gate via check-aggregate-completeness, copier template stamp, cross-repo doctor backstop) is fully specified and unambiguous. The prose-insertion target — §"Shared code sync — livespec-dev-tooling" inline, immediately after the existing partition-criterion paragraph — is the natural extension of the existing partition contract: the shipping side of that contract already exists; this PC adds the consumption side. No new H2 is introduced (so no heading-coverage.json co-edit is required, as the PC itself notes). Accepting this unblocks li-jnjtpl (Phase 2.2 — justfile.jinja template stamp), li-dctxr (Phase 2.3 — doctor cross-repo invariant), and the per-sibling wiring work in Phase 3 (li-ipxwir, li-ldtwir, li-runwir).

## Resulting Changes

- contracts.md
