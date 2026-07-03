# Fleet audit (Phase 2)

**Plain-language summary.** This document inventories, per governed repo, which
livespec-ecosystem plugin build is actually active and whether anything keeps it
current. The headline: only 4 of the 10 governed repos run the SessionStart
`just ensure-plugins` updater at all, and even those carry the one-session lag
from Phase 1. The reported console failure
(`livespec-console-beads-fabro`) has NO updater hook, so its orchestrator
pointer never moved off the stale `06e3e080` build that lacks the credential
self-heal. Separately, all four plugin repos' release pipelines are stalled —
each has an open, unmerged release PR authored by the `livespec-pr-bot` GitHub
App that the auto-merge workflow refuses to merge — so "latest release" is not
even a currency floor right now. One stale repo (openbrain, an adopter) is stale
by intent (`posture: "pinned"`), which must be respected. The matrix and
per-cell staleness call-outs follow.

## Q1 — per-repo release gap (why each "latest release" lags master)

Root cause is IDENTICAL across all four plugin repos: release-please opens a
green release PR authored by the GitHub App `livespec-pr-bot`; the
`auto-enable-merge` workflow only auto-merges PRs authored by `thewoolleyman`,
so release PRs are SKIPPED and sit open until a human merges. That manual merge
lapsed after ~Jun 30/Jul 1. Not a commit-type seam; not a failed workflow
(Release Please + CI both green on master and on the release PRs).

| Repo | Latest release (date) | master HEAD | commits ahead | Open release PR (unmerged) | Notable unreleased feat/fix |
|---|---|---|---|---|---|
| livespec (core) | v0.5.0 (Jun 29) | db76cf3 | 78 | #733 → 0.6.0 (open since Jul 1) | feat credential_wrapper, feat warn-vs-fail lever, feat github-auth guard, fix propose-change target |
| livespec-orchestrator-beads-fabro | v0.4.0 (Jun 30) = 06e3e080 | 19548b4c2f7c | 29 | #228 → 0.5.0 (open since Jul 1) | **feat 860f671 self-heal**, feat github-app auth, fix status-conformance gate, fix lifecycle invariant |
| livespec-driver-claude | v0.2.0 (Jun 24) | f6c988ec | 32 | #58 → 0.2.1 (open since Jun 27) | fix plugin-structure recipe, refactor consume dev-tooling pkg, ci red-green-replay |
| livespec-driver-codex | v0.2.0 (Jun 25) | e489f448 | 33 | #25 → 0.3.0 (open since Jun 26) | feat Codex auto-memory guard, fix plugin-structure recipe |

Historical release PRs (orch #226, core #633/#588) show `author=app/livespec-pr-bot`,
`mergedBy=thewoolleyman` — confirming releases only ever cut on manual merge.

## Q4 — full fleet × plugin × surface matrix

Governed repos (`.livespec.jsonc` + committed `.claude/settings.json`
enabledPlugins). Every one enables the same trio: `livespec@livespec`,
`livespec@livespec-driver-claude`, `livespec-orchestrator-beads-fabro@…`
(openbrain adds `livespec-impl-plaintext`). All enablement is project-scope via
committed settings.json.

| Repo | SessionStart hook | Active orch snapshot (lastUpdated) | Self-heal in it? | vs marketplace master (19548) |
|---|---|---|---|---|
| livespec (core) | `just ensure-plugins` ✓ | 19548b4c2f7c (Jul 3) | YES | CURRENT |
| livespec-orchestrator-beads-fabro | `just ensure-plugins` ✓ | 06e3e080ae19 (Jun 30) | **NO** | STALE (no session since Jun 30) |
| livespec-orchestrator-git-jsonl | `just ensure-plugins` ✓ | 0.4.0/0bc818d0 (Jun 29)* | — | STALE |
| dolt-server | `just ensure-plugins` ✓ | (not project-installed yet) | — | — |
| livespec-console-beads-fabro | **none** ✗ | **06e3e080ae19 (Jun 30)** | **NO** | **STALE — THE FAILURE** |
| livespec-dev-tooling | none ✗ | (not project-installed) | — | — |
| livespec-driver-claude | none ✗ | (not project-installed) | — | — |
| livespec-driver-codex | none ✗ | (not project-installed) | — | — |
| livespec-runtime | none ✗ | (not project-installed) | — | — |
| openbrain (adopter) | `check-ci-status.sh` (NOT ensure-plugins) ✗ | 0.1.0/accbbd14 (Jun 24) | NO | STALE — but posture:"pinned" (intentional) |

\* git-jsonl's active `livespec-orchestrator-beads-fabro` entry is absent from
installed_plugins.json; it installs its own `livespec-orchestrator-git-jsonl`
plugin at 0.2.0/05ad53a4 instead (different impl plugin).

Core-plugin (`livespec@livespec`) active pointers, for reference:
- livespec → db76cf3 (Jul 3, = master HEAD, CURRENT)
- console → 0.1.0/409c3551 (Jun 24, STALE, never updated)
- openbrain → 0.2.0/aa08a330 (Jun 24, pinned)
- git-jsonl → 0.4.0/0bc818d0 (Jun 29)
- orchestrator-beads-fabro → 0.4.0/0bc818d0 (Jun 29)

driver-claude active pointers: livespec→f6c988ec (Jul 1); console→0.1.0/9207bb73
(Jun 24); openbrain→0.1.0/f4aac6e3; git-jsonl & beads-fabro→0.2.0/663d4103.

### Surface coverage

| Surface | Updater? | Gate? | Staleness class |
|---|---|---|---|
| Interactive Claude (per repo) | ensure-plugins hook in only 4/10 repos; one-session lag even where present | none | active-snapshot pointer (H1+H5) — the console failure |
| Fabro sandbox | N/A — fresh clone + pinned docker image `sha-ea684ad` + uv pins | dispatch-time conformance verifiers (not plugin currency) | docker-image pin drift + repo dep pins (NOT plugin snapshots) |
| Codex (`codex exec`) | none (host-wide `~/.codex/config.toml`, no hook analogue) | none | host-wide snapshot; currently 0.4.0 w/ self-heal by coincidence |

### Staleness call-outs (every stale cell)

- **livespec-console-beads-fabro** — orchestrator pointer 06e3e080 (no self-heal);
  NO SessionStart hook → never self-updates → the reported `/next` failure.
- **livespec-orchestrator-beads-fabro (self)** — orchestrator pointer 06e3e080
  (no self-heal) despite HAVING the hook: no session started there since Jun 30,
  so H1 lag + infrequent sessions leave it stale.
- **openbrain** — stale but INTENTIONAL (`posture: "pinned"`); different hook.
- **driver-claude/codex/dev-tooling/runtime** — no updater hook; they don't
  project-install the plugins (source repos), so lower exposure. See
  "Hypotheses — not established" for the projected resolution behavior of a
  `/livespec:*` invocation in one of these repos.
- **All four release pipelines** — stalled (open unmerged App-bot release PRs);
  "latest release" is not even a currency FLOOR right now.

## Hypotheses — not established

- **Source-repo `/livespec:*` resolution is projected, not observed.** The
  `driver-claude`, `driver-codex`, `dev-tooling`, and `runtime` repos do not
  project-install the livespec-ecosystem plugins, so no active snapshot was
  captured for them. The claim that a `/livespec:*` invocation there would
  resolve "whatever user/global path exists" follows from the Phase 1 registry
  model (`semantics.md` §1/§3), but was not directly exercised in these repos.
