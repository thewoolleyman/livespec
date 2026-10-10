## The maintainer's statement of what done means

Every deploy-surface repo's AGENTS.md routes to a GitOps deployment topic, the gitops-deployment-topic clause is ratified, the inventory-coverage and replaced-installer checks are armed and green in livespec-dev-tooling, and drift in any playbook raises a needs-attention item.

## Definition of Done assertions derived from that statement

- Every deploy-surface fleet repository — livespec, livespec-dev-tooling, livespec-orchestrator-beads-fabro, vps-info, poweredge-xubuntu-info, gmktec-xubuntu-info, hp-xubuntu-info, fabro-hosts, otel-collector, local-llm and homelab — carries an AGENTS.md line routing to a `.ai/gitops-deployment*.md` topic that exists in that repository.
- livespec `SPECIFICATION/contracts.md` §"Fleet agent-instruction core" on master carries the ratified gitops-deployment-topic clause requiring that topic of every deploy-surface member and adopter.
- On livespec-dev-tooling master, `just check` fails on a provisioning-inventory host that no playbook selects and on a `# Replaces <path>` claim whose path exists, with both checks armed and passing on the live tree.
- A playbook whose `just ansible-drift` reports a change makes `needs-attention-internal` raise an ansible_drift item naming the playbook and host, and a clean drift raises none.

# 000 — Scope inherited from plan gitops-deployment-discipline (2026-10-10)

This plan carries the instruction and enforcement layer that plan
`gitops-deployment-discipline` (epic `livespec-qurhq2`) deferred when the
maintainer narrowed that plan on 2026-10-10 to the k3s-node converge, the
installer retirement, and the fleet-host mutation guard. The original design
and the failure-to-fix mapping are in
`plan/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md`
section 3; the deferral and its reasons are in that plan's research/001 and in
the scope events on `livespec-qurhq2`.

## Children carried over (re-parented from livespec-qurhq2)

- C2 `livespec-eyjepk`: canonical `.ai/gitops-deployment-discipline.md`, the
  AGENTS.md hook line, and the draft-PR, apply-layer and verification
  additions to `.ai/`. Its earlier staged work was lost on 2026-10-10 and must
  be re-authored.
- C4 `livespec-hsdguf`: livespec-dev-tooling `.ai/gitops-deployment.md`, the
  checks `ansible_inventory_hosts_covered` and
  `ansible_replaced_installers_retired`, the `## Host provisioning tree` spec
  section, and the `gitops-deployment-topic` conformance row. Its worktree
  `~/.worktrees/livespec-dev-tooling/gitops-discipline-devtooling` survives
  with a Red commit; the real inventory-coverage module was lost and must be
  rewritten. The rebuild-recipe finding it also carried was ratified as
  livespec-dev-tooling v068 in the parent plan.
- C6 `livespec-7x7ia7`: the `ansible_drift` signal in
  `needs-attention-internal`. Its edit was lost and must be re-authored.
- C7 `livespec-tf27wm`: the topic and AGENTS.md line in the seven host repos.
- C8 `livespec-zyh7uo`: register the seven host repos as adopters.
- C9 `livespec-7pp3bc`: orchestrator plan prose, strict resume reads the
  read-first chain's research. Carried by the maintainer's choice; it carries
  no assertion of this plan's Definition of Done.

## Spec state on arrival

`SPECIFICATION/proposed_changes/gitops-deployment-topic.md` in livespec is
pending: it was split from the ratified fleet-host-mutation-guard proposal
(livespec v223) and deferred here. The guard clause it pairs with is live, and
the shipped guard routes its deny reason to a repository's
`.ai/gitops-deployment*.md` topic when one exists, so every topic this plan
adds is picked up by the guard with no Driver change.

## Known follow-ups recorded elsewhere that belong here

- CI never runs `check-ansible-lint` in livespec-dev-tooling (it is in the
  `just check` aggregate but absent from `ci.yml`); needs an
  `approval:workflow-edit` change.
- Guard limits noted at ratification: a variable-target `sftp`, `scp` or
  `rsync` source on a hinted command is a stated limit; `mkfs.*` variants;
  the failure-path deny reason always uses the generic route.
