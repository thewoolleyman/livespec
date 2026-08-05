---
topic: request-budget-discipline
author: claude-opus-5
created_at: 2026-08-05T03:47:46Z
---

## Proposal: Register Request-budget-discipline as a Conformance-Pattern member

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add Request-budget-discipline to the Conformance Pattern's concern registry as a `baseline` concern binding every fleet repository and, mirroring Pin-freshness, Plugin-currency, and Shell-and-Justfile-discipline, extended to opted-in adopters through their `posture`. The registry's closing sentence, which names which members have their five slots filled, is re-derived in lockstep.

### Motivation

The fleet observes GitHub API request-budget best practices by convention rather than by mechanism. §"Fleet secrets" already carries a ratified **GitHub App request budget** paragraph covering budget-as-shared-resource, recurring rate-limit recording, and distinguishing primary exhaustion from auth and secondary failures. That paragraph is not a Conformance-Pattern registry member, so it has no Mechanism, Installer, Verifier, or Exemption slot, and nothing makes it provable across governed repositories. Per §"Conformance Pattern", "A concern is not adopted until all five slots are filled". A 2026-08-04 incident in an adopter repository exhibited two failure modes the existing paragraph does not prevent: unconditional polling against the primary limit, and an unpaced bulk-mutation burst against the SECONDARY limit, which the existing paragraph only requires be DISTINGUISHED, never avoided.

### Proposed Changes

ONE edit, in §"Conformance Pattern", in the paragraph beginning "Further recognized members, each the same five-slot shape:".

The replace-target below deliberately begins mid-sentence at the enumeration's final list item and runs to the end of the paragraph, because the list item ends with a sentence-final PERIOD. A narrower target starting at "A named member" would splice a lowercase conjunction directly after that period and produce ungrammatical text. There is exactly ONE resulting text; nothing is left to ratifier discretion.

Replace this exact text (it occurs exactly once):

— see §"Shell and Justfile discipline"). A named member is not adopted until all five of its slots are filled; Shell-and-Justfile-discipline's five slots are filled in its constraint section below.

with exactly this text:

— see §"Shell and Justfile discipline"), and **Request-budget-discipline** (a `baseline` concern binding every fleet repository and, mirroring Pin-freshness, Plugin-currency, and Shell-and-Justfile-discipline, extended to opted-in adopters through their `posture`, bound where an adopter's `posture` is `released`; a governed repo's automated GitHub API access stays within the primary and secondary request budgets it shares with every other repo on the same App installation — see §"Request-budget discipline"). A named member is not adopted until all five of its slots are filled; Shell-and-Justfile-discipline's and Request-budget-discipline's five slots are filled in their constraint sections below.

No `## ` heading is added, changed, or removed, so `tests/heading-coverage.json` needs no co-edit.

## Proposal: Fill the five slots in a new Request-budget discipline section

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new `### Request-budget discipline` constraint section filling all five Conformance-Pattern slots for the concern registered by the sibling proposal. It single-sources the existing **GitHub App request budget** paragraph as part of its Contract rather than restating it, and adds the obligations that paragraph does not carry: conditional reads on polling paths, secondary-limit-aware mutation pacing, a rate-limited 403 that cannot collapse into an empty success, and a reserved budget floor.

### Motivation

Same incident as the sibling proposal. The gaps in the existing paragraph, each mapped to an observed failure: (1) nothing requires conditional requests, though GitHub documents that a 304 response does not count against the primary limit, making repeat reads of unchanged data effectively free; (2) nothing constrains mutation RATE, though mutating requests are metered at a higher point cost against a per-minute ceiling, so a bulk sequence trips it regardless of remaining hourly budget; (3) nothing requires a single canonical client, which is why consumption is unattributable per caller and why every call site must independently remember the rules; (4) nothing forbids reading a rate-limited 403 as an empty result, which produces confident false negatives — the recorded failure shape in both this incident and the item that motivated the existing paragraph; (5) nothing reserves budget, so a bulk job can starve a time-critical read sharing the bucket.

### Proposed Changes

Insert a new `### Request-budget discipline` section immediately AFTER the paragraph beginning "**Per-consumer Anthropic API key naming.**" and immediately BEFORE this exact line (which occurs exactly once):

### Fleet membership contract

The section body to insert is delimited below by lines of three hyphens. Those delimiter lines are NOT part of the text and MUST NOT be inserted into the spec.

---

### Request-budget discipline

This contributor-facing constraint fills the Conformance Pattern's five slots for the `baseline` **Request-budget-discipline** concern (§"Conformance Pattern"). It binds every fleet repository and, mirroring Pin-freshness, Plugin-currency, and Shell-and-Justfile-discipline, opted-in adopters whose `posture` is `released`. It governs automated GitHub API access performed by livespec-supplied machinery; it neither lints nor constrains an adopter's or third-party consumer's own first-party code beyond the calling-API contract (`constraints.md` §"Constraint scope").

**Contract.** The normative invariant is the **GitHub App request budget** paragraph of §"Fleet secrets — 1Password Environment as canonical source" — budget as a finite shared resource, recurring rate-limit recording to a durable local signal, and primary-exhaustion diagnosis distinct from permission, authentication, and secondary-limit failures — EXTENDED by the four obligations below. That paragraph remains the single source for what it already states; this section does not restate it.

- **Conditional reads.** A polling path against a resource that is usually unchanged MUST issue conditional requests, because an unchanged-resource response does not consume primary budget. A caller that re-reads unchanged state at interval without a validator is non-conforming.
- **Paced mutations.** Automated paths MUST stay within the secondary limits as well as the primary ones — the published per-minute point ceiling — against which mutating requests are metered at a higher point cost than reads — and the published concurrency ceiling. A bulk mutation sequence MUST therefore be paced. Tripping a secondary limit is non-conforming even when primary budget remains.
- **Unmeasurable is not empty.** A rate-limited response MUST surface to the caller as an explicitly unmeasurable outcome, distinct from both success and a genuine empty result, and MUST NOT be representable as a falsy empty collection. A caller that reports "no results" from a rate-limited read is non-conforming: the reading is absent, not negative.
- **Reserved floor.** Bulk or deferrable automated work MUST be refusable below a declared remaining-budget floor, so it cannot starve a time-critical read sharing the same bucket. Pacing alone does not prevent starvation; a paced bulk job still drains the bucket.

**Mechanism.** One canonical request client, supplied by `livespec-runtime` (§"Shared runtime — livespec-runtime") and reused rather than reimplemented per the pattern's reuse-by-default rule (§"Conformance Pattern"). Automated GitHub access routes through it; an ad-hoc direct call is the non-conforming shape the Verifier detects.

**Installer.** The idempotent wiring that puts the Mechanism and its agent-facing guard in place, reached through the governed-repo lifecycle reconcile (§"Governed-repo lifecycle"). A channel each repository must hand-wire in its own committed agent settings MUST NOT be the wiring for this concern: such a channel reaches only the population that authors it, which is the failure this concern was registered in response to.

**Verifier.** The shared, fail-closed check wired into `just check` that rejects a direct GitHub API call outside the Mechanism in a fleet repository's own first-party code. Its cross-repository half is an entry in the fleet-conformance sweep inventory (§"Fleet membership contract"); a NEW bespoke check added to the upstream enforcement-suite repository that reads into a downstream consumer MUST NOT be the realization. For an opted-in adopter the sweep asserts the PRESENCE of the Mechanism and guard wiring only, and never inspects that adopter's own first-party code. The Verifier MUST report the scope it scanned and MUST fail rather than pass when that scope is empty, so it cannot report green over zero files.

**Exemption.** Two declared, fail-closed variations, never silent relaxations. (1) The credential-minting path legitimately calls the App endpoints directly, because it produces the credential the Mechanism uses; it is exempt by an in-place declaration naming that reason. (2) When remaining budget is not determinable, the caller warns loudly and proceeds under one declared severity lever rather than failing open silently — a severity lever, not an invariant relaxation, per the pattern's hard rule.

---

This edit adds only a `### ` heading, so `tests/heading-coverage.json` needs no co-edit.
