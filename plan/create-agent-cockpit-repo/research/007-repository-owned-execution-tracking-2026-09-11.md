# Repository-owned execution tracking and Phase 0/1 routing

Date: 2026-09-11

Plan epic: `livespec-livyxu`

Target repository: `thewoolleyman/agent-cockpit-info`

This note records the execution-tracking decision taken after the repository
bootstrap landed. It is subordinate to the authoritative implementation
constraints in `006-post-landing-review-closure-2026-09-10.md`; where older
notes discuss a future ledger without choosing its substrate, this note closes
that choice for the repository's initial standalone phase.

## Decision

Use the target repository's GitHub Issues tracker as its repository-owned work
tracking seam. Milestone
[`Phase 0/1 — executable cockpit contract`](https://github.com/thewoolleyman/agent-cockpit-info/milestone/1)
and tracker
[#2](https://github.com/thewoolleyman/agent-cockpit-info/issues/2)
hold the first dependency-layered execution graph.

Do not provision a Beads/Dolt tenant, install a LiveSpec orchestrator contract,
or add a runtime dependency on `livespec`, `livespec-dev-tooling`, or Fabro.
The reviewed architecture explicitly deferred LiveSpec adoption until after a
second-host proof and the appearance of an independently governed backlog.
Creating a ledger tenant merely to file the first slices would reverse that
decision before its reconsideration gate. GitHub Issues is already enabled,
travels with the private repository, supports durable links to pull requests
and acceptance evidence, and introduces no cockpit-host runtime service.

The source plan in `livespec` remains the planning and completeness authority.
The GitHub milestone becomes the implementation-status authority for the
transferred Phase 0/1 work. It must not be mirrored into plan files or a second
status queue.

## Routed dependency graph

The milestone contains one tracker and these gradeable slices:

1. [#3 — lock standalone architecture and autonomous safety defaults](https://github.com/thewoolleyman/agent-cockpit-info/issues/3).
2. [#4 — scaffold the pinned Ansible repository and validation toolchain](https://github.com/thewoolleyman/agent-cockpit-info/issues/4), blocked by #3.
3. [#5 — define requirements-traceability and measured-surface ledgers](https://github.com/thewoolleyman/agent-cockpit-info/issues/5), blocked by #3 and #4.
4. [#6 — inventory the current cockpit with read-only measurement probes](https://github.com/thewoolleyman/agent-cockpit-info/issues/6), blocked by #5.
5. [#7 — define state, external-seam, evidence, identity, and promotion contracts](https://github.com/thewoolleyman/agent-cockpit-info/issues/7), blocked by #3, #4, and #5.
6. [#8 — build safe contract fakes for identities and external services](https://github.com/thewoolleyman/agent-cockpit-info/issues/8), blocked by #7.
7. [#9 — implement bare-Ubuntu bootstrap and sample inventory validation](https://github.com/thewoolleyman/agent-cockpit-info/issues/9), blocked by #4, #7, and #8.
8. [#10 — add cockpit-doctor and close the Phase 1 CI gate](https://github.com/thewoolleyman/agent-cockpit-info/issues/10), blocked by #5 through #9 as recorded on the issue.
9. [#11 — prepare the PowerEdge G-1a feasibility-spike handoff](https://github.com/thewoolleyman/agent-cockpit-info/issues/11), blocked by #6, #7, #8, and #10.

Every issue cites this plan and commit
`87501e5beab143ffac20bafdc453183779ae4d0d`, names executable acceptance
criteria, and records its prerequisites. Tracker #2 is the only roll-up; its
checkboxes link directly to the implementation issues.

## Scope and safety boundary

This routing admits only the Phase 0/1 work authorized by research note 006:
repository scaffolding, schemas, inventories, read-only measurement probes,
test fakes, a non-secret bootstrap path, sample inventories, diagnostics and
CI, and the G-1a design handoff.

The milestone explicitly excludes G-1b application, autonomous G0-G3 cluster
activation, credential rotation or resealing, production/test identity
creation, unique persistent state, content capture, VPS provisioning, active
work migration, second-host rollout, and old-VPS deprecation. Issue #11 can
file and record a host-owner work item in `poweredge-xubuntu-info`, but cannot
run the spike or create a namespace, credential, cluster object, host artifact,
device exposure, port, or process.

The first ripe item is #3. Downstream items remain blocked by the dependency
lines in their bodies; implementation sessions must not skip those edges or
weaken an acceptance gate to manufacture readiness.

## Completion and reconsideration

The transferred Phase 0/1 work is complete only when all milestone issues are
closed by merged pull requests, `just check` is green at the milestone tip,
the bootstrap reaches pinned Ansible, sample inventories validate, the
requirements and measured surfaces are completely classified, test lanes use
no production credentials, and issue #11 has recorded a concrete
`poweredge-xubuntu-info` work item without applying host or cluster changes.

LiveSpec/Beads/Fabro adoption remains a later architecture question. Reconsider
it only after the second numbered cockpit proves the fleet abstraction and the
repository has a genuinely independent governed backlog; do not infer adoption
from this plan's use of a LiveSpec ledger for cross-repository coordination.
