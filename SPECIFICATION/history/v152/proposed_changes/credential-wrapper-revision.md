---
proposal: credential-wrapper.md
decision: accept
revised_at: 2026-07-01T07:18:04Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8-1m
---

## Decision and Rationale

Crit-path step 1 of epic livespec-zd8h: generalize the fleet secret-injection contract from 1Password/with-livespec-env.sh-specific to a backend-agnostic credential_wrapper (opaque literal argv-prefix array in .livespec.jsonc). Accepts both proposal sections: (a) generalize non-functional-requirements.md Fleet-secrets section plus the docs/installation.md and AGENTS.md restatements, inserting the standardized Credential wrapper contract paragraph verbatim; (b) bind the credential_wrapper key into contracts.md at Spec-side CLI contract, Fleet agent-instruction core (phrase binding + guard generalization), and config-named-cli-callability. No new H2 heading in any spec file, so tests/heading-coverage.json is unaffected.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
- ../docs/installation.md
- ../AGENTS.md
