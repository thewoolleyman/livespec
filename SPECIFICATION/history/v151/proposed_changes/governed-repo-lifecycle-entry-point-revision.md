---
proposal: governed-repo-lifecycle-entry-point.md
decision: accept
revised_at: 2026-06-27T06:23:04Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accept as proposed per the zs22.8.1 resume contract. Lands the new non-normative H3 '### Governed-repo lifecycle' under '## Spec', immediately after '### Conformance Pattern' and before '### Codex dogfooding compatibility'. It is an H3 — heading-coverage tracks H2 only (verified against the live check), so no heading-coverage entry is required. Fleet self-application infrastructure; introduces no new core skill, CLI, or doctor invariant on core's functional surface.

## Resulting Changes

- non-functional-requirements.md
