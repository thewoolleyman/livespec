# Acceptance proof plan — real already-open Codex sessions surviving normal plugin upgrades

This note plans the host-captured acceptance proof for plan `codex-plugin-hook-path-regression` (livespec epic `livespec-3rfjga`). The maintainer's directive, recorded verbatim in `durable-fix-scope.md` in this directory, requires it: "a real already-open Codex session surviving a normal plugin upgrade and executing its captured hooks correctly, plus verified supervisor startup and recovery behavior", where "direct script execution and green CI are useful but do not replace it".

It was written on 2026-11-03, after the spec phase finished. Four spec versions were ratified for this plan:

- livespec-driver-codex v015 `codex-hook-trust-continuity` (PR #941);
- livespec-driver-codex v016 `supervise-the-generalized-codex-hook` (PR #943);
- livespec-driver-codex v017 `codex-observer-no-start` (PR #948);
- livespec-dev-tooling v118 `shared-check-fail-a-fleet` (PR #3248).

## What each leg proves

The plan Definition of Done has eight assertions (on the epic, `livespec-3rfjga`). In the table below, the "Assertion" column gives each one's number, and the "Leg" column names the proof step in the next section that exercises it. "Human" in the "Who runs it" column means the maintainer has to act, either because the step needs physical presence or because it reboots a machine, which the directive forbids doing casually.

| Assertion | What must be observed | Leg | Who runs it |
|---|---|---|---|
| 1 | A dev-host session started before a marketplace upgrade of every fleet Codex plugin completes a turn after it with no "Hook failed", and every captured hook resolves | A | This seat |
| 2 | Each superseded version name resolves in one hop to a payload whose entrypoints exist | A (cache inspection) | This seat |
| 3 | Coverage is derived from the installed cache, so a newly hook-declaring plugin is covered | Factory proof of `livespec-driver-codex-esytmj`, re-read here | Factory, then this seat |
| 4 | The dev-host observer is running after a host reboot with no session having started it | D (service-manager verification, no reboot) | This seat |
| 5 | A release-gating check fails on an uncoverable Codex hook | Factory proof of `livespec-dev-tooling-yhacv6` | Factory |
| 6 | On the MacBook Pro, an already-open session survives a normal upgrade of every fleet plugin, runs every captured hook, and shows no "Hook failed" | E | This seat over ssh, with the maintainer for the TUI if needed |
| 7 | On the MacBook Pro, the observer is started by launchd at login and restarted after it exits | F (restart), G (LaunchAgent verification plus kill-and-restart, no logout) | This seat for F; human for G (runs it by hand on the Pro) |
| 8 | On the dev host, the observer is restarted by its supervisor after its process exits | C | This seat |

## Preconditions, all required before any leg

1. **Released, not merged.** The runs of `livespec-driver-codex-esytmj`, `-p3oixg`, `-v52m6a` (trust continuity), `-n2b3ui` (no-start, newest result) and `-yudufr` (launchd) have merged and are included in a livespec-driver-codex release. `livespec-dev-tooling-j7pb7s` (the lingering systemd unit) has merged and has been applied by the provisioning automation. Every leg runs against the released artifact installed through its normal path (`just ensure-codex-plugins` in the `livespec` repo on the dev host; the Codex marketplace on the Pro), never against a working tree.
2. **The stopgap is retired first.** The dev host's temporary observer (`~/.local/bin/livespec-codex-hook-cache-stopgap.py`) is stopped and removed BEFORE leg A, and the Pro's Driver-only observer (pid 76038, if still alive) is stopped before leg E. Otherwise the proof would show the stopgap working, which is what the 2026-11-03 attempt in this plan actually proved. A one-line check proves the retirement: no process matches the stopgap path, and the heartbeat file is no longer updated.
3. **The supervised observer is healthy.** On the dev host, `systemctl --user is-active livespec-codex-hook-cache-observer.service` reports `active`, and `codex_hook_cache_observe.py status --all --expected-pid <MainPID>` reports the observer running and healthy for every fleet plugin it covers after its first completed reconcile. On the Pro, the shipped LaunchAgent is installed (pre-authorized by the maintainer, relayed 2026-11-02) and loaded, and `status --all` reports the same.

   This reads fleet plugins, not every covered plugin, because a covered third-party plugin with no release tag MUST be reported as unverified and is never trusted (livespec-driver-codex `contracts.md` §"Codex hook-cache compatibility"). `honeycomb-plugins/honeycomb` on the dev host is that case, so `status --all` exits 1 there while every fleet plugin is healthy. That exit is expected and does not fail this precondition: read each plugin's line rather than the exit status, and keep honeycomb's line in the captured output.

   Two recipes share the name `ensure-codex-plugins`, and they differ here. The one in the `livespec` repo, which leg A uses, runs only the Codex marketplace and plugin commands, so its exit 0 says nothing about plugin health. The one in `livespec-driver-codex` also runs `codex_hook_cache_observe.py provision --all`, which returns non-zero for any unhealthy covered plugin, so by its source it exits 1 on the dev host for the honeycomb reason above.
4. **Hook trust is current.** The provisioner reports no untrusted covered hook. Trust is never granted by hand during a leg: under v015, the reconciler re-establishes it from release-verified bytes, and a manual trust step would void the leg.

## The legs

Each leg records start and end times from `date -u` taken at the moment of each step, not reused from earlier. It also records the exact plugin versions read from the Codex cache before and after, and the captured output.

**Leg A — dev-host already-open session across a normal upgrade (assertions 1, 2).**
1. In a scoped tmux server (`tmux -L hookcache-accept`, never the default socket), start an interactive Codex TUI in a scratch git directory, and record the plugin versions it captured.
2. Baseline turn: run a harmless command, then ask the session to run `git commit --allow-empty --no-verify -m guard-probe-pre`. The Driver's PreToolUse guard must BLOCK it; the blocked commit is the positive signal that hooks run, because Codex 0.166 does not log successful hook runs.
3. Trigger a normal upgrade of every fleet Codex plugin through the normal path, with no manual alias, trust or cache step. If no new release of a plugin is available when the leg runs, the leg waits for one rather than fabricating one; a same-version re-materialization is the secondary case (v015).
4. In the SAME session, run a harmless turn, then the guard probe again (`guard-probe-post`). Pass: zero "Hook failed" lines across both turns, the guard blocks, and no trust prompt appears.
5. Cache inspection: each superseded version name of each plugin that declares hooks resolves through `latest` to the current version, and every declared entrypoint exists there (assertion 2).

**Leg B — re-materialization at an unchanged version (assertion 1, v015 case).** If Codex re-materializes a plugin at the same version during the window, the same session check as A.4 applies. This leg is opportunistic. It is recorded when it happens and is not forced.

**Leg C — supervised restart on the dev host (assertion 8).** Record the observer's pid and heartbeat, then send that process SIGTERM. That signal comes from this seat as the operator. It is not sent by `ensure-codex-plugins`, which v017 forbids from signalling an observer. Pass: systemd starts a new process with a new pid within its restart delay, its heartbeat is newer than the kill, `status --all --expected-pid <new pid>` reports it running and healthy for every fleet plugin it covers (precondition 3 explains why this reads fleet plugins), and no Codex or Claude session started it.

**Leg D — dev-host reboot survival (assertion 4), by service-manager verification.** CORRECTED 2026-11-04. The maintainer ruled on 2026-11-03 (recorded verbatim in the epic's scope event of 2026-11-03T23:15:01Z): "This ain't gonna happen, if it's set up in launchd or init script, then verifying and running those is proof enough". So no reboot is performed. Instead this seat verifies on the dev host that the observer unit is enabled (`systemctl --user is-enabled livespec-codex-hook-cache-observer.service` reports `enabled`), that it is wanted by `default.target`, that the operator account lingers (`loginctl show-user ubuntu` reports `Linger=yes`), and that the unit is active. Together those mean systemd starts the observer at boot with no session. This leg PASSED on 2026-11-03 at 23:12:41Z; the evidence is in the epic's handoff of 2026-11-03T23:15:21Z.

**Leg E — Pro already-open session across a normal upgrade (assertion 6).** This is the same procedure as leg A, run on `chads-macbook-pro` over the recorded OpenSSH route. The TUI runs in a tmux server scoped on the Pro. If the code-mode host cannot be negotiated from a non-GUI ssh context, the maintainer starts the TUI in a GUI terminal. This seat then drives the turns and reads the transcript. A GUI start does not change what the leg proves.

**Leg F — launchd restart on the Pro (assertion 7, restart half).** This is the same procedure as leg C, with launchd. Pass: a new pid, a fresh heartbeat, and no session started it.

**Leg G — launchd start at login (assertion 7, login half), by LaunchAgent verification. HUMAN-ATTESTED.** CORRECTED 2026-11-04 under the same 2026-11-03 maintainer ruling: no logout is performed. The maintainer runs these steps by hand on the Pro. (1) `launchctl print gui/<uid>/com.livespec.codex-hook-cache-observer` shows the agent loaded and running. (2) The installed plist carries `RunAtLoad` = true, which is what makes launchd start the observer at login, and `KeepAlive` = true. (3) Kill the observer process. (4) launchd restarts it with a new pid and a fresh heartbeat, with no Codex or Claude session opened in between. This leg PASSED on 2026-11-04; the maintainer's pasted output is in the epic's handoff of 2026-11-04T00:25:18Z.

## Recording and verification

The capturing session posts one plan record with verdict `captured` through `dispatcher.py post-plan-record`. The record carries the build identities exercised and, for each assertion, the numbered steps and their proof. A DIFFERENT session then replays the steps and posts `verified`. The posting primitive refuses a `verified` record from the capturing identity. Leg D is host-captured: its verification steps are replayed by the different session like any other leg. Leg G is posted as `human_attested`, because the maintainer ran it by hand on the Pro. After the plan record is verified, an independent completeness reviewer commissioned under the archive gate checks every assertion and deferral against the child set. Only then are `livespec-gqjkge` and `livespec-1p31` closed and the plan archived.

## Failure handling

A failed leg is a finding, not a retry target. The failing release, plugin, hook, and captured output go on the owning work item. A "Hook failed" line in leg A or leg E reopens the question of which half of hook continuity broke: path continuity (aliases) or trust continuity (v015). Each half has its own owner, `esytmj`/`p3oixg` and `v52m6a` respectively.
