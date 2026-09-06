---
topic: ci-host-rebuildable-from-bare-metal
author: claude-fable-5-1 (k3s-on-gmktec-for-vps-usage plan session)
created_at: 2026-09-06T12:09:03Z
---

## Proposal: A host carrying fleet CI is rebuildable from bare metal by a committed, rehearsed procedure that a per-host profile parameterizes

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Add one clause to §"Self-hosted CI runner host requirements" stating a host-observable property: every step that takes a fleet CI host from powered-on hardware with empty storage to a pool member taking jobs MUST be performed by a procedure committed to the repository that provisions the host's job runtime; the procedure MUST be re-runnable and MUST refuse destructive steps against populated storage without explicit consent in that invocation; it MUST take every host-specific value from a per-host profile that is data, so a second host is a second profile and never a second procedure; the host's own record carries hardware facts and the profile's values and never the procedure; a procedure is proven by executing it, and one not rehearsed since it last changed is unproven; a backup-and-restore path MAY exist for data recovery but MUST NOT substitute for the procedure. Add one `## ` scenario heading to scenarios.md carrying three Gherkin scenarios for the property, with the matching `tests/heading-coverage.json` TODO entry naming the integration tier, co-edited atomically at revise.

### Motivation

Maintainer direction of 2026-09-06 (livespec plan k3s-on-gmktec-for-vps-usage, epic livespec-sab5gn, research/002; goal 0 of that plan): GitOps is the plan's number-one priority — the fleet's dedicated CI hosts MUST be rebuildable from scratch, from git, scripted end to end, with bare metal to CI node as the chosen definition of "from scratch"; no live host is changed by hand. The section already makes the STORAGE TIERS reproducible from the provisioning repository (the clause beginning "**Storage tiers on a host that runs jobs as containers.**": "That mount configuration, the identity-to-mountpoint binding, and the job runtime's refusal to start on an absent storage tier MUST be reproducible from the repository that provisions the host's job runtime and idempotently re-appliable") and proves a host by EXECUTING a job, but states no property for the host as a whole: a host could conform to every clause in the section with its storage controller, partition table, volume groups and base operating system reached by hand from a rescue medium and only the END STATE written down. That is exactly what the independent gitops-rebuildability review of the fleet CI host found on 2026-09-06 (recorded on ledger items livespec-ifwnqj.3, .4 and .5, re-parented to livespec-sab5gn the same day): everything from a prepared disk onward was in git and boot-proven, while the first mile — the RAID virtual disk, the GPT and ESP, the volume group and its logical volumes, their filesystems — had been run by hand from a recovery USB on 2026-09-04, with only the resulting layout recorded in the host's own record (poweredge-xubuntu-info AGENTS.md §Storage) and the committed restore script refusing to partition by design. Stating the property here keeps the section's opening rule: the fleet realizes it in livespec-dev-tooling (the recipe's home, its per-host profiles, and its rehearsal obligation are that repository's, proposed there as the matching provisioning-repository clause), and the per-host info repositories keep the hardware facts. The property is scoped to hosts carrying fleet CI, which is this section's scope; the fleet's factory hosts and the pre-existing operator VPS are governed elsewhere and are not reached by this clause. Per the authoring discipline, a load-bearing property needs a scenario: the new scenario heading and its heading-coverage entry are part of this proposal, not a follow-up.

### Proposed Changes

**Change 1 — the new clause in SPECIFICATION/non-functional-requirements.md.** In §"Self-hosted CI runner host requirements", insert the following new clause paragraph immediately AFTER the clause that begins:

> **Availability MUST NOT become a merge dependency.**

(and therefore immediately BEFORE the clause that begins "**Self-hosted capacity is a POOL, and it MAY span more than one host.**"). The inserted paragraph, verbatim:

> **A host carrying fleet CI MUST be rebuildable from bare metal by a committed procedure.** Every step that takes the host from powered-on hardware with empty storage to a pool member taking jobs — storage-controller and volume configuration, partitioning and volume management, base operating-system installation, the node's job runtime and every node-local mechanism, and the cluster-side state the host rebuilds on boot — MUST be performed by a procedure committed to the repository that provisions the host's job runtime. The procedure MUST be re-runnable: against a host already in its declared state it MUST change nothing, and a step that destroys existing storage MUST refuse to run against a populated volume unless the operator confirms that destruction explicitly in that invocation. A step performed by hand, from memory, or from an operator's shell history — however carefully its end state is recorded afterwards — is a defect in the procedure, not an accepted gap, and the host is out of contract until the step is scripted. The procedure MUST take every host-specific value it needs — storage device and controller identities, the role-labeled tiers and their placement, network interfaces and addresses, the node's admission capacity — from a per-host profile that is DATA the one procedure consumes, so that a second host is a second profile and never a second procedure. The host's own record MUST carry the hardware facts and the profile's values and MUST NOT carry the procedure, so that the record and the procedure cannot become two accounts of the same host. A procedure is proven by EXECUTING it: a rehearsal that produces a host the pool then proves by executing a job, per the proving clause below. A procedure that has not been rehearsed since it last changed MUST be treated as unproven. A backup-and-restore path MAY exist beside the procedure for data recovery and MUST NOT substitute for the procedure as the way the host's configuration is reproduced. This is a PROPERTY — the host-reproduced-from-the-repository relation — and the recipe, its profiles, and its rehearsal obligation are recorded by the repository that provisions the host's job runtime, never in this specification. Maintainer-directed 2026-09-06.

No `## ` heading is added, changed, or removed in non-functional-requirements.md (the section is an H3 and the clause is a bold-led paragraph in its existing style).

**Change 2 — the scenario in SPECIFICATION/scenarios.md.** Append the following new `## ` section immediately AFTER the section headed `## Drift acceptance under each mode` (the file's final section), verbatim:

> ## A fleet CI host is rebuilt from bare metal by the committed procedure
>
> ```gherkin
> Feature: Rebuilding a fleet CI host from bare metal by the committed procedure
>
> Scenario: A second host is a second profile, never a second procedure
>   Given the repository that provisions the pool's job runtime carries one rebuild procedure and one per-host profile per pool member
>   When an operator runs the procedure against a host with empty storage, naming that host's profile
>   Then the host's storage layout, base operating system, job runtime, and node-local mechanisms reach the profile's declared state with no step performed by hand
>   And the host joins the pool and is proven by executing a non-gating job addressed to it alone
>
> Scenario: A step reached by hand is a defect in the procedure
>   Given a pool member whose recorded end state includes a step that the committed procedure does not perform
>   When the procedure is rehearsed against empty storage
>   Then the rehearsal does not reproduce that state
>   And the host is out of contract until the step is scripted and the rehearsal reproduces it
>
> Scenario: The procedure is safe to re-run and refuses to destroy populated storage
>   Given a pool member already in its profile's declared state
>   When the procedure is re-run against it without explicit destruction consent in that invocation
>   Then it changes nothing
>   And every step that would destroy existing storage refuses to run
> ```

**Change 3 — the heading-coverage co-edit, at revise time.** Because Change 2 adds one `## ` heading to scenarios.md, the revise payload's `resulting_files[]` MUST include `../tests/heading-coverage.json` with one added entry, in the file's existing shape: `{"heading": "## A fleet CI host is rebuilt from bare metal by the committed procedure", "spec_root": "SPECIFICATION", "spec_file": "scenarios.md", "test": "TODO", "reason": "Ratifies the rebuild-from-bare-metal property for fleet CI hosts (maintainer-directed 2026-09-06, plan k3s-on-gmktec-for-vps-usage). A scenario describes end-to-end behavior, so its test MUST resolve to the integration tier or above: the mapped test is an integration-tier rehearsal of the committed rebuild procedure against a per-host profile, filed under the owning epic, and this TODO is replaced by that test id when it lands.", "work_item": "livespec-sab5gn"}`. The `reason` names the integration tier as `check-heading-coverage` direction 4 requires for a scenarios.md heading.

**Drift sweep (performed while authoring; the reviewer re-derives it).** The storage-tiers clause's sentence "That mount configuration, the identity-to-mountpoint binding, and the job runtime's refusal to start on an absent storage tier MUST be reproducible from the repository that provisions the host's job runtime and idempotently re-appliable, and a storage tier's physical placement is a host fact recorded in the host's own record, never in this specification." is the narrower, tier-level statement of the same relation and stays as written: the new clause generalizes it to the whole host and does not contradict it. The clause beginning "**A host is proven by EXECUTING a job, not by registering one.**" is referenced by the new clause as "the proving clause below" in words, not by anchor, and stays as written. The section's opening rule (properties here, mechanisms in the provisioning repository) is preserved: the clause names no script, path, or tool. No count, enumeration, or cross-reference elsewhere in the section is affected. The pending proposal ci-host-admission-cap-derivation inserts its clause at a different anchor (immediately before the Availability clause), so the two proposals' insertion points do not overlap and either may ratify first.
