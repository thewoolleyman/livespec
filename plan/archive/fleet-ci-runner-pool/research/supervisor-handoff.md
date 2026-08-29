# Supervisor handoff — fleet-ci-runner-pool

**Ledger epic:** `livespec-s43svm`.

Read this file fully before acting. This is the restart state for the current
runner incident; the older rollout narrative is historical.

## Live incident state

The podman JIT pool this section used to describe is **DECOMMISSIONED** as of
2026-08-21. Everything below about it is HISTORICAL. Do not use it as a
live reading, and do not try to reproduce its measurements — they will not
reproduce.

What was done, maintainer-authorized in session `fix-runner-confusion`:
`ci-runner-rate-replenisher.service` stopped (it was a transient `systemd-run`
unit, so it no longer exists as a unit at all); all 482 `runner@*.service` units
stopped; all 482 podman-era forge registrations deleted in a paced pass. Detail
is journaled on `livespec-s43svm.19` at 2026-08-21T22:34Z, and the plan-level
consequences on the epic `livespec-s43svm` at 2026-08-21T22:40Z.

The fleet's gating CI now runs **entirely on k3s/ARC capacity** on
`poweredge-xubuntu`, which was already true before this cleanup — the podman pool
had served zero jobs since the cutover and nothing routed to its labels.

`livespec-s43svm.19` REMAINS OPEN. The repo-side deletion in
`livespec-dev-tooling` and host-side file removal were NOT done; the units,
`system-runner.slice`, the podman scripts under `/usr/local/lib/ci-runner/`, and
`/var/lib/ci-sup/ci-runner-rate-ramp.sh` are stopped-but-present.

### Historical — the podman pool as it stood until 2026-08-21

`poweredge-xubuntu` ran a host-local containment service:

```text
ci-runner-rate-replenisher.service: active/running   # STOPPED AND REMOVED 2026-08-21
```

It repeatedly scanned the complete fleet, minted only inactive JIT slots at the
approved 80%-of-limit cadence (0.84 seconds), and started each `runner@…`
unit. JIT runners exit after one job, so a one-shot ramp is not sustained
capacity. This transient service did not survive reboot; it was containment
until `livespec-s43svm.5` landed.

The configured scope **was** 482 slots. THIS TABLE IS THE SOURCE OF A COSTLY
MISREADING: on 2026-08-21 a per-repo row (`livespec` = 75) was compared against
the fleet total (482) as though the two contradicted each other. They never did —
the eight rows sum to exactly 482. Read a row as a row and the total as a total.

| Repo | Slots (historical) |
| --- | ---: |
| `livespec` | 75 |
| `livespec-dev-tooling` | 63 |
| `livespec-driver-codex` | 67 |
| `livespec-driver-claude` | 66 |
| `livespec-orchestrator-git-jsonl` | 66 |
| `livespec-overseer` | 65 |
| `livespec-runtime` | 64 |
| `livespec-console-beads-fabro` | 16 |
| **Fleet total** | **482** |

`livespec-driver-pi` is absent from this table and that is CORRECT rather than a
gap: it never had a podman-era pool, having been cut over directly to k3s as the
ninth repo.

Recovery proof (historical): `livespec-overseer` PR #896 completed all 66 checks
with no queue, and the pool refilled to 65 online overseer runners. Verify
capacity per routed repository; an aggregate runner count is not recovery
evidence.

Two facts measured during the decommission, worth carrying forward because both
outlive the pool:

- **Stopping a runner unit does NOT deregister it.** After stopping
  `runner@thewoolleyman-livespec-1.service`, its registration was still present
  at the forge and still reported `status: online`. Explicit DELETE is required,
  and the `status` field is stale for a while after a stop. Verify against the
  forge registry, not the host, and not immediately.
- **A repo's `total_count` mixes populations and moves.** ARC runners register
  with an EMPTY label array and autoscale, so `livespec` read 75, then 82, then
  80 within seconds. Any point-in-time runner count is a snapshot of a moving
  number composed of two populations. `livespec-s43svm.42` exists to make that
  unreadable-at-the-wrong-scope by construction.

### Non-negotiable operational rules

- Do **not** start `ci-runner-supervisor.service` while `.5` is unfinished.
  Its 482-slot startup fan-out previously hit GitHub secondary throttling.
- A rate limit controls mint *cadence*, not recovery *scope*. The default
  recovery target is every configured repo/slot. A partial scope needs explicit
  emergency authorization and an audit record.
- The temporary script is `/var/lib/ci-sup/ci-runner-rate-ramp.sh`; it has a
  45-second per-mint timeout and contains no credentials. Credentials are
  injected only by `with-github-ci-runners-env.sh`.
- `gate-runner-supervisor.service` on the factory host is the privileged
  golden-master lane. Do not treat it as normal pool capacity or change its
  trust boundary.
- Never expose JIT config, credentials, or process command lines carrying JIT
  data. Use `systemctl show`, API counts, and sanitized journals.

## Root causes — HISTORICAL, from the podman-era incident

These describe the decommissioned podman pool. Items 1-4 are retired with it.
Item 5 (dockershim) is retired only once `livespec-s43svm.19`'s repo-side
deletion lands; until then the shim is stopped-but-present on the host.

1. Normal CI was routed to `["self-hosted","local-ci","poweredge"]` while
   the local pool had no online capacity.
2. The old bulk supervisor was disabled after unbounded startup requests hit
   GitHub throttles.
3. Missing stable runner roots caused post-mint slot failures.
4. One-shot JIT waves are consumed after a job and cannot serve later matrix
   waves; the active replenisher is temporary containment.
5. A separate pre-command host failure remains: custom-container
   `/usr/local/lib/ci-runner/dockershim/docker` exits 1. Do not retry-storm it.

## Ledger / PR state

- `livespec-s43svm.5` — **active**: durable rate-aware JIT admission
  controller (`livespec-dev-tooling`). It replaces the transient replenisher:
  global single writer, bounded queue, pacing, cooldown/backoff, finite retry,
  restart safety, secret-free telemetry, and controlled full-fleet proof.
- `.6` — P1 slot preflight. PR
  [livespec-dev-tooling#1399](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1399)
  passed local full checks but CI is blocked before commands by dockershim.
  Retain `~/.worktrees/livespec-dev-tooling/fix/jit-slot-preflight`; do not
  repeat failed infrastructure jobs until `.10` is repaired.
- `.7` — P1 automatic hosted failover. It uses an always-hosted router plus a
  reusable CI body, with hysteresis, manual modes, audit/cost safeguards,
  fork-hosted enforcement, and privileged-gate exclusion. Commit `4df0294`
  passed 66 targets (2,749 tests, 100% coverage). PR
  [livespec-dev-tooling#1400](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1400)
  has passed CI and auto-merged (run `31769129914`). The worker is refreshing
  its primary and cleaning only its owned failover worktree.
- `.7.1` — migrate eligible fleet workflows after #1400; pinned reuse plus
  outage/recovery/fork proof; exclude privileged gate workflows.
- `.8` — P1 pending approval, depends on `.5`: default rate-limited recovery
  must derive the whole configured fleet; partial scope is explicit/audited.
- `.9` — P1 pending approval, depends on `.7`: independent verifier must reject
  recovery when a routed repo has queued work and zero capacity without hosted
  failover.
- `.10` — P1 ready: diagnose/fail closed on dockershim before job assignment;
  require controlled host proof and secret-free diagnostics.

All are children of epic `livespec-s43svm` (or `.7.1` as stated). The Beads
ledger is the durable work plan.

**This PR-state section is STALE and is not maintained in lockstep.** Several
items listed above as active or pending have since closed. Read the ledger, not
this list: `bd list --parent livespec-s43svm --status all`.

## Restart sequence

1. Read epic `.5` through `.10`; inspect #1400 and #1399 before touching their
   worktrees.
2. Do **NOT** check or restore `ci-runner-rate-replenisher.service`. It was
   stopped and removed on 2026-08-21 and the pool it fed is deleted. The unit
   no longer exists, so the old `systemctl show` check returns nothing
   meaningful.

   **DANGER — this step previously read "if containment is down while jobs
   queue, restore the same complete paced scope."** Following that now would
   re-mint 482 stranded runner registrations and undo `livespec-s43svm.19`.
   Never restart the replenisher, the ramp script, or
   `ci-runner-supervisor.service`.

3. Verify each routed repo's Actions runner capacity and queued/running jobs
   against **k3s/ARC**, which is the only capacity the fleet gates on. Note
   that a repo's `total_count` moves under ARC autoscaling and carries no
   scope label — see `livespec-s43svm.42`.
4. If gating jobs are queued with no capacity, diagnose via
   `livespec-s43svm.41`'s pool-health signal (scaling / pool absent / wedged
   runner / genuine exhaustion). Do not reach for the podman pool.
5. Confirm #1400 cleanup, then execute `.7.1` in bounded repo slices.
6. Repair `.10`, then rerun #1399's failed jobs once—no retry storm.
7. Prioritize `.5`; after controlled proof, replace the transient replenisher
   with the durable controller and prove full-fleet recovery.

## Repository protocol

- Tracked changes: worktree → PR → required checks → rebase merge → primary
  refresh → cleanup. Do not edit this tracked file in the dirty primary
  checkout.
- Do not delete unfamiliar worktrees, especially the two named dev-tooling
  worktrees above.
- Only `tmp/overseer/<topic>/` is a primary-checkout runtime exception; it
  never permits tracked-file edits.
