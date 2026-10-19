# GitOps deployment discipline — the fleet-canonical statement

Read this BEFORE any deployment, Ansible, GitOps, host-provisioning, `kubectl`,
or ssh-to-a-fleet-host action, in any fleet repository.

This is the fleet-canonical statement of the six rules every repository with a
host-provisioning or deploy surface lives under. A member's or adopter's own
`.ai/gitops-deployment*.md` topic MAY cite this file for the rules and carry
only its own layer map: which committed role or playbook deploys which file,
and from which control node. `livespec` itself provisions nothing, so its
layer map is the pointer in §"Where the fleet's provisioning model lives".

Every rule below was written in response to a failure that actually happened.
The failures and the reasoning are recorded in `livespec`
`plan/archive/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md`
§1–§3; each rule names the failure it answers by that section's number.

## The six rules

### 1. Read the provisioning model before touching a host

Before any host or infrastructure action, read the provisioning model: the
control node, the committed apply command, and the committed drift command.
For the legacy Ubuntu fleet that model is `livespec-dev-tooling`
`ansible/README.md`. Read it first, not after a theory has formed.

ssh to a fleet host is for READ-ONLY verification only: reading a unit's
status, a file's content, or a process list. It is never how a change is made.

*Answers failure 1.* A session ssh'd into two k3s nodes and reasoned "there is
no checkout on the hosts, so the deploy is manual". The README in the
repository it had been editing states the control node is `vps` and
playbooks run FROM committed source. Having no checkout on a target is the
design, not a gap.

### 2. No live host is changed by hand

"This has to be done by hand on the host" names a gap in the committed
automation. Fix that gap. It is never a task to hand the maintainer, and never
licence for an improvised privileged command. A deploy is a change to git
followed by the committed apply.

The Driver's fleet-host mutation guard enforces the mechanical half of this
rule (`SPECIFICATION/contracts.md` §"Driver-shipped hooks"). It denies, among
others, a positively identified mutating `ssh`, `scp`, `rsync` or `sftp` to a
fleet host, a `kubectl` or `helm` verb outside the read-only set, an ad-hoc
privileged `ansible` run, and an apply of an uncommitted playbook. The
sanctioned set the guard never denies is `just ansible-apply`,
`just ansible-drift`, and `ansible-playbook` on a committed playbook. That section
is the authoritative list. When the guard denies you, the denial is correct:
find or write the committed path. Do not look for a command shape the guard
fails to recognise. Getting a mutation past the guard is the failure this rule
exists to prevent, however the command is spelled.

*Answers failure 4.* A session asked the maintainer to change hosts by hand,
under a plan whose founding directive was that no live host is changed by
hand.

### 3. A mechanism change lands in the layer the automation APPLIES

Before editing a runtime artifact — a unit file, a script, a config, a
manifest — ask: **which role or playbook deploys this file?** Make the change
there, or in the source that role renders from. A change made only to a copy
that nothing applies has changed nothing on any host, however correct it is.

*Answers failure 2.* A session treated the legacy shell installers as live
and the Ansible roles as staged. The reverse was true. It updated only the
dead installer, and by renaming the unit's placeholders it turned the real
installer's substitution into a silent no-op.

### 4. A replaced layer is retired, never maintained beside its replacement

When a role or playbook replaces an older installer, delete the older one, and
cite its pre-deletion commit so it stays recoverable from history. Two layers
that both look like the installer for the same file will be edited in
the wrong order. A role task that says `# Replaces <path>` is a claim that
`<path>` is gone. `livespec-dev-tooling` owns the mechanical check of that
claim (`ansible_replaced_installers_retired`, child C4 of the research note's
§4).

*Answers failures 2 and 3.* The dead installer could only be edited by mistake
because it still existed. And because the stale role looked like future
work, it was filed as "fix at some future cutover", even though that role was
the apply path and blocked the converge.

### 5. Run and read the drift report before every apply

Run the committed drift command (for the legacy fleet, `just ansible-drift
<playbook>`, which changes nothing) and read its diff before every apply. A
green repository is never proof that a host matches it. A host that no
playbook covers is invisible to both apply and drift, so an empty report about
that host means nothing.

*Answers the drift root cause.* The k3s pool's two nodes sat on 2026-09-08 code
while master moved on, because no playbook targeted their inventory group. No
drift report could show it, because no playbook, and so no drift run, reached
those nodes.

### 6. A review-gated change is a DRAFT pull request until NO-BLOCKERS

Open any change that needs an independent review before merge as a DRAFT pull
request, and mark it ready only after the review returns NO-BLOCKERS. Many
fleet repositories enable auto-merge, and such a repository merges on green
without waiting for anyone. In those repositories an open, non-draft pull
request is a merge already scheduled, not a pause point.

*Answers failure 6.* A session treated "PR open" as a pause in a repository
whose auto-merge job merges on green, and a pull request carrying a known
blocker reached master.

## The behaviour underneath all six

The pattern these rules break: acting before reading the model of the system
being acted on; fitting later evidence to a conclusion once it has formed,
rather than re-deriving; and, under infrastructure uncertainty, falling back
to handing the problem to a human. When you notice any of the three, stop and
reread rule 1.

A related rule belongs to the plan operation rather than here: a strict plan
resume reads the research notes in its read-first chain before acting
(failure 5). Its home is `livespec-orchestrator-beads-fabro`
`.claude-plugin/prose/plan.md`; landing it there is child C9 of the research
note's §4.

## Where the fleet's provisioning model lives

`livespec` has no deploy surface of its own. Each statement below points at
the repository that owns the fact, so it stays true when that repository
changes:

- **The legacy Ubuntu fleet** (`vps`, `poweredge-xubuntu`, `gmktec-xubuntu`,
  `hp-xubuntu`) is provisioned by `livespec-dev-tooling` `ansible/`. Its
  README names the control node, the two commands, and the playbook table.
  The inventory, `ansible/inventory/legacy.yml`, is the host set the mutation
  guard reads when the governed project carries no inventory of its own. Its
  header states that a play targets inventory GROUPS, never a hostname.
- **Kubernetes desired state** — the CI pool's queues, scale sets, gate Jobs
  and RBAC — stays as manifests under `livespec-dev-tooling` `ci-runner/` and
  is applied by a playbook. It is never edited in the cluster with
  `kubectl edit` or `kubectl patch`.
- **Per-host repositories** (`vps-info`, `poweredge-xubuntu-info`,
  `gmktec-xubuntu-info`, `hp-xubuntu-info`, `fabro-hosts`, `otel-collector`,
  `local-llm`, `homelab`) each owe their own `.ai/gitops-deployment*.md` with
  that repository's layer map, under the `gitops-deployment-topic` change to
  livespec `SPECIFICATION/contracts.md` §"Fleet agent-instruction core"
  (child C7 of the research note's §4; C4 supplies the conformance row, and C8
  registers the repositories as adopters so the obligation binds). Where it
  exists, read it before acting in that repository.
