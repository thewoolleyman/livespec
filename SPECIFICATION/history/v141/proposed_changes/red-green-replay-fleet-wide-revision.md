---
proposal: red-green-replay-fleet-wide.md
decision: accept
revised_at: 2026-06-25T14:48:08Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepting the Conformance Contract slot for epic livespec-gcp2: red-green-replay enforcement is fleet+adopter-wide, closing the 'no product Python' loophole that omitted the livespec-driver-* Drivers; enforced at both lefthook and authoritative CI; sole exemption is zero-first-party-Python repos (Rust console, tracked as livespec-1t17). No H2 change; heading-coverage unaffected.

## Resulting Changes

- non-functional-requirements.md
