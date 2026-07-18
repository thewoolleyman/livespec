# Plan — rename `claude-collector` → `otel-collector` (host OTel collector)

**Status:** VPS side DONE and live-confirmed (2026-07-18); macOS migration
PENDING on the Mac — the ONLY remaining item. Maintainer-approved 2026-07-11
as a separate, self-contained task (split out of
`plan/fabro-ci-image-factoring/`). **Owning session:** livespec core,
2026-07-11; live-marker confirmation 2026-07-18.

**Settled decisions (2026-07-11):** name = `otel-collector`; cross-platform
= runs on Linux or macOS (docs + code updated); marker migration = hard cut
(`collector.claude-collector` → `collector.otel-collector`, version bumped
0.4 → 0.5); GitHub repo renamed too (`thewoolleyman/otel-collector`,
`upstream` jessitron left intact).

**What LANDED (VPS, 2026-07-11):**
- `thewoolleyman/otel-collector` (formerly `claude-collector`) PRs #1
  (repo/docs rename + cross-platform) and #2 (macOS launchd label +
  migration runbook + `AGENTS.md`), both merged.
- GitHub repo renamed → `otel-collector`; local dir renamed
  `/data/projects/claude-collector` → `/data/projects/otel-collector`;
  live systemd unit swapped `claude-collector.service` →
  `otel-collector.service` (verified active, config loaded, 4317 up).
- Honeycomb: inventory found ZERO board/trigger dependency on the old
  marker, so no dashboard migration was needed.

**Live-marker confirmation — DONE (2026-07-18, from the livespec-core
session on the Linux VPS via the Honeycomb MCP):**
- `otel-collector.service` verified `active (running)` — 4-day uptime,
  config loaded from `/data/projects/otel-collector/config.yaml`, port 4317
  up. The gRPC log lines about `api.honeycomb.io:443` ("operation was
  canceled" / "handshake failed") are the normal multi-subchannel-cancel
  churn, NOT export failures — data lands (see counts below).
- New marker flowing: over 24h the `agent-activity` env carries **314,601**
  events with `collector.otel-collector="washere"`, version **`0.8`**
  (bumped past the handoff's `0.5` by Phase P-host config work), continuous
  through now.
- Old marker fully gone: **0** events with `collector.claude-collector` over
  24h — the hard cut is complete; nothing still stamps the old marker.
- Host-metrics also marked: the `livespec-host-metrics` dataset (Phase
  P-host `hostmetrics`+`docker_stats`) carries `collector.otel-collector=
  "washere"` v`0.8` too (7,604 events/1h) — closes verify-step 9. (Honeycomb
  classifies that dataset as `events`-kind, a P-host ingestion detail, not a
  rename-thread concern.)
- Cross-repo straggler sweep clean: the only surviving `claude-collector`
  strings in this repo are legitimate "renamed from `claude-collector`"
  historical mentions (this handoff, `plan/fabro-ci-image-factoring/
  handoff.md`) and frozen archive transcripts — no stale path references.

**What's PENDING (the only remaining item):**
- **macOS migration** — run on the Mac via the collector repo's `AGENTS.md`
  first-line reminder → `plan/rename-to-otel-collector-macos-migration.md`
  (unload old-label LaunchAgent, install new, smoke-test, then delete the
  reminder + archive that plan). Cannot be driven from the Linux VPS.

The remainder of this document is the ORIGINAL task spec (kept for the
migration-checklist detail); the decisions above are now settled.

## Bottom line

The host runs a single `otelcol-contrib` process out of the
`claude-collector` repo (`/data/projects/claude-collector`, systemd unit
`claude-collector.service`). Despite the name, it is functionally the
**host's shared OTel collector**: it carries all three signal pipelines
(traces, metrics, logs) and exports to Honeycomb. The only genuinely
Claude-specific piece is ONE processor, `transform/agent_timeline`, which
rewrites `claude_code.*` spans into Honeycomb's Agent-Timeline shape (and
runs on the traces pipeline only). Everything else — the OTLP receiver,
the Honeycomb exporter, the batch processor, the metrics/logs pipelines —
is generic.

Two forces make the name actively misleading:
1. **`plan/fabro-ci-image-factoring/` (Phase P-host)** bolts `hostmetrics`
   + `docker_stats` (host CPU/mem/disk + per-container stats) onto this
   collector. Nobody would guess host resource metrics live in a repo
   named "claude-collector".
2. **Dual-runtime fleet.** When the separate
   `livespec-orchestrator-beads-fabro/plan/codex-factory-telemetry/`
   thread teaches Codex to emit telemetry, a Codex shaper lands in this
   SAME collector. The clean end-state is one neutral host collector
   hosting (a) a Claude Agent-Timeline shaper, (b) later a Codex shaper,
   (c) host/factory/CI resource metrics.

So: rename the collector to a neutral name. This does NOT remove the
Claude Agent-Timeline processor — that stays (still valid for Claude Code
sessions); only the container gets an accurate name.

## Why this is a separate task (not folded into fabro-ci-image-factoring)

- It touches a **live systemd unit** (a host mutation needing explicit
  maintainer go-ahead + sudo) and a **Honeycomb marker attribute** that
  saved queries/boards/triggers filter on — a real migration, not a
  rename-in-place.
- It is **not required** to "handle Codex" in the CI-image plan (that is
  covered there by naming Codex explicitly + the adapter-version
  lockstep) and it **does not block Phase P-host** (P-host targets the
  current path until this lands).

## Open decisions (recommend + pick before executing)

1. **The neutral name.** Recommended: `host-otel-collector` (says what it
   is: the host's OTel collector). Alternatives: `otel-collector` (terser
   but generic), `livespec-collector` (ties it to the fleet, though it
   also carries non-livespec Claude Code sessions). The marker attribute
   becomes `collector.<newname>`.
2. **Rename the GitHub repo too, or only the local dir + unit?** This repo
   is an adaptation of jessitron's upstream `claude-collector` (its
   `CLAUDE.md` is upstream text). Check `git -C /data/projects/claude-collector
   remote -v` first: if the remote is the maintainer's own repo, renaming
   the GitHub repo is clean; if it still points at an upstream fork,
   decide whether to rename only locally (dir + systemd unit + marker) and
   leave the remote. Recommended: verify the remote, then rename to a
   maintainer-owned repo of the new name.
3. **Marker-attribute migration strategy.** Recommended: hard cut
   (`collector.claude-collector` → `collector.<newname>`, bump version)
   AFTER inventorying Honeycomb boards/triggers that filter on the old
   marker and updating them. Alternative: dual-stamp both markers for a
   transition window (belt-and-suspenders; more config). The maintainer's
   env (`thewoolleyweb` team, `livespec` env) is low-surface, so a hard
   cut is likely fine — but inventory first.

## Migration checklist

**Host mutation — items marked ⚠ need explicit maintainer authorization +
sudo; do NOT run them unprompted.**

1. **Decide** the name + GitHub-rename scope + marker strategy (above).
2. **Inventory** Honeycomb (`thewoolleyweb` / `livespec` env) for any
   board, saved query, trigger, or SLO filtering on
   `collector.claude-collector` (= "washere") or the
   `collector.claude-collector.version` column. List them; they are the
   post-cut edit set.
3. **Repo/dir rename.** `mv /data/projects/claude-collector
   /data/projects/<newname>` (the `/home/ubuntu/workspace` and
   `/home/ubuntu/projects` symlinks are single top-level symlinks to
   `/data/projects`, so no per-repo symlink work). If renaming the GitHub
   repo: rename it on GitHub, then `git remote set-url` in the clone.
4. **config.yaml.** Rename the marker attribute in `transform/mark` for
   ALL THREE pipelines (`collector.claude-collector` →
   `collector.<newname>`, and the `.version` key), bump the version
   value, and update the file's own comments. (Per the repo's convention,
   bump `collector.<name>.version` on every config change.)
5. ⚠ **systemd unit.** Rename `/etc/systemd/system/claude-collector.service`
   → `<newname>.service`; update its `Description`, `ExecStart`
   `--config=` path (points at the renamed dir), and any `WorkingDirectory`.
   Then `systemctl daemon-reload`, `systemctl disable --now
   claude-collector`, `systemctl enable --now <newname>`. Confirm the new
   unit is `active (running)` and telemetry still flows.
6. **In-repo text.** Update `CLAUDE.md`, `README.md`,
   `docker-compose.yaml` (service/container name), `run`,
   `claude-env.sh`, `.env.example`, and `notes/` to the new name.
   (`.env` is gitignored — check it references nothing name-bound.)
7. **Cross-repo references.** `grep -rl claude-collector` across the fleet
   and update stragglers — at minimum
   `livespec/plan/fabro-ci-image-factoring/handoff.md` (Phase P-host cites
   `/data/projects/claude-collector/config.yaml`); confirm the
   `codex-factory-telemetry` plan's endpoint/receiver references are
   name-agnostic (they cite ports/files, not the repo name).
8. **Post-cut Honeycomb edits.** Update the boards/triggers/SLOs found in
   step 2 to the new marker attribute.
9. **Verify.** New unit running; a fresh Claude Code session's spans show
   `collector.<newname> = "washere"` with the bumped version; the
   host-metrics dataset (once Phase P-host lands) also carries the new
   marker.

## Rollback

Reversible at each step: restore the old `.service` unit +
`daemon-reload` + re-enable; `git mv` the dir back + `remote set-url`;
revert the config marker rename. The only lossy edge is Honeycomb
dashboards edited to the new marker — keep the step-2 inventory so they
can be reverted.

## Relationship to other threads

- **`plan/fabro-ci-image-factoring/`** (this repo) — the CI-image epic
  that surfaced this. Phase P-host adds the host/container-metrics
  receivers to this collector; it targets the current path and is NOT
  blocked by this rename.
- **`livespec-orchestrator-beads-fabro/plan/codex-factory-telemetry/`** —
  the thread that will add a Codex telemetry shaper to this same
  collector; the neutral name is the correct home for both runtime
  shapers.
