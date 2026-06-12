---
proposal: family-secrets-1password-environment.md
decision: accept
revised_at: 2026-06-12T06:41:26Z
author_human: E2E Test <e2e-test@example.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted as proposed (user-authorized). The 1Password Environment already carries the live family credentials and the wrapper machinery is installed; codifying it as the single canonical source — with the env-injection consumption rule, the sealed bootstrap-token exception, the scoped transient-materialization rule, the GitHub Actions derived-projection exception, the operator-managed write side, the no-leakage rule, and per-consumer Anthropic key naming — closes the audit finding that every family secret was loose with no canonical source behind it. No existing normative text in this tree conflicts; the section is net-new under the Constraints bucket of non-functional-requirements.md.

## Resulting Changes

- non-functional-requirements.md
