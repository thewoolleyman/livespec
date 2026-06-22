---
proposal: family-universal-agent-instruction-core.md
decision: modify
revised_at: 2026-06-22T06:41:53Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-opus-groom-livespec-ad4ov7
---

## Decision and Rationale

Accepted into the spec. Consolidated to contracts.md as the single contract surface; the mechanical enforcement is stated by reference to the existing shared fleet-membership obligation suite (where the fleet / shared-code-sync contract already lives) rather than a duplicate constraints.md invariant.

## Modifications

Folded the clause into one new contracts.md section 'Family agent-instruction core' instead of splitting across contracts.md + constraints.md; enforcement is referenced to non-functional-requirements.md Shared code sync — livespec-dev-tooling.

## Resulting Changes

- contracts.md
