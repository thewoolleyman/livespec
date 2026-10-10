## The maintainer's statement of what done means

The two k3s nodes converge to committed state through just ansible-apply ansible/ci-pool.yml with drift clean, the legacy installers they replaced are gone, and the fleet-host mutation guard ships in the Driver and is proven by one live denial.

## Definition of Done assertions derived from that statement

- Running `just ansible-drift ansible/ci-pool.yml` from the control node vps reports no change for poweredge-xubuntu or gmktec-xubuntu after `just ansible-apply ansible/ci-pool.yml` has converged them from committed source.
- A live read of gmktec-xubuntu after that apply matches its committed phase0 profile and the R5 per-node model: the churn-slot extended resource advertises 12, the node carries no CI taint, the pool quotas total 44, and the agent timer is armed.
- No path named by a `# Replaces <path>` declaration in `ansible/roles/*/tasks/*.yml` exists in the livespec-dev-tooling tree, `ci-runner/k3s/phase2/install-node.sh` included, and each commit that deleted one cites the pre-deletion SHA in its body.
- The `fleet_host_guard` PreToolUse hook ships in a released livespec-driver-claude build, is registered in that build's `hooks.json`, and loads in a governed project session.
- A positively-identified mutating `ssh` command to a fleet-managed host, issued from a governed Claude Code session running the released Driver, is denied by the shipped guard with a reason naming the GitOps deployment discipline.

# 001 — Definition of Done authored on resume, and the plan rescoped to it (2026-10-10)

Written 2026-10-10 by the fable session that resumed this plan after the
2026-09-12 wind-down. The epic predates the plan Definition of Done
requirement; the resume directive reported `plan-definition-of-done: missing`,
and the statement above is the maintainer's answer, chosen from three offered
scopes. It is narrower than research note 000's section 5 acceptance list.

## What the statement keeps and what it defers

The statement names three outcomes: the k3s nodes converge through the
committed playbook with drift clean, the installers that playbook replaced
are gone, and the fleet-host mutation guard ships and is proven by one live
denial. Children that deliver those outcomes stay in this plan:

- C1 `livespec-vbqmdd` — the contracts.md clause for the guard. Its proposal
  also carries the required GitOps-deployment agent-instruction TOPIC clause,
  which binds the deferred instruction work (C2, C4, C7); the C1 executor
  splits the proposal into two topic files and only the guard clause is
  ratified in this plan. The topic clause stays pending for the follow-up.
- C3 `livespec-ggs36t` — the guard itself, draft PR livespec-driver-claude#750,
  NO-BLOCKERS after four adversarial rounds; merges after C1 ratifies.
- C5 `livespec-lfie5z` — C5a merged 2026-09-12 (PR #2274); C5b's three
  commits survive on branch `ci-pool-retire-shell` and retire the installers.
- C12 `livespec-obsinx` (filed this session, `ready`; C5 is blocked on it) — the rebuild-recipe amendment that C4's proposal
  carried as its second finding: the node-provisioning stage becomes
  `just ansible-apply ansible/ci-pool.yml`, with the spec-tier test rewrite
  and README step 4. Retiring `install-node.sh` without it would leave the
  ratified recipe naming a file that no longer exists, so it is load-bearing
  for assertion 3 and cannot be deferred with the rest of C4.

Deferred to a follow-up plan, to be opened before this plan archives and to
receive these children by re-parenting: C2 `livespec-eyjepk` (canonical
instructions topic), C4 `livespec-hsdguf` minus its second finding (layer-map
topic, the two Ansible tree checks, the new `## Host provisioning tree`
section, the conformance row), C6 `livespec-7x7ia7` (drift signal), C7
`livespec-tf27wm` (host repos), C8 `livespec-zyh7uo` (adopter registration),
C9 `livespec-7pp3bc` (plan prose). Research note 000 ordered instruction and
enforcement FIRST; the maintainer's statement reverses that order for this
plan, and the reversal is a ruling recorded in the scope event.

## Executor state found on resume, and what was lost

All seven executor worktrees recorded in the 2026-09-12 wind-down still
existed when this session began. Between 07:22 and 07:35 local on 2026-10-10,
while this session was reading them, five were removed by another process on
the host (consistent with a `just reap-stale-worktrees` run at another
session's start). Branches survived in every case; uncommitted work did not:

- C2 `gitops-discipline-instructions`: five STAGED files lost (the canonical
  topic, the AGENTS.md line, three `.ai/` additions). Must be re-authored.
- C6 `nai-ansible-drift-signal`: the Signal 11 SKILL.md edit lost.
- C9 `plan-resume-reads-research`: the prose edit and its spec proposal lost.
- C5b `ci-pool-retire-shell`: worktree gone, all three commits intact on the
  branch (73b42a71, 3d35fa82, cd159c4a).
- C3 `fleet-host-guard`: worktree gone, branch pushed, PR #750 intact.
- C4 `gitops-discipline-devtooling`: survived; its real
  `ansible_inventory_hosts_covered.py` was ALREADY lost with `/tmp/c4-handoff/`
  (the Red stub is what is on disk). Rescued this session into the session
  scratchpad as a bundle plus a tarball of the dirty tree.
- C1 `spec-gitops-deployment-discipline`: survived, clean, five unpushed
  commits; rescued as a bundle. First executor step is to push it.

The repository stashes were checked and hold unrelated 2026-07/08 work.

## Carrier map (recorded on the epic; restated here for the reader only)

1 and 2 → C5 `livespec-lfie5z`. 3 → C5 `livespec-lfie5z` and C12 `livespec-obsinx`. 4 → C1
`livespec-vbqmdd` and C3 `livespec-ggs36t`. 5 → plan-level proof: the live
denial is a host-captured step of the plan's own Proof of Done, exercised
against the released Driver build, and no child discharges it.
