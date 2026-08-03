# Livespec CI on Hetzner — handoff

## Purpose and authority

Drive ledger epic `livespec-h22nve` until a required Livespec merge-gating job is proven to execute on the dedicated Hetzner host under the v192 contract, and the GitHub-hosted fallback is also proven. The ledger is the only status authority. This file carries coordination and decision boundaries, not a parallel work queue.

The maintainer explicitly authorized autonomous planning and execution to get Hetzner serving CI quickly because GitHub-hosted Actions are now paid. Do not stop for choices that can be resolved from repository, ledger, forge, or owner-session evidence. Ask only for a genuinely unavailable human credential or an irreversible choice outside the accepted contract.

## Read first

Read these in order before acting:

1. `plan/livespec-ci-on-hetzner/approach.md`
2. `SPECIFICATION/non-functional-requirements.md` §“Self-hosted CI runner host requirements” and its two conforming-host/fallback scenarios
3. `/data/projects/homelab/plan/05-hetzner-fleet-member/handoff.md`
4. `/data/projects/homelab/plan/07-build-substrate/handoff.md`
5. `/data/projects/livespec/AGENTS.md`
6. `/data/projects/homelab/AGENTS.md`

The named first action is read-only. Before any later mutation, load the exact topic guidance required by those two instruction files; in particular, do not touch credentials, CI gates, work-items, specifications, timed evidence, worktrees, or host deployment from remembered conventions.

Do not use archived plan placement as delivery evidence. Homelab epic `hl-6uldtn` is reopened and delivery-active; its active thread is `plan/05-hetzner-fleet-member/`. Thread07 already owns the host build/CI substrate. Never create a competing homelab plan or contact the host from this thread.

## Named first action

Run a fresh read-only critical-path census before grooming or changing anything:

```bash
git -C /data/projects/livespec fetch --prune origin
git -C /data/projects/homelab fetch --prune origin
/usr/local/bin/with-livespec-env.sh -- bd show livespec-h22nve --json
/usr/local/bin/with-homelab-env.sh -- bd show hl-6uldtn --json
/usr/local/bin/with-homelab-env.sh -- bd show hl-xuu5j3 --json
gh api repos/thewoolleyman/livespec/actions/runners
gh pr list --repo thewoolleyman/livespec --state open --limit 100 --json number,title,headRefOid,statusCheckRollup
```

Verify each command saw its intended input and retain raw output beside any derived count. Then invoke `livespec-orchestrator-beads-fabro:groom` on `livespec-h22nve` if it remains `backlog`, using the ownership and acceptance boundaries below. If another owner has already groomed or advanced it, resume the ledger's actual children instead of duplicating them.

## Grooming boundary

The epic's coherent implementation cuts are determined from live state, but the decomposition must preserve these ownership seams:

- Livespec repository changes: tested workflow routing to an explicit dedicated-runner label, strict event classification, an operator-usable hosted fallback, liveness/freshness observation, and evidence collection. These are factory-dispatchable only when their acceptance is local and credential-free; route them through `livespec-orchestrator-beads-fabro:drive` as `impl:<id>` rather than implementing them inside the planning session.
- GitHub repository settings and runner-registration credentials: factory-ineligible because they require live privileged forge access. Record that routing on their ledger item and execute in-session through the authorized operator identity; never expose a token in arguments, files, logs, fixtures, or the job environment.
- Hetzner/NixOS service realization: owned exclusively by homelab Thread07, downstream of Thread05's real-machine admission. Supply v192 properties to that owner and consume its measured outputs. Do not file a duplicate Livespec implementation item for host modules or services.
- Live required-job and fallback exercises: factory-ineligible external-state verification. Minimize paid Actions runs; one pushed candidate should carry all locally proven work, and unchanged code must never be rerun merely to see.

Do not hard-code labels, service names, or a fallback mechanism before measuring the host owner's accepted interface. Do not revive the archived shared-factory resident listener pool. A persistent registration is nonconforming even if it runs only one job at a time.

## Completion evidence

The epic may close only when forge and host artifacts jointly establish all of the following:

- a required same-repository Livespec merge-gating job names and actually runs on server 3039451's dedicated runner capacity;
- its registration accepted no more than that one job, deregistered afterwards, and no prior workspace is observable;
- supervisor and job identities are distinct as required, the job has no minting credential or stronger fleet secret, and it lacks admin/root-equivalent daemon access;
- strict outside-collaborator fork approval and allowed trigger classes are measured from the forge, not inferred from workflow prose;
- runner liveness and binary freshness are observable before a job is routed;
- withdrawing or disabling the self-hosted route causes the same required gate to complete on GitHub-hosted capacity rather than queue indefinitely;
- the shared factory host carries no CI listener or worker process;
- every commissioned tracked change is merged, both primary checkouts are fast-forwarded and clean, worktrees are removed, and remote branches are absent.

Closing `livespec-h22nve` archives this thread. Until those observations exist, an archived branch, a green local test, a registered idle runner, or a merged host module is decomposition progress—not delivery.

## Next-session command

Read exactly this one path and execute its named first action:

`plan/livespec-ci-on-hetzner/handoff.md`
