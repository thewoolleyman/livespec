# Leg A result and the keep-original-bytes measurement (2026-11-07)

Leg A failed, and the keep-original-bytes measurement was negative. An already-open Codex session keeps failing its hooks after a plugin's content changes, and its safety guard then fails open. Restoring the original bytes at the superseded version path does not help. So plan assertions 1 and 6 look unachievable by any Driver change on current Codex. Whether to reword them is the maintainer's decision, and they stand as written until it is made.

This note records what was measured on the dev host (`vmi3006760`), what was read from Codex's source, and which conclusions are inferred. The procedure is in `acceptance-proof-plan.md`, §"Leg A". All times are UTC.

## What ran

The session under test was an interactive Codex TUI, codex-cli 0.166.0, thread `01a1b78b-ddfb-72f0-98f7-d34537e9f4fc`, in a scratch git directory under `tmux -L hookcache-accept`. It started at 19:44:53Z, before the release under test was published at about 20:18Z.

The vps-info stopgap `codex-hook-trust.timer` was stopped from 19:41:48Z to 20:24:53Z, so it could not mask the result. The observer was untouched until the apply described below.

The upgrade was `just ensure-codex-plugins` in the `livespec` repository, from 20:19:15Z to 20:19:59Z, exit 0, with no manual alias, trust or cache step. It moved only the Driver, from 0.12.1 to 0.12.2. The orchestrator (0.301.0) and livespec (0.47.0) were already current, so this was not an upgrade of every fleet plugin. The observer rebuilt the aliases by about 20:20:15Z.

## Results

| Time | Step | Result |
|---|---|---|
| 19:46:26Z | Harmless turn, before the upgrade | Completed, no "Hook failed" |
| 19:47:16Z | Guard probe, before the upgrade | Blocked by the Driver's `livespec_footgun_guard.py` |
| 20:20:26Z | Harmless turn, same session, after the upgrade | Completed, with "Hook failed: plugin contents changed; hook approval required" |
| 20:21:07Z | Guard probe, same session, after the upgrade | NOT blocked. The command ran and exited 128 only because the Codex sandbox makes `.git` read-only |
| 20:22:47Z | Guard probe with the original 0.12.1 bytes restored | NOT blocked, same failures, same exit 128 |
| 20:23:51Z | Fresh `codex exec` in the same directory | Hooks ran and the guard blocked the probe |

In each post-upgrade probe turn, three "Hook failed" lines appeared before the tool ran and three after. Which hooks those were is not recorded, because the failure text does not appear in the rollout file. Three per turn end is consistent with the Driver's three Stop hooks.

No commit was created in any step. In the unblocked probes that was the sandbox's doing, not the guard's.

The fresh session started before the timer restarted, so the stopgap played no part in it. Re-trust therefore works for new sessions; only already-open sessions are exposed.

**Path continuity held.** Every superseded version of both hook-declaring plugins resolves in one hop through `latest`, and every declared entrypoint exists there. That supports assertion 2. It does not make assertion 1 pass.

**The original-bytes arm.** From 20:22:45Z to 20:23:49Z, `livespec-driver-codex/livespec/0.12.1` was a real directory rather than an alias, byte-identical to the pre-upgrade manifest, and the observer did not revert it. Afterwards the alias was restored by hand and the cache matched the pre-swap manifest exactly.

**Limits of this arm.** It is one arm. The bytes went back after the session had already failed, and there was no arm in which the original bytes were never replaced. The peer-thread-start rewrite arm named in the deferred measurement was not run.

**Re-trust wrote the correct value.** A port of Codex's fingerprint gives `sha256:60179ed9…` for 0.12.2, which equals the `trusted_content_hash` on all nine Driver hook entries in `config.toml`. The same port gives `sha256:28bc6327…` for the 0.12.1 snapshot. The agreement on 0.12.2 is what validates the port.

**A version bump alone triggers it.** Between the 0.12.1 and 0.12.2 payloads, the only file that differs is `.codex-plugin/plugin.json`, and `hooks/` is byte-identical. So every Driver release does this to every already-open session, including releases that touch no hook.

**This contradicts a ratified scenario.** `SPECIFICATION/scenarios.md` in `livespec-driver-codex`, "an already-open session keeps running its hooks after a covered plugin's installed content changes but its hooks do not", says the session's next turn runs those hooks with no failure and its PreToolUse guard denies a forbidden command again "rather than failing open". Its precondition held exactly, and the behaviour is the opposite. Rewording plan assertions 1 and 6 would therefore not be enough on its own: that scenario would also have to be revised, or stay false.

## What Codex's source says

Read at tag `rust-v0.166.0` of `openai/codex`, under `codex-rs/hooks/src/engine/`:

- `plugin_trust.rs`: `PluginHookTrust::verify` re-hashes the plugin root on every hook execution and compares the result with the `trusted_content_hash` held on the handler. A mismatch returns the exact text "plugin contents changed; hook approval required".
- `plugin_fingerprint.rs`: the hash covers file names and bytes, excluding `__pycache__`, `.venv`, `.pyc` and `.egg-info`. A root that is a symbolic link returns a different error, "plugin root is not a directory".
- `command_runner.rs`: a failed verify finishes the run with the outcome `trust_error`, and the hook command never runs.
- `dispatcher.rs`: the should-block decision reads only the status `Blocked`. This matches the observed behaviour, where the tool ran. The mapping from `trust_error` to a run status was not read.

`plugin_trust.rs` and `command_runner.rs` are identical at `rust-v0.167.0` and on `main` as read on 2026-11-07, so upgrading Codex does not change them.

## What is inferred

The session appears to hash the NEW version's root against the hash it approved at startup. The evidence is indirect. A symbolic-link root would have reported "plugin root is not a directory", which never appeared, and restoring the bytes at the 0.12.1 path changed nothing. The code that refreshes the root in a running session was not read.

This corrects the working hypothesis in the epic's handoff of 2026-11-04T03:58:58Z, that the session re-hashes the content it captured at startup. If that were so, the restored bytes should have matched.

Re-enabling the stopgap should not repair an open session, because the correct trust was already in `config.toml` when these turns failed. That was not tested.

## Effect on the plan

- Assertions 1 and 6 remain unmet and stand as written, pending the maintainer's ruling routed through `legacy-coordinator-agent` on 2026-11-07.
- The fail-open is tracked separately from the plan's assertions as `livespec-driver-codex-sjwyha`, so it is not lost whichever way that ruling goes.
- `openai/codex#31383` is related, not identical: it reports exit-1 failures on 0.142.5. Nothing is to be posted there without the maintainer's approval.
- After the leg, `just ansible-apply ansible/dev-host.yml --tags codex_config` in `livespec-dev-tooling` staged the observer at v0.12.2, at 20:27:48Z. The drift report was read first. The observer restarted and `config.toml` did not change.

The manifests, payload copies and screen captures behind this note were in a session-private scratch directory and are not durable. This note, the epic's ledger entries and `livespec-driver-codex-b5rhjf` are the durable account.
