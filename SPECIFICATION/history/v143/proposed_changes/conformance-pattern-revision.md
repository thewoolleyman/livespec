---
proposal: conformance-pattern.md
decision: accept
revised_at: 2026-06-25T17:39:08Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Increment 5, milestone M1 of epic livespec-zs22 (sub-epic livespec-zs22.7, milestone livespec-zs22.7.2). Lands the Conformance Pattern as a NEW NON-normative top-level '### Conformance Pattern' section in non-functional-requirements.md, after '### Control-Plane console guidance' and before '### Codex dogfooding compatibility'. It records the repeatable five-slot recipe (Contract / Mechanism / Installer / Verifier / Exemption), the reuse-by-default delivery rule, the consolidated 'just' keystone with its functional/non-functional boundary, the profile + declarative '.livespec-fleet-manifest.jsonc' 'adopters'/'posture' boundary, the four-tier enforcement-in-depth, the explicit-exemptions/default-fail-closed hard rule, and the concern registry seeded with concern #1 worktree-discipline and concern #2 cross-harness plugin-resolution. NAMES and GENERALIZES existing machinery (§Fleet membership contract, §Shared content sync — copier template, §Shared code sync — livespec-dev-tooling, §Cross-repo coordination — pin-and-bump) rather than duplicating it; framed exactly like the Dispatcher / grooming / Planning Lane / console blocks (no new core skill / CLI / doctor invariant on core's functional surface; realization stays in its owners' specs per §Sibling spec ownership). Honors locked decisions: baseline profile not 'factory'; just non-functional-only; fleet pins track latest RELEASE. H3 addition, so heading-coverage (which tracks H2 only) is unaffected. The machinery is tracked as ledger milestones livespec-zs22.7.3 through livespec-zs22.7.7, not duplicated as spec_commitments. Source design: research/factory-conformance/cross-repo-conformance-pattern.md and research/planning-workflow-gap/planning-lane-design.md.

## Resulting Changes

- non-functional-requirements.md
