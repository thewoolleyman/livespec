## The maintainer's statement of what done means

RE these codex errors: 'Hook failed / No such file or directory (os error 2)'. There used to be logic in place to automatically update the codex cache on hook releases and avoid this problem. Something has regressed recently. I want you to open a work item bug and plan to address this ... The preference should be to find the previous plan, which handled the Codex hook updates and caching to avoid this problem, and reference it in the new plan. Update old plan with a comment linking to this regression, create new plan with a modern definition of done, etc.

## Definition of Done assertions derived from that statement

- A Codex session started on the dev host before a marketplace upgrade of every fleet Codex plugin completes a turn after that upgrade with no 'Hook failed' error, and every hook command it captured at startup resolves to an existing entrypoint in a validated current payload.
- After a marketplace upgrade, each superseded version directory name of every fleet Codex plugin that declares hooks resolves through one hop, old-version to latest to current-version, to a payload in which every declared hook entrypoint exists.
- The set of plugins the hook-cache reconciliation covers is derived from the plugins installed in the Codex cache, so a fleet plugin that first declares a Codex hook in a later release is covered without a code or configuration change.
- The hook-cache observer is running on the dev host after a host reboot with no Codex or Claude session having started it.
- A release-gating check fails, naming the plugin and hook, when a fleet plugin declares a Codex hook that the hook-cache reconciliation does not cover, so such a release cannot reach the release channel silently.

# Codex plugin hook-path regression — charter and first measurement

## Charter

Codex seats report `Hook failed / No such file or directory (os error 2)` at
turn end. This plan restores hook-path continuity for long-running Codex
sessions across marketplace upgrades of EVERY fleet Codex plugin, not only the
Driver, and adds a gate so a release cannot silently re-open the gap.

### Prior art this plan builds on (read first)

- `plan/archive/workaround-codex-plugin-bug/` (livespec repo), epic
  `livespec-ipfg65`, closed 2026-08-14. Its research
  `research/compatibility-symlink-reconciliation.md` holds the root mechanism
  and the one-hop alias design (`old-version -> latest -> current`). It
  shipped the reconciler and observer in `livespec-driver-codex`
  (`dev-tooling/codex_hook_cache_reconcile.py`,
  `dev-tooling/codex_hook_cache_observe.py`, Driver spec history v007,
  https://github.com/thewoolleyman/livespec-driver-codex/pull/452, released
  v0.7.0). Its scope section said, verbatim: "A general repair for all Codex
  plugins is out of scope. This plan owns only the `livespec-driver-codex`
  payload and its declared hooks." That deferral is the gap this regression
  fell through.
- `livespec-overseer/plan/archive/codex-parity-and-rollout-safety/research/live-session-rollout-safety.md`
  (livespec-overseer repo): Codex binds hook entrypoints to absolute
  versioned cache paths for the process lifetime; `codex plugin marketplace
  upgrade` (run by `ensure-codex-plugins` at session start, and by Codex's own
  background auto-upgrade) prunes the old versioned directory, so a NEW
  session deletes the path a RUNNING session uses.
- `livespec-c1k9` (fleet plugin currency, closed) and `livespec-c1k9.10`
  (Codex upgrade wired into ensure-plugins) — the currency path that triggers
  the prune.
- `livespec-1p31` (backlog bug): adopt the oh-my-codex #3024 live-session
  rollout policy. ABSORBED by this plan as a child — the policy (keep old
  versioned paths resolvable; clean up only by TTL / liveness) is exactly the
  fleet-wide behaviour this plan's Definition of Done demands.
- `livespec-66knbc` (backlog epic): the first, superseded anchor of the same
  `workaround-codex-plugin-bug` plan; its requirement carriers were delivered
  under `livespec-ipfg65`. Disposition: closed as superseded by
  `livespec-ipfg65` (delivered) and this plan (remaining fleet-wide scope).

## First measurement — 2026-11-02 (all times UTC, from `date -u`)

Host: the dev host (`/home/ubuntu/.codex/plugins/cache`).

1. 14:21Z — `livespec-driver-codex/livespec/` holds real dir `0.8.4`, a
   `latest -> 0.8.4` link, and twelve aliases `0.6.1..0.8.3 -> latest`. The
   Driver observer is running (`codex_hook_cache_observe.py run
   --marketplace livespec-driver-codex --plugin livespec`, pid 2600355, up
   10 days), state file `~/.local/state/livespec-driver-codex/hook-cache-state.json`.
   The Driver workaround is intact.
2. 14:21Z — `livespec-orchestrator-beads-fabro/livespec-orchestrator-beads-fabro/`
   held ONLY `0.274.2`; `livespec/livespec/` ONLY `0.45.0`;
   `livespec-overseer/livespec-overseer/` ONLY `5.46.0`. No `latest`, no
   aliases. No observer runs for any of them.
3. 14:23Z — the orchestrator cache had moved to ONLY `0.275.0` (written
   14:22:13Z by an upgrade during this session); `0.274.2` was deleted. Any
   Codex process that started under 0.274.2 or earlier now holds hook paths
   that do not exist. Live Codex processes at that instant had started at
   00:05Z, 07:34Z and 14:20Z.
4. Hooks declared by the orchestrator plugin (`hooks/hooks.json` in 0.275.0):
   SessionStart `codex_yolo_reapply.py`, SessionStart
   `registered_plugin_currency_warning.py`, Stop `session_wait_stop.py`, each
   as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<file>"` behind an
   `if [ -n "${CODEX_THREAD_ID:-}" ]; then exit 0; fi` guard. Codex's
   `~/.codex/config.toml` `[hooks.state]` lists them as
   `livespec-orchestrator-beads-fabro@...:hooks/hooks.json:{session_start:0:0,session_start:0:1,stop:0:0}`.
   The overseer and core plugins declare no Codex hooks today.
5. Orchestrator `hooks.json` history (orchestrator repo):
   `d9c939167` 2026-07-19 SessionStart yolo reapply;
   `b79f4e878` 2026-10-29 Stop hook `session_wait_stop.py` (first release
   v0.261.0, 2026-10-30T03:30Z); `bea06155d` 2026-10-31 second SessionStart
   hook (first release v0.264.0). Before b79f4e878 the orchestrator had only a
   SessionStart hook, which runs once while the directory still exists; the
   Stop hook runs at EVERY turn end, which is why the failure surfaces at turn
   end and became visible from 2026-10-30.
6. Release cadence makes the window wide: the orchestrator cut more than one
   hundred releases between 2026-10-25 and 2026-11-02, so almost any Codex
   session older than about an hour holds a pruned path.

### Answer to the coordinator's either/or

The aliases were NOT removed: the orchestrator cache never had any — no
observer, state file, or alias for it exists, and the shipped reconciler's
defaults and its ratified Driver contract cover only `livespec-driver-codex`.
The regression is the orchestrator plugin ACQUIRING a per-turn Codex hook
(Stop, v0.261.0) under an alias mechanism scoped to the Driver alone.

### Open hypothesis (to measure, not assumed)

`os error 2` is a spawn error, not a Python `can't open file` error. The
`CODEX_THREAD_ID` guard does not prevent it, which suggests Codex spawns the
hook with the (deleted) plugin root as working directory or resolves the
command against it. Slice 1 measures this; it decides whether guarded,
"Codex-skipped" hooks are also exposed.

## Design direction (to be ratified through the Driver spec)

Generalize the Driver's reconciler + observer from one hard-coded plugin to
every fleet plugin installed in the Codex cache whose payload declares hooks
(derived from the installed caches, never a hard-coded list), with per-plugin
observed-version state, the same one-hop topology, payload validation and
unsafe-path refusal. Supervise the observer so it survives reboot without a
session starting it. Add a release-gating check that fails when a fleet
plugin declares a Codex hook the reconciler does not cover. The Driver spec
(livespec-driver-codex `SPECIFICATION/`, history v007) currently restricts the
contract to the Driver's own payload, so the change goes through
`/livespec:propose-change` → independent review → `/livespec:revise` in that
repo before implementation.

## Stopgap and second generalization gap — 2026-11-02T14:31Z

The full operational record (path, how to check liveness, restart, stop and
the retirement trigger) is a ledger comment on bug `livespec-gqjkge`. The
summary:

- Running the Driver's shipped observer against the orchestrator, configured
  only by its `--marketplace` and `--plugin` flags, does NOT work.
  `validate_payload` refuses the orchestrator payload with
  `.codex-plugin/plugin.json: manifest declares no hooks entry`. The
  orchestrator ships `hooks/hooks.json` without a manifest `hooks` key, and
  Codex loads it from that default location; `[hooks.state]` in
  `~/.codex/config.toml` confirms it. **The durable reconciler must discover
  hooks the way Codex does: from the manifest entry OR from the default
  `hooks/hooks.json`.**
- Observer status is keyed by the state file's DIRECTORY. A second instance
  whose state file sits in the Driver's state directory therefore reports
  "running and healthy" off the Driver's heartbeat. Per-plugin state and
  status must be isolated.
- Stopgap: `/home/ubuntu/.local/bin/livespec-codex-hook-cache-stopgap.py`, a
  host-local, unsupervised process. It keeps one-hop `old -> latest ->
  newest-real` links for the orchestrator, overseer and core caches. It is
  inotify-driven with a 30 s safety sweep, and uses 0.03 % CPU. A reboot kills
  it. It is retired once the durable reconciler is verified.

## Carriers and routing (design direction)

- Spec: livespec-driver-codex `SPECIFICATION/` (history v007 restricts the
  reconciler contract to the Driver's own payload). A propose-change widens it
  to every installed fleet Codex plugin whose payload declares hooks, found by
  either discovery route. It also requires per-plugin state and status
  isolation, supervision that survives a reboot, and a release-gating coverage
  check.
- Implementation: livespec-driver-codex work-items filed after ratification,
  dispatched through the factory.
- Supervision across reboot is delivered by the host-provisioning automation,
  never hand-installed (GitOps rules).
