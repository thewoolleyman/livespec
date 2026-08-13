---
topic: self-hosted-capacity-pool-and-execution-proof
author: claude-opus-5-fleet-ci-runner-pool
created_at: 2026-08-13T00:55:00Z
---

## Proposal: Specify self-hosted capacity as a multi-host pool, and require execution proof before routing

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"Self-hosted CI runner host requirements" is written throughout in the singular — "a host", "a conforming host", "a registered host". Every requirement in it is correct, but the section never says whether self-hosted capacity is ONE host or SEVERAL, and the fleet has now committed to several: `poweredge-xubuntu` is serving as the first member of a pool that `hetzner-prod` and `gmktec` are intended to join. Two things follow that the section does not currently state, and this proposal adds both:

1. **Capacity is a label-keyed POOL that may span hosts**, and every runner carries a shared pool label plus a host-unique label.
2. **A host is not proven by registering.** It is proven by EXECUTING a job. Registration and online status are cheap and mean almost nothing.

### Motivation

Both additions come from provisioning the fleet's first conforming host end-to-end on 2026-08-13 rather than from reasoning about the text.

**On pooling.** The singular phrasing invited a wrong architectural framing that was actually proposed in session and had to be corrected: that a second host would SUPERSEDE the first. It does not — GitHub dispatches a job to any idle runner carrying every label the job names, so hosts are co-members and capacity is additive. Recording that removes a false either/or that the current wording does nothing to prevent, and it strengthens the §Availability clause: with more than one member, one host's loss degrades throughput instead of stalling the lane.

**On the per-host label.** A pool keyed solely on a shared label cannot be steered. Reproducing a host-specific failure, validating a newly joined host before it takes shared traffic, and draining one host all require addressing ONE member. Retrofitting a host-unique label after several hosts are registered means re-minting every registration in every repository, so the obligation belongs in the contract before the pool grows rather than after.

**On execution proof.** This is the one with a measured cost. During provisioning, four separate containment tests reported FAIL on a host whose containment was in fact intact — the suite dropped privileges to the runner identity and inherited a working directory that identity could not traverse, so the probes captured empty output and empty compared unequal. The same host, same commit, same image scored 5 fail from one directory and 0 fail from another. Registration had already succeeded at that point and the runner reported online; neither fact had any bearing on whether the host could run a job. Only executing one settled it. The existing §Availability clause already requires the fleet to observe that a host has STOPPED taking jobs; it does not require anyone to establish that the host ever STARTED.

### Proposed Changes

ONE EDIT to `SPECIFICATION/non-functional-requirements.md`, replacing text that exists verbatim in the live file today.

**Edit — append two paragraphs after the Availability clause.** Replace this paragraph exactly:

```
**Availability MUST NOT become a merge dependency.** Because §"CI as a merge gate (branch protection)" makes a single all-green gate the sole required check, a self-hosted host that stops reporting does not fail anything — it simply never reports, and every merge in that repository waits indefinitely on a check that will not arrive. A repository routing gating jobs to self-hosted capacity MUST therefore retain a route returning those jobs to hosted capacity that requires no specification revision to take, and the fleet MUST be able to observe that a registered host has stopped taking jobs rather than inferring it from jobs accumulating in a queue.
```

with:

```
**Availability MUST NOT become a merge dependency.** Because §"CI as a merge gate (branch protection)" makes a single all-green gate the sole required check, a self-hosted host that stops reporting does not fail anything — it simply never reports, and every merge in that repository waits indefinitely on a check that will not arrive. A repository routing gating jobs to self-hosted capacity MUST therefore retain a route returning those jobs to hosted capacity that requires no specification revision to take, and the fleet MUST be able to observe that a registered host has stopped taking jobs rather than inferring it from jobs accumulating in a queue.

**Self-hosted capacity is a POOL, and it MAY span more than one host.** This section is otherwise written in the singular, and that phrasing describes what each host owes rather than how many there are. The forge dispatches a job to any idle runner carrying every label the job names, wherever that runner runs, so hosts serving the same label are co-members whose capacity is ADDITIVE — a further host never supersedes an existing one. Each host runs its own supervisor and mints its own registrations; no coordination between hosts is required, and none MUST be introduced. Multiple members do not relax the hosted-capacity route required above, which covers every member being unavailable at once, but they do make reaching it rarer.

**Every runner MUST carry both a shared pool label and a host-unique label.** Repository workflows target the shared label, so a job lands wherever there is capacity. The host-unique label exists so that ONE member can still be addressed: to reproduce a failure that occurs on a single host, to validate a newly joined host before it takes shared traffic, and to drain a member by routing away from it. A pool keyed only on the shared label can be grown but not steered. This obligation is stated ahead of need because retrofitting a host-unique label once several hosts are registered requires re-minting every registration in every repository, whereas adding it at first registration costs nothing.

**A host is proven by EXECUTING a job, not by registering one.** Before a repository routes gating jobs to a host, that host MUST have run a job to completion under the execution identity above, and that job MUST be one that cannot block a merge — a non-gating job addressed to the host-unique label satisfies both. A successful registration, an `online` status, and a visible runner each cost nothing and establish nothing: a runner can register, report online, and fail every job handed to it, for reasons — an unreadable working directory, a missing launch file, an unsatisfiable image — that only running one surfaces. The §Availability clause above obliges the fleet to observe that a host has STOPPED taking jobs; this clause obliges it to establish that the host ever STARTED.
```

**Why this direction rather than a rewrite.** The section's existing requirements are unchanged and correct; what is missing is the cardinality they are silent about and one proof obligation. Appending is therefore preferred to rewriting the singular phrasing throughout, which would touch every clause to say something none of them is currently wrong about.

**What a ratifier should confirm rather than take on trust.** The execution-proof clause is written as a HARD precondition on routing, not as guidance. That is deliberate and it binds: a repository may not route gating jobs to a host on the strength of registration alone, even when the host is visibly online. A ratifier who wants that softer should amend the clause rather than reject the edit — but note that softening it re-admits precisely the failure this proposal was written from, where a host looked healthy by every cheap signal available and was not.

**Scope note — three things deliberately NOT proposed.** First, nothing here names a host, a label value, a provider, or a count; the pool's membership is operational state, not contract. Second, the architecture clause requiring x86_64 Linux is untouched, even though the maintainer has stated an intent to carry runner capacity on macOS machines as well (2026-08-13, while tagging tailnet hosts for this pool — the tagging is recorded in `thewoolleyman/tailscale-admin`, not in this repository, so no artifact here anchors it and no count is asserted). Apple Silicon is arm64 rather than x86_64, so those machines are out of contract for gating CI as the clause stands. Whether to publish arm64 images or to scope them to the non-gating auxiliary lane the Scope section already carves out is an open decision that should be made on its merits, not settled as a side effect of this proposal. Third, the provisioning defects found while establishing the first host are implementation bugs fixed in `livespec-dev-tooling`, not contract, and are recorded there and in the `fleet-ci-runner-pool` plan rather than here.
