# Durable fix scope — maintainer directive of 2026-11-02 and the reconciliation it triggered

This note records the scope change for plan `codex-plugin-hook-path-regression` (livespec epic `livespec-3rfjga`). The scope change follows a maintainer directive relayed by `legacy-coordinator-agent` at about 23:15Z on 2026-11-02. It holds the directive verbatim, the reconciliation of existing work across the fleet repositories, the dispositions taken, and the plan Definition-of-Done assertions derived from the directive.

## The maintainer's statement (verbatim, as relayed by the coordinator)

Take ownership of permanently fixing the Codex hook failures in thread codex://threads/019edb72-6382-7163-8ed5-7ed14206ed07. Run this through the proper livespec workflow on the VPS: load the current coordinator skills and repository instructions, establish or resume the appropriate herdr plan and session, and follow all required ledger, ownership, delegation, testing, review, release, and provisioning rules. Discover the actual commands and workflow from the installed skills. Do not improvise a parallel process.

First inspect the thread and VPS ledger history across livespec, livespec-driver-codex, livespec-orchestrator-beads-fabro, and livespec-overseer. Reconcile existing work and active owners before dispatching anything. Reuse the existing plan/session where appropriate rather than creating duplicates.

Goal: normal plugin auto-updates must not break hooks captured by already-open Codex sessions. Protection must start automatically and recover after process failure, login, or restart. Preserve hook behavior and safety enforcement; do not disable hooks or suppress errors to make tests pass.

Prior investigation and changes to verify:
- The target thread reportedly contains 822 unique hook-error prompts naming three missing Driver 0.8.3 Stop scripts after an update to 0.8.4.
- The MacBook Pro had no compatibility observer or aliases. A shipped detached observer was started, historical aliases restored, and Driver upgraded normally to 0.9.0. Six retained Stop-hook executions passed, and the safety guard still rejected unsafe input. This is partial mitigation, not a completed durable fix.
- That observer was last reported as PID 76038. Verify its current identity and health before touching it. It does not survive reboot.
- Draft PR https://github.com/thewoolleyman/livespec-driver-codex/pull/921 contains proposed macOS LaunchAgent provisioning, commit 187ae798107ab416d12ce008a9ce0b0fd5404f5d. CI was reported green. It has NOT been merged, and the LaunchAgent has NOT been activated. Review it under the proper livespec process; adopt, revise, or replace it as appropriate. Do not treat it as approved merely because it exists.
- Its handoff is recorded on livespec-driver-codex-yudufr. Inspect that record for worktree locations and evidence.
Existing ecosystem work:
- Core investigation: https://github.com/thewoolleyman/livespec/pull/3051
- Measurements: https://github.com/thewoolleyman/livespec/blob/master/plan/codex-plugin-hook-path-regression/research/charter-and-first-measurement.md
- Bug livespec-gqjkge; plan epic livespec-3rfjga; all-plugin implementation livespec-driver-codex-esytmj. Driver specification PR #918 was subsequently reported merged. Recheck all current states.
- esytmj and yhacv6 were reported to have queued factory launchers. Linux provisioning j7pb7s awaits the generalized release. Respect those owners and coordinate dependent work.
- Earlier Driver-only compatibility logic did not cover the orchestrator. Known gaps include default hooks/hooks.json discovery, observer state/health collisions, and unsupervised stopgaps. Read the ledger rather than assuming these remain unfixed.
- Overseer background: https://github.com/thewoolleyman/livespec-overseer/blob/master/plan/archive/codex-parity-and-rollout-safety/research/live-session-rollout-safety.md
Create a complete plan for implementation, regression coverage, release, managed host provisioning, and safe retirement of temporary observers. Cover relevant hook-declaring plugins and supported hosts, including the affected Pro. Keep Mac supervision compatible with the final generalized implementation rather than baking in a Driver-only state layout. Coordinate the work on the VPS and apply host changes through the approved livespec provisioning process.

Acceptance must include a real already-open Codex session surviving a normal plugin upgrade and executing its captured hooks correctly, plus verified supervisor startup and recovery behavior. The earlier live-session probe timed out negotiating its code-mode host, so that acceptance test is still unverified. Direct script execution and green CI are useful but do not replace it. Diagnose that test blocker through the proper workflow. Do not reboot my machines casually or bypass security controls.

Keep the ledger and herdr session current. Report the verified root causes, adopted or superseded changes, releases and host rollout status, test evidence, and any remaining blockers. Do not call this complete while only temporary aliases are repaired or required rollout and live-session verification remain outstanding.


## Definition of Done assertions added by this directive

The five original assertions in `charter-and-first-measurement.md` stand unchanged as assertions 1-5. The directive extends the goal to every supported host, including the MacBook Pro, and to supervised start and recovery. That adds three assertions:

6. On the MacBook Pro, a Codex session that was already open before a normal marketplace upgrade of every fleet Codex plugin completes a turn after that upgrade, runs every hook it captured at startup, and shows no 'Hook failed' error.
7. On the MacBook Pro, the hook-cache observer is started by the user's service manager at login and restarted by it after its process exits, with no Codex or Claude session having started it.
8. On the dev host, the hook-cache observer is restarted by its service supervisor after its process exits, with no Codex or Claude session having started it.

These assertions are derived by this session from the directive; the maintainer has not separately confirmed their wording. The directive's own acceptance clause — a real already-open session surviving a normal upgrade, and verified supervisor start and recovery, with green CI or a direct script run not counting — is what assertions 1, 4, 6, 7 and 8 operationalize.

## Reconciliation (ledger reads, 2026-11-02 23:1x-23:5xZ)

| Item | Repository | State | Relation |
|---|---|---|---|
| `livespec-gqjkge` | livespec | blocked | the bug; closes when the plan-level proof proves assertions 1-2 |
| `livespec-1p31` | livespec | backlog | the absorbed oh-my-codex #3024 live-session policy |
| `livespec-driver-codex-esytmj` | livespec-driver-codex | ready, factory-queued | the generalized reconciler and observer for every hook-declaring plugin, plus the systemd user unit (assertions 1-3) |
| `livespec-driver-codex-yudufr` | livespec-driver-codex | ready, held | re-cut on 2026-11-02 as the macOS launchd counterpart of esytmj, sequenced after it |
| `livespec-dev-tooling-j7pb7s` | livespec-dev-tooling | ready, held | installs the systemd user unit with lingering on the dev host (assertion 4); waits for esytmj's release |
| `livespec-dev-tooling-yhacv6` | livespec-dev-tooling | ready, factory-queued | the release-gating coverage check (assertion 5) |
| `bd-ib-xqd4hv` | livespec-orchestrator-beads-fabro | ready | side defect: filing graded j7pb7s's References against the filer's repository |
| `overseer-vfz5v5` | livespec-overseer | pending-approval | one of the upgrade trigger sites; adjacent, not a carrier |

## Dispositions

**Draft PR livespec-driver-codex#921 (macOS LaunchAgent): superseded and closed.** An independent read-only review found four blockers:

1. `ensure-codex-plugins.sh` still runs `observe ensure`, which can SIGTERM the launchd observer and spawn a detached duplicate.
2. The PR hardcodes the Driver-only scope and the pre-esytmj state and heartbeat layout, against the v014 requirement of per-marketplace-and-plugin records.
3. The supervisor is generated at runtime rather than shipped, and `ensure` does not check it.
4. Health can pass before the first reconcile.

The full review is on the PR. Its sound parts are carried into the re-cut yudufr.

**j7pb7s needs-human block: false positive, released.** Released under coordinator ruling R493. Root cause filed as `bd-ib-xqd4hv`.

## Host findings

- **Pro reachability.** The VPS reaches the MacBook Pro (`chads-macbook-pro`, MacBookPro18,2, macOS 26.5.2) over tailscale ssh. Read-only checks only.
- **Pro observer.** Detached pid 76038 is alive and was started on 2026-11-02 at 07:56 local time. It runs the Driver's `codex_hook_cache_observe.py run`, with no LaunchAgent. The cache holds 0.8.3, 0.8.4, 0.9.0 and `latest`.
- **No approved macOS provisioning path exists.** The livespec-dev-tooling Ansible inventory declares only legacy Ubuntu hosts. A one-time install of the shipped LaunchAgent on the Pro is a maintainer decision, raised through the coordinator.
- **Live-session probe blocker (likely, unconfirmed).** On the Pro, an ephemeral `codex` resolves to the Homebrew cask 0.163.0, whose `codex-code-mode-host` carries the `com.apple.quarantine` attribute. A first launch of that host from a non-GUI ssh context can stall past the handshake timeout. Version skew may add to it: CLI 0.163, daemon 0.166, desktop app 0.162-alpha. The remedy (cask upgrade plus Gatekeeper first-run approval) is a maintainer decision, raised through the coordinator.
- **Acceptance method.** Use a real interactive Codex TUI session in a scoped tmux server, never `codex exec`. Open it before a normal marketplace upgrade and send a further turn after the upgrade. The livespec-overseer live-exercise harness (`overseer-uzvcbn.4`) can host it but has no upgrade stage today.
- **Security side finding.** A process on the Pro carries an MCP API key in its command-line arguments. This was raised to the maintainer through the coordinator, and the value is not recorded anywhere.

## Explicit deferrals

- **A full macOS provisioning tree for the Pro.** Deferred: a single shipped LaunchAgent does not justify one. Reconsider if the maintainer rejects the one-time install route, or if more Mac-hosted services need management.
- **An upgrade stage in the livespec-overseer live-exercise harness.** Deferred: the acceptance proof is run by hand in a scoped tmux server. Reconsider if the proof has to be repeated per release.
