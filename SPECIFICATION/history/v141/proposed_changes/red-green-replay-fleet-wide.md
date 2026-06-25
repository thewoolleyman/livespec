---
topic: red-green-replay-fleet-wide
author: claude-opus-4-8
created_at: 2026-06-25T14:47:00Z
---

## Proposal: Red-green-replay enforcement is fleet+adopter-wide (close the 'no product Python' loophole)

### Target specification files

- non-functional-requirements.md

### Summary

Add a bullet to §"..." right after the 'Executable-enforcement-suite requirements' bullet stating that the Red->Green replay gate is REQUIRED in every livespec-governed repo carrying any first-party Python (Drivers included, not only orchestrator plugins + sibling libraries), regardless of how a repo classifies that Python (hook scripts, dev-tooling, and product modules all count) -- there is NO 'no product Python' exemption. It MUST be enforced at BOTH layers: the local lefthook commit-msg gate AND an authoritative CI check (with the full history its commit-range form needs). The sole exemption is a governed repo with ZERO first-party Python (e.g. the Rust operator console), which carries a language-appropriate analogue tracked as its own work-item. New adopters inherit the wiring via the templates/impl-plugin/ copier scaffold.

### Motivation

Maintainer directive (2026-06-25): red-green-replay MUST be enforced across the entire fleet AND all adopters, regardless of a repo's self-classification. The existing 'Executable-enforcement-suite requirements' bullet says these checks flow to 'livespec-orchestrator-* plugins AND sibling libraries' but OMITS the livespec-driver-* Drivers -- the enumeration gap that let the Drivers rationalize a 'no product Python' exemption (their 228/365-line footgun guards + dev-tooling + tests are real Python). This is the Conformance 'Contract' slot for the red-green-replay concern (epic livespec-gcp2); the wirings into both Drivers + the CI parity are landing in their repos, and the Rust console analogue is tracked as livespec-1t17. 'Both layers' matters because a lefthook-only gate is bypassable and this fleet's rule is that CI is authoritative.

### Proposed Changes

In non-functional-requirements.md, immediately AFTER the bullet '- **Executable-enforcement-suite requirements.** ... codified in `livespec-dev-tooling`'s own `contracts.md`.', insert a new sibling bullet:

- **Red-green-replay is fleet+adopter-wide.** The Red->Green replay gate (`check-red-green-replay`, shipped via `livespec-dev-tooling`) is REQUIRED in EVERY livespec-governed repo carrying any first-party Python -- the `livespec-driver-*` Drivers included, not only the orchestrator plugins and sibling libraries named above -- regardless of how a repo classifies that Python: hook scripts, `dev-tooling/` checks, and product modules ALL count, so there is NO "no product Python" exemption. It MUST be enforced at BOTH layers -- the local `lefthook` commit-msg gate AND an authoritative CI check (given the full history its commit-range form needs) -- because a hook-only gate is bypassable and CI is the source of truth. The SOLE exemption is a governed repo with ZERO first-party Python (e.g. a Rust component such as the operator console), which is beyond the Python gate's reach and instead carries a language-appropriate red-green analogue tracked as its own work-item. New adopters inherit this wiring through the `templates/impl-plugin/` copier scaffold.

No '## ' (H2) heading change, so tests/heading-coverage.json is unaffected.
