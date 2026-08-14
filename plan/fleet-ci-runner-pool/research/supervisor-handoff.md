# Supervisor handoff — fleet-ci-runner-pool

**Ledger epic:** `livespec-s43svm`.

Read this file fully before acting. This is the restart state for the current
runner incident; the older rollout narrative is historical.

## Live incident state

The fleet is **up and serving CI**. `poweredge-xubuntu` has an active
host-local containment service:

```text
ci-runner-rate-replenisher.service: active/running
```

It repeatedly scans the complete fleet, mints only inactive JIT slots at the
approved 80%-of-limit cadence (0.84 seconds), and starts each `runner@…`
unit. JIT runners exit after one job, so a one-shot ramp is not sustained
capacity. This transient service does not survive reboot; it is containment
until `livespec-s43svm.5` lands.

The complete configured scope is 482 slots:

| Repo | Slots |
| --- | ---: |
| `livespec` | 75 |
| `livespec-dev-tooling` | 63 |
| `livespec-driver-codex` | 67 |
| `livespec-driver-claude` | 66 |
| `livespec-orchestrator-git-jsonl` | 66 |
| `livespec-overseer` | 65 |
| `livespec-runtime` | 64 |
| `livespec-console-beads-fabro` | 16 |

Recovery proof: `livespec-overseer` PR #896 completed all 66 checks with no
queue, and the pool refilled to 65 online overseer runners. Verify capacity
per routed repository; an aggregate runner count is not recovery evidence.

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

## Current root causes

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

## Restart sequence

1. Read epic `.5` through `.10`; inspect #1400 and #1399 before touching their
   worktrees.
2. Check containment without credentials:

   ```bash
   ssh -o BatchMode=yes poweredge-xubuntu \
     'systemctl show ci-runner-rate-replenisher.service \
       -p ActiveState -p SubState -p ExecMainStatus -p Result'
   ```

3. Verify each routed repo's Actions runner capacity and queued/running jobs.
4. If containment is down while jobs queue, restore the same complete paced
   scope only; never parallelize ramps or start the old bulk supervisor.
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
