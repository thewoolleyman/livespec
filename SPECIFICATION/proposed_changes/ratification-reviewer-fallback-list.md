---
topic: ratification-reviewer-fallback-list
author: claude-opus-5
created_at: 2026-08-26T09:45:00Z
---

## Proposal: An ordered ratification-reviewer list, so one model's unavailability cannot halt fleet ratification

### Target specification files

- SPECIFICATION/spec.md

### Summary

Widen `ratification_reviewer_model` from a single model designation to an ORDERED list of designations tried in order, require the ratification evidence to record which reviewer actually ran and whether it was a fallback, and keep the existing escalation when every listed reviewer is unavailable. A single string remains valid and means a one-element list, so no adopter config breaks.

### Motivation

**This is a measured outage, not a hypothetical.** On 2026-08-26 a `livespec-runtime` ratification review was spawned under `ratification_review: auto-spawn` with `ratification_reviewer_model: "fable"`. The reviewer died mid-review on an account usage limit ("You've reached your Fable 5 limit") and returned no verdict. The driving session behaved exactly as this specification requires — it treated absence of a verdict as escalation rather than as NO BLOCKERS, refused to substitute a different model because the revise CLI validates evidence's `reviewer_model` against the configured designation, and refused to hand-write evidence for a review that never happened. The current text produced correct behaviour. The problem is what that correct behaviour costs when the designated model is unavailable fleet-wide.

**The blast radius is five of six repositories, and it includes this one.** Measured at `origin/master` on 2026-08-26: `thewoolleyman/livespec` (this repo, `"fable"`), `livespec-runtime` (`"fable"`), `livespec-console-beads-fabro` (`"fable"`), `livespec-overseer` (`"fable"`), and the `homelab` adopter (`"claude-fable-5"`) are all hard-blocked from completing any ratification while Fable capacity is exhausted. Only `livespec-orchestrator-beads-fabro` (`"sonnet"`) can ratify — confirmed live, since its ratification reviewer ran normally in the same minute another repo's died.

Two consequences make this structural rather than an inconvenience:

- **The supervisory surface is blocked.** `livespec-overseer` supervises the other repositories, so a single model's outage stops spec ratification in the repo that governs the others.
- **The fix cannot be ratified during the outage that motivates it.** `ratification_reviewer_model` is defined here, in this file, and this repository is itself `"fable"`-designated. A fallback policy is a change to this specification, so the single-model dependency blocks the ratification of its own remedy. That circularity is the sharpest argument for the change: an availability dependency on the critical path of the spec-change mechanism can wedge the mechanism used to remove it.

**What this proposal does NOT relax.** The independent-review floor is untouched. A fallback is a different independent reviewer, never a self-review, never the deciding session, and never a hand-written attestation. Exhausting the list still escalates to maintainer input, so "no reviewer available" continues to stop the revise rather than degrading into a weaker form of evidence. The intent is to remove a single point of failure from the mechanism, not to lower the bar the mechanism enforces.

**Why the substitution must be recorded.** If a fallback can run silently, the evidence no longer answers "who reviewed this" without consulting configuration that may since have changed. Recording the attempted-and-unavailable designations alongside the one that ran keeps a fallback auditable after the fact, and makes a substitution a visible event rather than an invisible degradation.

### Proposed Changes

**(1)** In `SPECIFICATION/spec.md`, in the `spec_governance` settings table, replace the `ratification_reviewer_model` row:

> | `ratification_reviewer_model` | non-empty string matching `^[A-Za-z0-9._/-]+$` | absent/unconfigured | no |

with:

> | `ratification_reviewer_model` | non-empty string matching `^[A-Za-z0-9._/-]+$`, or a non-empty ordered array of such strings | absent/unconfigured | no |

**(2)** In `SPECIFICATION/spec.md`, in the paragraph beginning `effective_ratification_review MUST enforce the unconditional independent-review floor`, replace the sentence:

> A missing, malformed, or unavailable reviewer-model designation requires maintainer input in either mode.

with:

> A reviewer-model designation MAY be a single model or an ORDERED LIST of models. `effective_ratification_review` MUST try designations in the order given and MUST use the first that is available, so that one model's unavailability does not by itself block ratification. A fallback designation is subject to every requirement the first designation is: it MUST be an independent reviewer, MUST NOT be the deciding session, and MUST NOT be substituted by an attestation the reviewer did not produce. The ratification evidence MUST record the designation that actually performed the review and, when it was not the first, that a fallback occurred and which earlier designations were unavailable. A missing or malformed designation, or the exhaustion of every designation in the list without an available reviewer, requires maintainer input in either mode.

**(3)** In `SPECIFICATION/spec.md`, in the same paragraph, replace the sentence:

> Repo `thewoolleyman/livespec` MUST designate `fable` in its root `.livespec.jsonc` when this contract is implemented.

with:

> Repo `thewoolleyman/livespec` MUST designate `fable` first in its root `.livespec.jsonc` when this contract is implemented, and MUST designate at least one further model after it so the repository that defines this key is not itself haltable by one model's unavailability.

### Consequences for adopters

A bare string remains valid and is interpreted as a one-element list, so every existing `.livespec.jsonc` continues to resolve exactly as it does today, and an adopter that wants no fallback simply keeps its current value. Adopters wanting the resilience add one entry. The `homelab` adopter's maintainer has already directed the order `fable`, then `opus`, for its own repositories; this proposal fixes the mechanism, not any adopter's chosen order.

Evidence written before this change lacks the fallback fields. Since it also records a single reviewer that necessarily WAS the first designation, such evidence remains conforming without rewriting, and the new fields are required only of evidence produced after the change.
