# Handoff — codex-acp version auto-bump (factory-gated freshness)

**State (build-ready, 2026-07-13).** The design (`design.md` beside this file)
is **APPROVED — all architecture decisions resolved by the maintainer**. This
is the LAST Phase 1 deliverable (epic `livespec-3lev.4`); building it closes
Phase 1. No code written yet.

## The resolved decisions (do not relitigate)

1. **Pin home = IMAGE ONLY.** `CODEX_ACP_VERSION` (in
   `livespec-dev-tooling/docker/fabro-sandbox/base/Dockerfile`) is the single
   source of truth. The orchestrator DROPS its explicit `@0.16.0` and consumes
   the baked global fetch-free: `CODEX_IMPLEMENTER_ADAPTER = "npx --no-install
   @zed-industries/codex-acp"` (in
   `livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_fabro_argv.py`).
2. **Cadence = WEEKLY, bump on ANY new `zed-industries/codex-acp` release.**
3. **Gate = EXTEND the existing golden-master** (`orchestrator-image/acceptance-live-golden-master.sh`)
   with a Codex-provider switch + a candidate-image override — not a new workflow.
4. **Priority = build this next.**

## Why we're here (context — don't redo the investigation)

The original Phase 1 plan proposed "drop `@0.16.0` → version-less." That was
**investigated in-image and abandoned (2026-07-13)**: `npx -y` (pinned OR
version-less) already runs the baked `codex-acp@0.16.0` global with **no per-run
download**, so version-less is a no-op that also removes a load-bearing
credential-projection pin (silent-drift risk, `bd-ib-ss7rkr`). The pin is
safer; the fix is to make it self-updating via a **tested** bump. Full evidence
in `design.md` §"Why not version-less". The empirical facts (verified against
`python-rust-v0.43.1`):
- `npx --no-install @…/codex-acp` runs the baked binary even with
  `--network none` (fetch-free, network-independent).
- `npx -y @…/codex-acp[@ver]` does a per-launch registry metadata round-trip
  (hangs offline) but no package download.
- Baked global resolves to mise node's globals
  (`…/mise/installs/node/26.3.0/lib/node_modules/@zed-industries/codex-acp`,
  version 0.16.0).

## Build plan (proposed PR breakdown)

Order chosen so the quick, independently-valuable orchestrator change lands
first and the automation follows.

### PR-A (`livespec-orchestrator-beads-fabro`) — orchestrator → baked global, fetch-free
- `_dispatcher_fabro_argv.py`: `CODEX_IMPLEMENTER_ADAPTER = "npx --no-install
  @zed-industries/codex-acp"` (drop `@0.16.0`; add `--no-install`). Update the
  load-bearing comment: the version is now the baked image's `CODEX_ACP_VERSION`,
  and the credential-projection re-verification (`bd-ib-ss7rkr`) is now EXECUTED
  by the auto-bump's Codex golden-master gate (point at it), not a manual TODO.
- Update the two tests that hardcode the string:
  `tests/…/commands/test_dispatcher.py` (~:1043, `acp_adapter=npx -y …@0.16.0`)
  and `tests/…/commands/test_dispatcher_dual_cred.py` (~:167–168). Product `.py`
  → **Red-Green-Replay** (stage ONE test file at Red; the other + impl + comment
  at Green).
- **Accept:** a real Codex-provider golden-master dispatch (needs PR-C's
  provider switch, OR a manual `fabro run --input acp_adapter=…` against the
  current image) confirming the adapter launches from the baked global and the
  run is green incl. credential projection. Independent value: the adapter
  launch becomes network-free even before the automation exists.

### PR-B (`livespec-dev-tooling`) — the freshness scan + bump PR for `CODEX_ACP_VERSION`
- New autodiscovery **pin format** for the `CODEX_ACP_VERSION` Dockerfile ARG,
  external source `zed-industries/codex-acp` (query latest via `gh release view`
  / `npm view`). Wire it into `pin_autodiscovery` + the rewrite in the
  `bump-pin-rewrite` composite action (mirrors the existing per-format arms;
  reuse the tested-module pattern from `fabro_image_pin_rewrite`).
- Extend `reusable-pin-freshness.yml` (or a dedicated weekly cron shim) to scan
  it and open the bump PR. The existing image workflow
  (`fabro-sandbox-image.yml`) already builds a candidate image (`…-sha-<short>`)
  on the PR — nothing new needed there.
- The bump PR's **required status** is the Codex-mode golden-master result from
  PR-C (cross-repo). Wire the dispatch trigger (existing `repository_dispatch`
  fan-out) + branch-protection required-check.

### PR-C (`livespec-orchestrator-beads-fabro`) — Codex-mode golden-master gate
- Add a `--provider codex` (or `--input acp_adapter=<codex>`) path to
  `acceptance-live-golden-master.sh` so the dispatch runs the Codex implementer
  adapter (Codex creds are already provisioned via `require_codex_auth_file` /
  `provision_codex_auth`).
- Add a **candidate-image override** so the *sandbox* image is the candidate
  `…:python-sha-<short>` instead of the released `workflow.toml` pin. **VERIFY
  FIRST** whether the Dispatcher's per-dispatch overlay
  (`_dispatcher_plan.py render_run_config_overlay` /
  `_dispatcher_overlay.py`) can override `[environments.livespec-ci.image]
  docker`. If not, fallback: a test-only workflow.toml or an env the overlay
  honors.
- Wire it as a repository_dispatch handler that runs the gate and posts a commit
  status back to the dev-tooling bump PR's head sha.

## Hard constraints (carry into every dispatch brief)

- **No-Circular-Dependency** (`.ai/no-circular-dependency.md`): the version
  lives in `livespec-dev-tooling`; the credential test is orchestrator-side. The
  gate is an **event dispatch + status callback**, NEVER a code read from
  dev-tooling into the orchestrator. The orchestrator's `--no-install`
  baked-global consumption is a consumer→producer read (cycle-free).
- **Credential-projection guarantee** (`bd-ib-ss7rkr`): the whole point of the
  gate is to re-verify `project_codex_auth_snapshot` on each bump. The
  Codex-mode golden-master MUST exercise it (a real Codex dispatch that
  authenticates from the host snapshot), not just any green run.
- All changes: worktree → PR → merge; product `.py` uses Red-Green-Replay;
  never `--no-verify`. The Codex-dispatch accept is credentialed/costly →
  surface to the maintainer before firing (as the golden-master run was).
- Fleet-secret discipline: the golden-master runs under the 1Password wrapper
  (`/usr/local/bin/with-livespec-env.sh -- …`); it self-provisions the op token
  via `sudo -n` + systemd-creds. Invoke the script directly (not `just`, which
  isn't on the wrapper's minimal PATH).

## Cross-references

- Design: `plan/codex-acp-auto-bump/design.md`.
- Parent epic: `livespec-3lev` (`fabro-ci-image-factoring`), Phase 1 `.4`
  (journaled there). Parent handoff:
  `plan/fabro-ci-image-factoring/handoff.md` (NEXT ACTION #1 points here).
- Credential-projection tracker: `bd-ib-ss7rkr`.
- Golden-master invocation reference (verified working 2026-07-13):
  `cd /data/projects/livespec-orchestrator-beads-fabro && /usr/local/bin/with-livespec-env.sh -- bash orchestrator-image/acceptance-live-golden-master.sh --run --build-image`
  (defaults to Claude today; PR-C adds the Codex switch).
