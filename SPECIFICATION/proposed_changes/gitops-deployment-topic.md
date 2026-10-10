---
topic: gitops-deployment-topic
author: claude-fable-5-1 (gitops-deployment-discipline C1 session, livespec-vbqmdd)
created_at: 2026-09-12T05:47:33Z
---

## Proposal: A deploy-surface member or adopter carries a GitOps-deployment agent-instruction topic, enforced by the fleet-membership obligation suite

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add one clause to SPECIFICATION/contracts.md §"Fleet agent-instruction core" requiring every member or adopter whose tree carries a host-provisioning or deploy surface to carry a GitOps-deployment agent-instruction topic — a `.ai/gitops-deployment*.md` file referenced from its root `AGENTS.md` by a read-BEFORE hook line naming deployment, Ansible, GitOps, host provisioning, `kubectl`, and ssh-to-a-fleet-host — stating the six rules of the fleet GitOps deployment discipline plus that repository's own layer map; the deploy surface is derived from the tree, never declared in a manifest key; `livespec` itself carries the fleet-canonical statement of the six rules; and the obligation is enforced by the shared fleet-membership obligation suite alongside the section's existing instruction obligations (the section's closing enforcement sentence is amended to enumerate it). This proposal is DEFERRED to the follow-up plan carrying children C2 (livespec-eyjepk), C4 (livespec-hsdguf), and C7 and is NOT to be ratified by plan gitops-deployment-discipline, because ratifying a required-topic MUST while the canonical topic, the conformance row, and the adopter onboarding are deferred would state an obligation the fleet does not meet; the guard it pairs with is the sibling proposal `fleet-host-mutation-guard`.

### Motivation

Epic livespec-qurhq2, child livespec-vbqmdd (C1); design and rationale in livespec `plan/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md` §1–§3. On 2026-09-11/12 a session resuming plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) ssh'd into two k3s nodes and reasoned imperatively about deploying by hand, while the provisioning README in the repository it had been editing states the control node is `vps` and playbooks run from committed source; it then edited the retired shell installers instead of the Ansible role that actually deploys the file, filed the stale role as future work although Ansible IS the apply path, and asked the maintainer to change hosts by hand. Nothing in any repository's agent instructions told the session to read the provisioning model first, so the GitOps premise was not load-bearing in its reasoning. The fix that binds is an instruction obligation on every repository that carries a deploy surface, mechanically enforced: §"Fleet agent-instruction core" already states the `AGENTS.md` / `.ai/<topic>.md` convention and enforces instruction obligations through the fleet-membership obligation suite, so this clause adds one obligation in that shape. The seven host/deploy repositories the research names are onboarded as adopters under sibling children of the epic; the canonical livespec topic is child livespec-eyjepk (C2); the conformance row `gitops-deployment-topic` in `livespec-dev-tooling` is child livespec-hsdguf (C4).

### Proposed Changes

**Change 1 — the new clause.** In SPECIFICATION/contracts.md §"Fleet agent-instruction core", insert the following paragraph immediately AFTER the paragraph that ends:

> so the destination the auto-memory redirect (§"Driver-shipped hooks") points to actually exists.

and immediately BEFORE the paragraph that begins:

> Beads-backed members MUST ship a **beads-access guard**:

The inserted paragraph, verbatim:

> A member or adopter whose tree carries a **host-provisioning or deploy surface** MUST carry a **GitOps-deployment agent-instruction topic**. A deploy surface is DERIVED from the tree by the obligation suite — never declared in a manifest key — and is present when the tree carries any of: an `ansible/` directory, a `services/` directory, an `install*.sh` script at most three directory levels deep, or a host record (a repository that describes one fleet host, named `<host>-info`). The topic is a `.ai/gitops-deployment*.md` file referenced from the root `AGENTS.md` by a **read-BEFORE hook line** — a reference bullet in the `AGENTS.md` `.ai/` convention block whose text names deployment, Ansible, GitOps, host provisioning, `kubectl`, and ssh-to-a-fleet-host as the actions the topic is to be read before — so the guidance loads before the first such action rather than after a host has been touched. The topic MUST state, in that repository's own voice, the six rules of the fleet GitOps deployment discipline: (1) the provisioning model — the control node and the committed apply and drift commands — is read before any host or infrastructure action, and ssh to a host is for read-only verification only; (2) no live host is changed by hand — "this has to be done by hand on the host" names a gap in the committed automation to fix, never a task for the maintainer and never an improvised privileged action, and a deploy is a change to git followed by the committed apply; (3) a mechanism change lands in the layer the automation APPLIES — the role or playbook that deploys the changed file — never only in a runtime artifact that layer copies; (4) a layer replaced by its successor is retired, with its pre-deletion commit cited, never maintained beside the replacement; (5) the drift report is run and read before every apply, and a green repository is never taken as proof that a host matches it; and (6) a review-gated change is a DRAFT pull request until its independent review returns NO-BLOCKERS, because a repository whose automation merges on green does not wait for a human once its checks pass. The topic MUST also carry the repository's own layer map: which committed role or playbook deploys which file, from which control node. `livespec` itself MUST carry the fleet-canonical statement of the six rules at `.ai/gitops-deployment-discipline.md`, referenced from its `AGENTS.md`, so that a member's topic MAY cite it for the rules and carry only that member's layer map and fleet facts.

**Change 2 — enumerate the obligation in the section's enforcement sentence** (clause lockstep: the closing paragraph enumerates the obligations the suite enforces, so the new obligation is added to that enumeration in the same change). In the same section, replace the sentence fragment, verbatim:

> Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, and the beads-access guard MUST be enforced fleet-wide

with:

> Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, the beads-access guard, and the GitOps-deployment topic in deploy-surface members and adopters MUST be enforced fleet-wide

The remainder of that sentence and paragraph is unchanged.

No `## ` or `### ` heading is added, changed, or removed by this finding, so it contributes no tests/heading-coverage.json co-edit (the co-edit the former combined proposal `gitops-deployment-discipline` required arises from the scenario in the sibling proposal `fleet-host-mutation-guard`).
