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

## Resume state — 2026-08-04, after the fleet fail-open sweep

**`livespec-dev-tooling-3otdg4` is IMPLEMENTED and its PR is open but deliberately unmerged.** livespec-dev-tooling [#1274](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1274) carries commit `1108bd1`, `just check` green at 66/66, with both `TDD-Red-*` and `TDD-Green-*` trailer blocks. Auto-merge is NOT armed. What remains is a maintainer decision, recorded under "The open decision" below.

**Attempt 4 failed like none of the first three**, then the work moved in-session. The dispatch died twice at `ACP turn failed: ACP protocol error` inside the Implement stage, before touching the task at all — an agent-runtime failure, not a spec failure, and a fifth dispatch through the same runtime had no reason to survive it. The handoff's pre-authorized fallback was taken: implemented in-session under Red-Green-Replay. The parked run was force-removed and the item reassigned off `fabro`.

**A measurement changed the shape of the work.** The item's groomed scope claimed the fail-open assertion would be "a genuine no-op in every fleet repo", so the fan-out could not redden siblings. Measured across all 13 repos in `.livespec-fleet-manifest.jsonc`, that was FALSE: six carried the fail-open fallback and five of those also run the check, so landing it first would have reddened five repositories — enforcement-before-adoption, the named cause of revert-worthy breakage in `.ai/ci-gate-discipline.md`. The maintainer chose to repair first.

**That sweep is done.** Epic `livespec-zmys` with six per-repo children, all merged: `livespec-runtime` [#472](https://github.com/thewoolleyman/livespec-runtime/pull/472), `livespec-driver-claude` [#417](https://github.com/thewoolleyman/livespec-driver-claude/pull/417), `livespec-driver-codex` [#397](https://github.com/thewoolleyman/livespec-driver-codex/pull/397), `livespec-orchestrator-git-jsonl` [#550](https://github.com/thewoolleyman/livespec-orchestrator-git-jsonl/pull/550), `livespec-overseer` [#698](https://github.com/thewoolleyman/livespec-overseer/pull/698), `livespec-console-beads-fabro` [#640](https://github.com/thewoolleyman/livespec-console-beads-fabro/pull/640). A fleet-wide re-measure returns ZERO remaining self-hosted `runs-on` fallbacks, and the same query returns 3 on the pre-repair trees so the zero is fail-capable. `livespec-orchestrator-beads-fabro` was excluded with reason, verified at byte level: its only three occurrences are `#`-comments and comments are stripped before parsing.

### The open decision — do not merge #1274 without settling it

The sweep incidentally surfaced a **pre-existing fleet-red state**, filed as `livespec-dev-tooling-irtt` (P0, ready). Three repos' master CI is red — `livespec-runtime`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-beads-fabro` — all failing `check-public-api-result-typed`.

Root cause, established rather than inferred: `check-public-api-result-typed` used to sit behind the `pure_trees` role-absence gate. The `pure-trees-scan-universe-decoupled` work removed that gate DELIBERATELY, shipping with its own design document, and un-shadowing those detectors was a stated benefit rather than a side effect. All three red repos declare `pure_trees = { not_applicable = … }`, so the check had never actually run there; un-gating it scanned their whole public API for the first time and found dozens of long-standing violations. The fan-out then bumped `livespec-runtime` from `v1.17.1` straight to `v1.18.9` in one step — so the break lies somewhere in that range, not necessarily in `v1.18.9` itself. Causation is nailed at the consumer end: that repo's last green master run has `check-public-api-result-typed` RUNNING AND PASSING, and the very next commit is the pin bump and the first red.

The remedy is a genuine maintainer call and was deliberately NOT self-resolved, because `.ai/ci-gate-discipline.md`'s literal remedy (revert-and-reland) would revert a deliberate architectural improvement. Either the un-gating is reverted and re-landed behind adoption, or the three consumers adopt it. Whichever is chosen, no lever, env var, carve-out, or severity demotion — `li-4x3a45` is the recorded wontfix on exactly that.

A second defect was split out as `livespec-dev-tooling-zi29` (P1, ready), because the revert does not close it and closing the satisfying half would ship it silently: a zero-`.py` PR skips the Python matrix via `detect-py-changes`, so its `ci-green` reports green while the master push runs the full aggregate and goes red. PRs keep merging onto a red master and nobody is told. That mechanism is why this fleet-red went unnoticed for hours. Its acceptance requires the positive control FIRST — a real zero-`.py` PR green at `ci-green` paired with the master-push aggregate failing at the same tree.

### If a future session must dispatch this item anyway

Its dispatch command, after the preflight below:

```bash
PR=$(python3 -c 'import json,pathlib;d=json.loads((pathlib.Path.home()/".claude/plugins/installed_plugins.json").read_text());print(next(e["installPath"] for e in d["plugins"]["livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro"] if e.get("projectPath")=="/data/projects/livespec-dev-tooling"))')
cd /data/projects/livespec-dev-tooling && /usr/local/bin/with-livespec-env.sh -- \
  python3 "${PR}/scripts/bin/drive.py" --repo /data/projects/livespec-dev-tooling \
  --action impl:livespec-dev-tooling-3otdg4 --json
```

The earlier form of this command resolved the plugin root with
`ls -d …/*/ | tail -1`, which sorts lexically rather than by build date and
selected a stale Jul-15 build out of 125 cache directories. The replacement
reads the install record. See `.ai/dispatcher-drain-operations.md`
§"Resolve the plugin root from the install record, never with `ls … | tail -1`".

**Preflight, all four, before dispatching** — each of these actually bit a previous attempt:

1. **Plugin currency.** The dispatcher refuses (exit 3) when its plugin build predates the latest release. Fix at source with `just ensure-plugins` from `/data/projects/livespec` (`claude plugin update` alone fails — the plugins are installed at *project* scope, not user). **Never** bypass a version gate.
2. **Tenant-wide ledger check.** A malformed `depends_on` on ANY item in the target tenant blocks every dispatch there. Two such records were repaired; expect the class, not those two.
3. **Description size.** Keep the dispatched description under ~1500 chars. It is currently 1492. Park depth in notes — but see hazard 4, because notes ship to the agent too.
4. **No doubled curly braces in `description` OR `notes`.** Fabro expands the workflow `goal`, which embeds both, so a GitHub-Actions expression containing `||` aborts the dispatch in seconds with `fabro_run_id: null`. Verify with a grep whose pattern is first shown matching a known-present instance.

Also check `git status --short` in `/data/projects/livespec-dev-tooling`. At wrap-up it carried a tracked modification owned by ANOTHER session (`plan/pure-trees-role-key-scope/supervisor-handoff.md`). A dirty source checkout can make the engine fall back to a synthetic snapshot base and fail at publish with a misleading workflows-permission error. **Do not revert another session's work** — dispatch anyway and, if publish fails that way, attribute it rather than re-debugging from scratch.

### What the three failed attempts established

- **Attempt 1** ran ~1h, implemented the change, and its own adversarial review CONFIRMED a crash in its candidate: an unquoted repo-variable fallback reached a `cast()` standing in for a runtime check, and `.group()` on `None` raised `AttributeError` — a security check crashing. Nothing was published. That code no longer exists (the run was force-removed), so the finding survives only in the item's notes.
- The spec was then reframed from enumerating input cases to stating a **totality property** — the guard returns a verdict for ANY `runs-on` and never raises — because enumerating cases would never have proved the hole closed.
- **Attempt 2** died in seconds at template expansion (hazard 4 above), caused by a note the previous session itself had written.
- **Attempt 3** reached the implement stage and was stopped intact at session wrap-up, ~28 minutes in and still in stage 1 of many. Its run was force-removed and the ledger item reset to `ready`/unassigned, so state is clean — nothing to unwind.

If attempt 4 also fails at review, consider implementing it in-session instead: it is product Python in a sibling repo, so it needs Red-Green-Replay and a worktree → PR, but it escapes the unattended-turn cap entirely.

## The decomposition

Re-measure every id. “Blocked by” is the ledger edge; a cross-tenant blocker is carried as a `sibling_work_item` entry in `metadata.non_local_depends_on`, not as a beads edge.

| Id | Repo | Tier | Blocked by | Slice |
|---|---|---|---|---|
| `livespec-teasvm` | `livespec` | maintainer-side | — | Fail-closed gating routing + retire archived-pool workflow residue — **CLOSED 2026-08-04**, PR [#1970](https://github.com/thewoolleyman/livespec/pull/1970), merged `29b7e5ca` |
| `livespec-dev-tooling-3otdg4` | `livespec-dev-tooling` | factory → **in-session** | `livespec-teasvm`, then epic `livespec-zmys` | Close the routing guard's label blind spot + hosted fail-closed assertion — **IMPLEMENTED**, PR [#1274](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1274) open and unmerged; 4 dispatches failed, see Resume state |
| `livespec-uyfggr` | `livespec` | maintainer-side | `livespec-teasvm` | Bring forge state to the v192 baseline + fork-exclusion drift detector — **CLOSED 2026-08-04**, PR [#1985](https://github.com/thewoolleyman/livespec/pull/1985) |
| `livespec-hhx4gl` | `livespec` | maintainer-side | — | Retire the Phase-0 `ci-runner` installation from the shared factory host — **CLOSED 2026-08-04** |
| `livespec-3on57g` | `livespec` | maintainer-side | `livespec-uyfggr`, `livespec-dev-tooling-3otdg4` | Adopt the dedicated Hetzner label + liveness/freshness observation |
| `livespec-7wvyo7` | `livespec` | maintainer-side | `livespec-3on57g` | Live one-job exercise on server 3039451 |
| `livespec-q7sfu6` | `livespec` | maintainer-side | `livespec-7wvyo7` | Prove the hosted fallback, then restore the intended posture |

`livespec-dev-tooling-3otdg4` lives in the **`livespec-dev-tooling`** tenant, not this one. The groom minted it as `livespec-qheazr` with this repo's prefix; `bd create` refused that foreign prefix at the target tenant, so it was refiled under a native id and `livespec-3on57g`'s reference was rewritten to match. That orchestrator defect is `bd-ib-a8zi` in `livespec-orchestrator-beads-fabro`, with this recurrence recorded on it. If a future groom emits a cross-repo slice, expect the same failure and apply the same fix — **never** `bd create --force`, which would plant a foreign-prefix id in a sibling tenant permanently.

**Three of the four non-Hetzner slices are closed.** Only the factory slice remains, and it has survived three dispatch attempts without publishing. Read its ledger notes before touching it — they carry the confirmed defect from attempt 1 and the dispatch hazards from attempt 2, both cheaper to read than to rediscover. The two general dispatch hazards found here are written up in `.ai/dispatcher-drain-operations.md`.

There is also an **unmerged PR carrying an earlier version of this very file**: livespec [#2003](https://github.com/thewoolleyman/livespec/pull/2003), which refreshed the handoff and added those two hazards. The wrap-up edits were folded onto the SAME branch rather than a separate one, precisely so two branches could not conflict on this file. If #2003 is still open when you resume, let it land before editing the handoff again; if it was closed unmerged, re-apply its `.ai/dispatcher-drain-operations.md` half, which is the durable part.

## Also opened by this thread

`livespec-opwqmy` (bug, `ready`, `admission:manual`) — `systemctl preset-all --dry-run` silently applies presets host-wide. It was named as the negative control in `livespec-hhx4gl`'s own acceptance and fired on the shared factory host on 2026-08-04, enabling 49 units. `--dry-run` is documented as supported by only eleven verbs and `preset-all` is not among them, while `systemctl --help` advertises the flag with no caveat. 46 of the 49 symlinks were reverted; `ssh.service` and the `sshd.service` alias were deliberately left enabled because a lockout on a remote host is not recoverable. The item is `admission:manual` so no drain can pick up host work. Evidence: `tmp/overseer/livespec-ci-on-hetzner/preset-all-incident-20260804.txt` and `preset-revert-set.txt`.

The durable lesson generalizes past this thread: **a control is not a control until it has been made to fail on demand.** `livespec-hhx4gl`'s original acceptance trusted a command because its name and its `--help` line implied a behavior nobody had tested, and the same session's dispatch spec enumerated input cases instead of constraining behavior, missing a crash that every stated control would have passed.

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
- **Shared factory host.** No CI listener or worker process and no active runner timer, but the whole Phase-0 installation is still present: scripts under `/usr/local/lib/ci-runner/`, unit files under `/etc/systemd/system/`, empty `system-runner.slice` and `system-gate-runner.slice`, and two failed transient `systemd-run` units from `ci-runner-heartbeat.sh`. The units are `disabled` at a vendor preset of `enabled`.

  **That preset does NOT make the host one `systemctl preset` from re-arming** — an earlier reading of this thread said so and was wrong. A second, independent gate is already in place: on 2026-08-03 a `hosted-only.conf` drop-in was added to all six runner units (`ci-runner-supervisor.service`, `runner@.service`, `gate-runner-supervisor.service`, `gate-runner@.service`, `ci-runner-heartbeat.timer`, `ci-runner-cache-prune.timer`) carrying `ConditionPathExists=/run/livespec-local-ci-enabled`. That runfile is absent, and because it lives in `/run` it cannot survive a reboot. So even a preset re-enable leaves every unit refusing to start until an operator explicitly creates it.

  `livespec-hhx4gl` therefore removes a **dormant, double-gated** installation. It is real v192 hygiene — "carry" is stronger than "run", and the drop-in's own comment says to remove it "when a later spec revision restores self-hosted CI", which v192 is — but it is NOT an urgent containment hole, and it must not be prioritized ahead of the slices that are. Its `gate-runner` counterpart stays out of scope pending a reading of whether v192's factory-host clause reaches the privileged `livespec-orchestrator` tier; refer that to `livespec-orchestrator-beads-fabro`'s own specification rather than deciding it here.
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
