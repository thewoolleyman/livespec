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

The named first action is read-only. Before any later mutation, load the exact topic guidance required by those two instruction files; in particular, do not touch credentials, CI gates, work-items, specifications, timed evidence, worktrees, or host deployment from remembered conventions. `.ai/ci-gate-discipline.md` is load-bearing for every remaining slice and is quoted in the ownership section below.

Do not use archived plan placement as delivery evidence. Homelab epic `hl-6uldtn` is reopened and delivery-active; its active thread is `plan/05-hetzner-fleet-member/`. Thread07 already owns the host build/CI substrate. Never create a competing homelab plan or contact the host from this thread.

## State — the epic is groomed; do not groom it again

The epic was decomposed on 2026-08-04 into the seven slices below. `livespec-h22nve` is held at **`active`**, not `backlog`, deliberately: `groom` refuses any target not at exactly `backlog`, so `active` is what prevents a later session from re-decomposing the epic and duplicating slices that already exist. **Do not return it to `backlog`.**

The groom operation closed the epic as “regroomed out” as its normal final step. For a plan-thread anchor that is a false clear — it would archive this thread while none of the completion evidence exists — so the closure was reversed in the same session. This is the same failure the `homelab` repository had to reverse twice (`hl-bfwpqb` false-clearing thread 05, then `hl-6uldtn` false-clearing thread 07). The structural cause is recorded there: a regroomed-out epic false-clears its downstream edges because the ledger refuses task-blocks-epic edges and replacement slices cannot inherit the block, so the mitigation has to be prose. Expect to re-apply this correction if anything closes the anchor before the completion evidence exists.

## Named first action

Run a fresh read-only critical-path census before resuming anything. Every recorded number below is point-in-time and several have already moved:

```bash
git -C /data/projects/livespec fetch --prune origin
git -C /data/projects/homelab fetch --prune origin
/usr/local/bin/with-livespec-env.sh -- bd show livespec-h22nve --json
cd /data/projects/homelab && /usr/local/bin/with-homelab-env.sh -- bd show hl-6uldtn hl-xuu5j3 hl-wkyeqg hl-euzuhb --json
gh api repos/thewoolleyman/livespec/actions/runners
gh api repos/thewoolleyman/livespec/actions/variables
gh api repos/thewoolleyman/livespec/actions/permissions/fork-pr-contributor-approval
gh pr list --repo thewoolleyman/livespec --state open --limit 100 --json number,title,headRefOid,statusCheckRollup
```

`bd` resolves its tenant from the working directory, so a `homelab` query issued from the `livespec` checkout fails with `Access denied for user 'livespec'` — run it from `/data/projects/homelab`.

Verify each command saw its intended input and retain raw output beside any derived count. Then re-measure the slices from the ledger and resume the first genuinely unblocked one; the table below records the cut, not live status.

## The decomposition

Re-measure every id. “Blocked by” is the ledger edge; a cross-tenant blocker is carried as a `sibling_work_item` entry in `metadata.non_local_depends_on`, not as a beads edge.

| Id | Repo | Tier | Blocked by | Slice |
|---|---|---|---|---|
| `livespec-teasvm` | `livespec` | maintainer-side | — | Fail-closed gating routing + retire archived-pool workflow residue — **CLOSED 2026-08-04**, PR [#1970](https://github.com/thewoolleyman/livespec/pull/1970), merged `29b7e5ca` |
| `livespec-dev-tooling-3otdg4` | `livespec-dev-tooling` | **factory** | `livespec-teasvm` | Close the routing guard's label blind spot + hosted fail-closed assertion |
| `livespec-uyfggr` | `livespec` | maintainer-side | `livespec-teasvm` | Bring forge state to the v192 baseline + fork-exclusion drift detector |
| `livespec-hhx4gl` | `livespec` | maintainer-side | — | Retire the Phase-0 `ci-runner` installation from the shared factory host |
| `livespec-3on57g` | `livespec` | maintainer-side | `livespec-uyfggr`, `livespec-dev-tooling-3otdg4` | Adopt the dedicated Hetzner label + liveness/freshness observation |
| `livespec-7wvyo7` | `livespec` | maintainer-side | `livespec-3on57g` | Live one-job exercise on server 3039451 |
| `livespec-q7sfu6` | `livespec` | maintainer-side | `livespec-7wvyo7` | Prove the hosted fallback, then restore the intended posture |

`livespec-dev-tooling-3otdg4` lives in the **`livespec-dev-tooling`** tenant, not this one. The groom minted it as `livespec-qheazr` with this repo's prefix; `bd create` refused that foreign prefix at the target tenant, so it was refiled under a native id and `livespec-3on57g`'s reference was rewritten to match. That orchestrator defect is `bd-ib-a8zi` in `livespec-orchestrator-beads-fabro`, with this recurrence recorded on it. If a future groom emits a cross-repo slice, expect the same failure and apply the same fix — **never** `bd create --force`, which would plant a foreign-prefix id in a sibling tenant permanently.

## Ownership boundary

- **Livespec repository changes.** Only `livespec-dev-tooling-3otdg4` is factory-dispatchable (`drive` as `impl:<id>`): its acceptance is local and credential-free and it touches no workflow file. **Every other slice is maintainer-side**, because the factory dispatch credential deliberately withholds the `workflows` grant, so a dispatched agent cannot push a branch touching `.github/workflows/` (`.ai/ci-gate-discipline.md`). Drive those in-session through the worktree → PR → merge → cleanup protocol.
- **GitHub repository settings and runner-registration credentials.** Factory-ineligible; they require live privileged forge access. Execute in-session through the authorized operator identity; never expose a token in arguments, files, logs, fixtures, or the job environment.
- **Hetzner/NixOS service realization.** Owned exclusively by homelab Thread07, downstream of Thread05's real-machine admission. Supply v192 properties to that owner and consume its measured outputs. Do not file a duplicate Livespec implementation item for host modules or services.
- **Live required-job and fallback exercises.** Factory-ineligible external-state verification. Minimize paid Actions runs; one pushed candidate should carry all locally proven work, and unchanged code must never be rerun merely to see.

Do not hard-code labels, service names, or a fallback mechanism before measuring the host owner's accepted interface. Do not revive the archived shared-factory resident listener pool. A persistent registration is nonconforming even if it runs only one job at a time.

## The external gate on homelab

`livespec-3on57g`, `livespec-7wvyo7` and `livespec-q7sfu6` cannot begin until homelab has delivered **both** `hl-wkyeqg` (provision server 3039451) and `hl-euzuhb` (ratify `hetzner-prod` fleet admission), **and** Thread07 (`hl-xuu5j3`) has published its accepted runner realization. beads refuses cross-tenant edges for these, so the precondition is prose-only and cannot be trusted to block anything mechanically.

Measured 2026-08-04, and possibly stale by the time you read it: `hl-wkyeqg` and `hl-euzuhb` were both `pending-approval`, their Phase-C predecessors `hl-acv732` and `hl-ovxxtq` were still `active`, and `hl-xuu5j3` was `backlog` and blocked. **Server 3039451 was not provisioned and `hetzner-prod` was not admitted.** Thread07's own handoff forbids it beginning `revise`, `groom`, or implementation until both outcomes exist.

## What was measured on 2026-08-04

Point-in-time; re-measure rather than inheriting any of it. The full raw census is journaled on `livespec-h22nve`.

- **Runners.** `actions/runners` returned `total_count=6`, down from 13 the previous day — all offline, all labelled `self-hosted,local-ci`, all Phase-0 residue. The set is **not static**, so `livespec-uyfggr` must re-enumerate rather than act on a recorded id list.
- **Routing.** `CI_RUNNER_LABELS` is `["ubuntu-latest"]`, unchanged since 2026-07-18, so gating matrices really do run hosted.
- **Fork approval.** `all_external_contributors` — v192's strict tier, satisfied. Nothing yet detects it weakening; that detector is `livespec-uyfggr`.
- **Triggers and protection.** `ci.yml` triggers on `pull_request` plus `push: branches: [master]`, exactly v192's permitted set. `master` protection requires the single context `ci-green`, with `enforce_admins: true`.
- **Shared factory host.** No CI listener or worker process and no active runner timer, but the whole Phase-0 installation is still present under `/usr/local/lib/ci-runner/` with its units `disabled` at a vendor preset of `enabled` — one `systemctl preset` from re-arming. That is `livespec-hhx4gl`. Its `gate-runner` counterpart is deliberately out of scope pending a reading of whether v192's factory-host clause reaches the privileged `livespec-orchestrator` tier; refer that to `livespec-orchestrator-beads-fabro`'s own specification rather than deciding it here.
- **Phase-0 remote branches.** `origin/ci-shadow/phase2-matrix` and `origin/ci-shadow/pilot-1` still exist. They were created by an earlier session; `livespec-uyfggr` requires explicit maintainer confirmation before deleting either.

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
