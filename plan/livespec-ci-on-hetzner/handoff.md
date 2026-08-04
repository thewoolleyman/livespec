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

**Read this paragraph before running anything.** As of 2026-08-04 there is **NO unblocked implementation work left in this epic**. Every slice is either closed or waiting on something this thread does not own. Do not go looking for a slice to drive — you will either find none or re-drive finished work. What this thread is waiting on is exactly two things:

1. **One maintainer decision**, on the fleet-red P0 `livespec-dev-tooling-irtt`. It is fully diagnosed and the option set is laid out under "The one open decision" below. Nothing else in this thread is blocked by it, but landing further `livespec-dev-tooling` releases while it is open pushes the breakage further into the fleet, so prefer settling it before cutting one.
2. **An external homelab gate** — `hl-wkyeqg` (provision server 3039451) and `hl-euzuhb` (ratify `hetzner-prod` admission) — which gates the last three slices and which this thread must not touch.

So your first action is the census below, run to CONFIRM that picture rather than to find work. If it shows the homelab gate has opened, the next slice is `livespec-3on57g`. If it shows the P0 decided, act on that decision. If it shows neither, this thread has nothing to do and you should say so rather than manufacture work.

Run a fresh read-only critical-path census. Every recorded number below is point-in-time and several have already moved:

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

Verify each command saw its intended input and retain raw output beside any derived count. Then re-measure the slices from the ledger; the table below records the cut, not live status. Per the paragraph above, expect to find nothing unblocked — confirm that rather than hunt.

## Resume state — 2026-08-04, after the fleet fail-open sweep

**`livespec-dev-tooling-3otdg4` is DONE — implemented, merged, green, and closed.** livespec-dev-tooling [#1274](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1274) merged as `70ec2887` with `just check` green at 66/66 and both `TDD-Red-*` and `TDD-Green-*` trailer blocks; its master CI run is `completed/success`. Epic `livespec-zmys` is closed with all six children closed. **Nothing on the non-Hetzner half of this thread is open.**

**One deviation, recorded rather than buried:** #1274 was intended to be held unmerged pending the decision below, and it AUTO-MERGED anyway — the repo's own `auto-enable-merge` workflow armed it as `app/livespec-pr-bot` fifteen seconds after it was opened. Five of the six sibling PRs had already auto-merged the same way in the same session, so it was foreseeable, and opening it as a DRAFT was the available safe form. The six-repairs-first ordering was satisfied and no repo was reddened by it; what was lost is the chance to sequence it against the P0 below. **Anyone opening a PR in these repos should assume auto-merge will be armed for them.**

**Attempt 4 failed like none of the first three**, then the work moved in-session. The dispatch died twice at `ACP turn failed: ACP protocol error` inside the Implement stage, before touching the task at all — an agent-runtime failure, not a spec failure, and a fifth dispatch through the same runtime had no reason to survive it. The handoff's pre-authorized fallback was taken: implemented in-session under Red-Green-Replay. The parked run was force-removed and the item reassigned off `fabro`.

**A measurement changed the shape of the work.** The item's groomed scope claimed the fail-open assertion would be "a genuine no-op in every fleet repo", so the fan-out could not redden siblings. Measured across all 13 repos in `.livespec-fleet-manifest.jsonc`, that was FALSE: six carried the fail-open fallback and five of those also run the check, so landing it first would have reddened five repositories — enforcement-before-adoption, the named cause of revert-worthy breakage in `.ai/ci-gate-discipline.md`. The maintainer chose to repair first.

**That sweep is done.** Epic `livespec-zmys` with six per-repo children, all merged: `livespec-runtime` [#472](https://github.com/thewoolleyman/livespec-runtime/pull/472), `livespec-driver-claude` [#417](https://github.com/thewoolleyman/livespec-driver-claude/pull/417), `livespec-driver-codex` [#397](https://github.com/thewoolleyman/livespec-driver-codex/pull/397), `livespec-orchestrator-git-jsonl` [#550](https://github.com/thewoolleyman/livespec-orchestrator-git-jsonl/pull/550), `livespec-overseer` [#698](https://github.com/thewoolleyman/livespec-overseer/pull/698), `livespec-console-beads-fabro` [#640](https://github.com/thewoolleyman/livespec-console-beads-fabro/pull/640). A fleet-wide re-measure returns ZERO remaining self-hosted `runs-on` fallbacks, and the same query returns 3 on the pre-repair trees so the zero is fail-capable. `livespec-orchestrator-beads-fabro` was excluded with reason, verified at byte level: its only three occurrences are `#`-comments and comments are stripped before parsing.

### The one open decision — a fleet-red P0 this thread found but must not decide alone

The sweep incidentally surfaced a **pre-existing fleet-red state**, filed as `livespec-dev-tooling-irtt` (P0, ready). **FIVE** repos' master CI is red — `livespec`, `livespec-runtime`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-beads-fabro`, `livespec-overseer` — all failing `check-public-api-result-typed`. It is not this thread's doing: every failing run names only `.py` files, and this thread's commits touched exclusively `.github/workflows/ci.yml` and Markdown.

**Root cause, localised to an exact commit by controlled bisect.** `check-public-api-result-typed` used to sit behind the `pure_trees` role-absence gate. Commit `46c5dab` ("scan the first-party universe, not pure_trees") removed that gate DELIBERATELY, shipping with its own design document, and un-shadowing the detectors was a stated benefit rather than a side effect. It first shipped in **`v1.18.8`** — *not* v1.18.9, which is how it presented, because the fan-out bumped consumers `v1.17.1` → `v1.18.9` in one step and they never saw v1.18.8. Proven by holding one consumer tree constant and varying only the checker: `v1.17.1` and `v1.18.7` exit 0 with zero violations, `v1.18.8` and `v1.18.9` exit 1 with eleven. Every affected repo declares `pure_trees` as `not_applicable` or `unarmed_until`, so the check had never actually run there.

**The measurement that reframes the remedy.** The raw violation count is 168, and that number overstates the work: 11 are in TEST files (`livespec-overseer` declares no `tests_tree_prefix`, so the role key falls back to `tests/` — that default is NOT vacuous, `tests/` really exists with 75 tracked files, but the repo ALSO keeps 59 test modules co-located directly under `overseer/`, and those are what the check reads as public API), and 56 are duplicate hits on byte-identical mirrored copies (`.claude-plugin/overseer/` and `overseer/`, sha256-verified, both tracked, no sync recipe found — so a fix must reach both). **The honest figure is 101 distinct functions**: `livespec-overseer` 56, `livespec-orchestrator-beads-fabro` 17, `livespec` 13, `livespec-runtime` 11, `livespec-orchestrator-git-jsonl` 4. Heuristically ~19 are parse/load/resolve functions that look like genuine `Result` candidates, ~18 are CLI entrypoints that look like a `supervisor_entry_files` config gap, and 64 need a per-function call.

So the choice is **not** the binary it first appeared to be. A third option exists: keep the un-gating, fix the check's test-tree scoping, let each repo declare the role keys that actually describe it, and treat the genuine residue as ordinary adoption work. The remedy was deliberately NOT self-resolved because reverting would undo a considered architectural improvement, and because the removed gate honoured `unarmed_until` — the blessed spelling that carries a LEDGER ID, used by three of the five affected repos, so the un-gating silently overrode deferrals that had been deliberately recorded. Whichever way it goes: no lever, env var, carve-out, or severity demotion — `li-4x3a45` is the recorded wontfix on exactly that, and enforcement must not precede adoption.

**A second defect was split out as `livespec-dev-tooling-zi29` (P1, ready)**, because the revert does not close it and closing the satisfying half would ship it silently. Its mechanism is established at step level, and it is NOT the "skipped matrix" story it was first filed with: on a zero-`.py` PR the job `check-public-api-result-typed` reports **`success`** while its `Skip when no .py changes` step succeeds and *every* real step — including the one that runs the check — is `skipped`. A REQUIRED context certifies nothing while presenting as a check that passed, and it does not even report `skipped`. That is why five masters could sit red while PRs kept merging. Four rival hypotheses were eliminated by measurement first and are recorded on the item. The trap is now written up as instance 16 in `.ai/verifying-against-the-right-source.md`.

**`zi29` is a cross-repo epic, not a one-repo patch** — measured after that write-up, so it is here and on the item but was not in the original filing. The `Skip when no .py changes` pattern is present in **six of the ten** fleet repos checked (`livespec`, `livespec-dev-tooling`, `livespec-runtime`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-beads-fabro`, `livespec-overseer`) and absent in four (`livespec-driver-claude`, `livespec-driver-codex`, `livespec-console-beads-fabro`, `homelab`). The producer repo has the hole too, and those six include **all five** repos currently red on `-irtt` — the mechanism and its consequence in the same set, which is exactly why the two items were split. Treat it the way `livespec-zmys` was treated: one epic, per-repo children, adoption before enforcement — because changing what a required context REPORTS is itself an enforcement change.

A third, smaller item is `livespec-dev-tooling-7ix8` (P2, ready): `just bootstrap` splices a `worktree_discipline` default into `.livespec.jsonc` and nothing commits it, so the prescribed first-touch setup leaves every fresh checkout dirty and never converges — which is exactly the `dirty_worktree` precondition the dispatcher preflight exists to clear.

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
| `livespec-dev-tooling-3otdg4` | `livespec-dev-tooling` | factory → **in-session** | `livespec-teasvm`, then epic `livespec-zmys` | Close the routing guard's label blind spot + hosted fail-closed assertion — **CLOSED 2026-08-04**, PR [#1274](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1274), merged `70ec2887`; 4 dispatches failed, implemented in-session, see Resume state |
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

Re-measured later the same day, after this thread's non-Hetzner half completed: **every one of those six values was unchanged.** That is worth knowing before planning around it — the gate did not merely fail to open, it did not move at all while a full six-repo sweep landed beside it. Thread 05's own handoff independently records the host dark at "row C" after a `type=hw` reset. Re-measure anyway; the point of recording two readings is that the second one is also expiring.

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

**Two of those bullets are already banked, verified independently on 2026-08-04 — re-measure rather than trust, but know they were true once.** The shared factory host carries no CI listener or worker process: no `ci-runner*` or `runner@` unit files remain, `/usr/local/lib/ci-runner/` holds only the four deliberately out-of-scope `gate-runner` scripts, and no listener process exists. And strict outside-collaborator fork approval was read from the forge as `all_external_contributors`, not inferred from prose. Also banked, though not itself a closing bullet: both gating `runs-on` values in this repo's `ci.yml` now fall back to `["ubuntu-latest"]`, the Phase-0 `ci-shadow/*` remote branches are gone, and `ci-selfhosted-shadow.yml` is deleted — each verified with a query shown to be fail-capable.

Everything else on that list is Hetzner-dependent and cannot be discharged until the homelab gate opens.

Closing `livespec-h22nve` archives this thread. Until those observations exist, an archived branch, a green local test, a registered idle runner, or a merged host module is decomposition progress—not delivery.

## Next-session command

Read exactly this one path and execute its named first action:

`plan/livespec-ci-on-hetzner/handoff.md`
