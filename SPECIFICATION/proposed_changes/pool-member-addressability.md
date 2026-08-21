---
topic: pool-member-addressability
author: claude-opus-5
created_at: 2026-08-21T22:32:27Z
---

## Proposal: Restate pool-member addressability as a property, so ARC-provisioned capacity can satisfy it at all

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The §"Self-hosted CI runner host requirements" clause **Every runner MUST carry both a shared pool label and a host-unique label** is written as a LABEL MECHANISM, not as a property. Nine fleet repositories now gate their merges on ARC `gha-runner-scale-set` capacity, whose runners register with an EMPTY label array and are addressed by scale-set name — they cannot carry a host-unique label, and do not appear in the repository runners API at all. The section's own stated style is that "Every requirement is stated as a host-observable PROPERTY rather than as a package name, service unit, or distribution mechanism", and this is the one clause in the section that breaks that rule. This amendment restates the requirement as the ADDRESSABILITY property it actually wants — that an individual pool member remain separately addressable for reproduction, validation, and drain — and lets each provisioning mechanism satisfy it by its own native means: labels for a JIT pool, per-member scale sets or placement constraints for ARC. The dependent sentence in the **host is proven by EXECUTING a job** clause, which today satisfies itself by reference to "the host-unique label", is amended in the same pass so no unamended statement is left contradicting the change.

### Motivation

Measured against live state on 2026-08-21, during the post-cutover conformance audit of this section (`livespec-s43svm.40`, filed from that audit).

The clause is SATISFIED on the podman-era pool it was written for: those 482 registrations carry `[self-hosted, local-ci, poweredge]` — `local-ci` shared, `poweredge` host-unique — verified live on `livespec-console-beads-fabro`, whose sixteen registered runners all carry exactly that set.

It is NOT SATISFIABLE by the capacity the fleet now gates on, and not because anyone got it wrong. In ARC's `gha-runner-scale-set` mode a runner registers with an empty label array; jobs select it by scale-set name through the repository's `CI_RUNNER_LABELS` variable. Querying `livespec-console-beads-fabro`'s runners returns exactly the sixteen podman-era registrations and NONE of the live `livespec-console-beads-k3s-*-runner-*` pods that were serving jobs at that same moment. So the fleet's merge-gating capacity is addressed by a mechanism this clause does not describe, using a label model it cannot participate in.

Why this is not cosmetic. The clause states its own reason for existing ahead of need: "retrofitting a host-unique label once several hosts are registered requires re-minting every registration in every repository, whereas adding it at first registration costs nothing." That argument is entirely about the label model. Under ARC the equivalent question — how do you steer, validate, or drain ONE host when the pool spans more than one — is answered by scale-set placement (node selectors, taints, per-host scale sets), and none of that is written down anywhere in this specification. Today the pool is a single host, so nothing is broken and nothing is urgent. The clause exists precisely for the moment that stops being true, and in its present form it will not help then: an operator reading it will go looking for a host-unique LABEL that ARC cannot provide, on capacity that does not appear in the API they would look in.

The amendment deliberately PRESERVES the ahead-of-need obligation rather than relaxing it, because the retrofit argument survives translation: adding a per-member addressing path at first provisioning is cheap, and adding one to an established multi-member pool is not, whichever mechanism provides it.

What is NOT claimed. No violation of the fork-exclusion precondition is asserted here (that was a separate finding of the same audit, `livespec-s43svm.39`, repaired 2026-08-21). No claim that steering is currently impossible — with one host it is moot, and per-repo scale sets already provide per-repo steering. No claim that the podman-era clause was wrong when written.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, §"Self-hosted CI runner host requirements":

**1. Replace the clause beginning "**Every runner MUST carry both a shared pool label and a host-unique label.**"** — that is, the whole paragraph whose text is:

"**Every runner MUST carry both a shared pool label and a host-unique label.** Repository workflows target the shared label, so a job lands wherever there is capacity. The host-unique label exists so that ONE member can still be addressed: to reproduce a failure that occurs on a single host, to validate a newly joined host before it takes shared traffic, and to drain a member by routing away from it. A pool keyed only on the shared label can be grown but not steered. This obligation is stated ahead of need because retrofitting a host-unique label once several hosts are registered requires re-minting every registration in every repository, whereas adding it at first registration costs nothing."

with:

"**Every pool member MUST be separately addressable, in addition to being reachable through the pool.** Repository workflows target the pool, so a job lands wherever there is capacity. Separate addressability exists so that ONE member can still be reached: to reproduce a failure that occurs on a single host, to validate a newly joined host before it takes shared traffic, and to drain a member by routing away from it. A pool that can be reached only as a whole can be grown but not steered.

This is a PROPERTY, and each provisioning mechanism satisfies it by its own means. A pool of individually-registered runner agents satisfies it with labels — a shared pool label every member carries, plus a label unique to each member. A pool provisioned as autoscaling runner sets satisfies it by the addressing its own selection mechanism provides — a per-member set, or placement constraints that bind a set to one member — because in that mode runners register with no labels at all and are selected by set name, so a label-based reading of this requirement would be unsatisfiable rather than merely inconvenient. Neither realization is preferred here; what MUST hold is that an operator can direct a job at one named member and at no other.

A mechanism whose members are NOT visible through the forge's runner listing does not thereby escape this requirement: it MUST document where its members ARE enumerable, because an operator who cannot enumerate the pool cannot steer it either.

This obligation is stated ahead of need. Retrofitting per-member addressing onto an established multi-member pool is expensive under every mechanism — re-minting every registration in every repository for a label-based pool, re-cutting and re-routing sets for an autoscaling one — whereas providing it at first provisioning costs nothing."

**2. In the clause beginning "**A host is proven by EXECUTING a job, not by registering one.**"**, replace the phrase:

"a non-gating job addressed to the host-unique label satisfies both"

with:

"a non-gating job addressed to that host alone, through whichever per-member addressing the preceding clause obliges, satisfies both"

This second edit is not optional polish. That clause discharges itself by naming the host-unique label specifically, so leaving it unamended would keep a live requirement whose only stated means of satisfaction is the mechanism this proposal has just stopped requiring — the exact shape of unamended-statement drift that makes a ratified change less true than it looks.
