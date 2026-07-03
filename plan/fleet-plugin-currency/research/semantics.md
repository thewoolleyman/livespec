# Resolution semantics (Phase 1)

**Plain-language summary.** This document establishes exactly how a
livespec-ecosystem plugin build gets selected when a session starts, and why the
console ran a stale one. When a Claude Code session begins, it resolves each
enabled plugin to one immutable on-disk snapshot via an "active-snapshot
pointer" in the registry; that pointer only moves when a scoped
install/update runs, and even then the *running* session keeps the build it
already resolved (the flip is honored only by the NEXT session — a built-in
one-session lag). The SessionStart updater hook that some repos run tracks the
marketplace's **master** branch, not the fleet's release tags. The load-bearing
surprise: the release pipeline is stalled fleet-wide, so "latest release" was
actually the BROKEN build lacking the credential self-heal, and only tracking
master delivered the fix. Of the seven candidate root causes, H1/H4/H5 are the
deepest confirmed drivers; H3 is refuted; H2/H6/H7 are partial or reframed. The
sections below give the mechanism for each.

Mechanism writeup for the fleet-plugin-currency thread. Evidence base:
`tmp/fleet-plugin-currency/evidence/` (Phase 0) + live GitHub/API probes +
Claude Code docs (code.claude.com/docs/en/plugins, /plugins-reference).

## 1. Active-snapshot pointer lifecycle (Claude Code)

- The registry is `~/.claude/plugins/installed_plugins.json` (`"version": 2`).
  Each plugin id maps to an ARRAY of entries, one per scope. Project-scope
  entries carry `scope:"project"` + `projectPath`; user entries `scope:"user"`;
  adopters can be `scope:"local"` (openbrain). The `installPath` field IS the
  active snapshot for that scope (`cache/<marketplace>/<plugin>/<id>/`).
- Snapshot id (`<id>` = the `version` field + dir name) is either a **semver**
  (`0.1.0`, `0.4.0`) or a **12-hex commit SHA** (`06e3e080ae19`, `19548b4c2f7c`).
  Empirically: older `claude plugin install` runs (Jun 24–29) produced
  semver-named active pointers; recent `claude plugin update` runs (Jun 30–Jul 3)
  produced SHA-named active pointers. Docs confirm the rule: a plugin.json with
  an explicit `version` is version-keyed for passive update-notifications, but an
  explicit `claude plugin update` force-fetches the marketplace's default-branch
  (master) HEAD and keys the snapshot by that commit SHA. `ensure-plugins` runs
  BOTH (`install` then `update`), so the update leg wins and pins the SHA.
- The pointer flips ONLY when a scoped install/update runs for THAT scope
  (`claude plugin install/update -s project <plugin>`). Nothing else moves it.
- **One-session lag (H1):** `claude plugin update` help + docs both read
  "restart required to apply." The flip is written to `installed_plugins.json`
  at update time, but the RUNNING session keeps its already-resolved snapshot;
  the new pointer is honored only by the NEXT session. So a SessionStart updater
  always leaves the current session one build behind the fetch.

## 2. Cache hygiene / GC (H7)

- `cache/<mp>/<plugin>/<id>/.in_use/` is a DIRECTORY of per-PID marker files
  (e.g. `06e3e080ae19/.in_use/117092`); a live session writes its PID there.
  `~/.claude/plugins/.last_inuse_sweep` records the last sweep (Jul 3 04:46).
  The sweep GCs snapshots with no live-PID marker; snapshots with a live PID
  or referenced by an active pointer are retained. It is conservative — 51
  orchestrator snapshot dirs remain on disk.
- **Manifest-version trap:** semver-named dirs are content-AMBIGUOUS. Because
  release-please bumps `plugin.json.version` only at the release commit, every
  post-release master commit still declares the SAME version (`0.4.0`). An
  `install` that resolves a post-release master commit lands in dir `0.4.0`,
  colliding with the release-tag `0.4.0` content — last-writer-wins. Evidence:
  the orchestrator has BOTH a `0.4.0` dir WITH self-heal (`selfheal=2`, a
  post-Jul-1 master build) AND a `06e3e080ae19` dir WITHOUT self-heal (the
  actual v0.4.0 release-tag commit). Only SHA-named dirs are content-stable.

## 3. Scope precedence (H3)

- Entries are per-scope; a project session resolves its `scope:"project"` +
  matching-`projectPath` entry. Standard precedence is most-specific-wins
  (project/local over user); `--plugin-dir` local copy overrides an installed
  same-named plugin for that session.
- Empirically MOOT here: NO livespec-ecosystem plugin has a user-scope entry —
  all `livespec@*` / `livespec-orchestrator-*` entries are project-scope; only
  ralph/codex/honeycomb/ntfy (non-livespec) are user-scope, openbrain-local is
  `local`. So no user/project shadowing is active. **H3 REFUTED.**

## 4. `ensure-plugins` mechanics (H4/H5)

`just ensure-plugins` (identical body in every repo that has it) runs, per
plugin: `marketplace add -s project` → `install -s project` → `update -s
project`. The marketplaces are github sources (`thewoolleyman/<repo>`), whose
"latest" is the DEFAULT BRANCH (master) HEAD — NOT the latest release tag.
So the currency mechanism tracks **master**, while the fleet's pin discipline
(`compat.pinned`, `bump-pin`, release-please) targets **release tags**. Those
two "latest" definitions disagree (**H4 CONFIRMED**), and — see Q1 — the release
side is badly stalled, so master is FAR ahead of the latest release.

## 5. Fabro sandbox resolution (H6, Fabro leg) — REFRAMED

The Fabro dark-factory sandbox does NOT resolve host plugins at all:
- Dispatcher (`.../commands/dispatcher.py`) runs `fabro run` from the target
  repo's primary checkout; Fabro clones the repo FRESH inside a docker sandbox
  (Architecture C, DinD). Sandbox image is a MANUAL pin
  `ghcr.io/thewoolleyman/livespec-fabro-sandbox:sha-ea684ad` (dev-tooling master
  build, 2026-06-12) baking mise/uv/just/lefthook/node-ACP/gh.
- Prepare steps (`workflow.toml`): `git fetch --unshallow`, `mise install`,
  `uv sync --all-groups`, `lefthook install`, install commit-refuse hook, set
  `livespec.sandboxExempt`, run two dev-tooling conformance verifiers. There is
  NO `claude plugin install`, NO `ensure-plugins`, NO `~/.claude/plugins` use.
- The phase graph (`workflow.fabro`) drives implement/fix/pr/review via a plain
  ACP Claude Code adapter; the only tooling gate is a script node
  `mise exec -- just check` (repo-local, uv-pinned `livespec_dev_tooling`). The
  implement.md prompt invokes no `/livespec:*` skill.
- Therefore the sandbox is NOT subject to the active-snapshot-pointer staleness
  class. Its currency is governed by (a) the manual docker-image pin
  `sha-ea684ad` (a floating master build that the v013 pin_autodiscovery
  formats do NOT cover, per workflow.toml's own note) and (b) the repo's
  committed `pyproject.toml`/`uv.lock` dependency pins. **H6 for Fabro:
  REFRAMED — different mechanism, different (still real) staleness surface.**

## 6. Codex surface (H6, Codex leg)

- `~/.codex/config.toml` enables `livespec@livespec`, `livespec@livespec-driver-codex`,
  `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`
  HOST-WIDE (no project scope, no SessionStart-hook analogue → no updater).
- Codex orchestrator cache: single snapshot `0.4.0`, which DOES carry the
  self-heal (`selfheal=2`, evidence 12) — so Codex currently happens to be
  fresher than the Claude console, but by coincidence, with no updater and no
  gate. **H6 for Codex: CONFIRMED unmanaged.**

## 7. Release-pipeline semantics (the load-bearing Q1 finding)

"Latest release" and "marketplace master" deliver DIFFERENT builds, and the
release side is stalled fleet-wide:
- release-please opens a green release PR on every master push (authored by the
  GitHub App `livespec-pr-bot`), but the `auto-enable-merge` workflow's gate is
  `contains(["thewoolleyman"], pull_request.user.login)`. The App bot is NOT in
  that allowlist, so `enable-auto-merge` is SKIPPED on every release PR. Release
  PRs therefore sit OPEN until a human merges them manually (historically
  `mergedBy=thewoolleyman`). That manual merge lapsed after ~Jun 30/Jul 1.
- Consequence: the self-heal fix (`860f671`, `feat:`, Jul 1) is in the OPEN,
  unmerged orchestrator release PR #228 (→ 0.5.0) and in NO release. The latest
  orchestrator RELEASE (v0.4.0 = `06e3e080`, Jun 30) PREDATES it. So a currency
  mechanism that tracked "latest release" would have delivered the BROKEN
  v0.4.0 to the console; only tracking MASTER (what `ensure-plugins` actually
  does) delivered the fix to the repos that ran it. This INVERTS the research
  plan's stated invariant ("latest RELEASED pin") and must be reconciled in
  Phase 4: fixing the release pipeline (auto-merge the App-bot release PR) is a
  PREREQUISITE for any release-tracking currency design.

## H1–H7 verdicts (established)

- **H1 (one-session lag) — CONFIRMED.** `claude plugin update` = "restart
  required to apply"; SessionStart updater applies only to the next session.
- **H2 (stale activation despite fetch) — PARTIAL / not the primary cause.**
  Newer content exists in cache, but the console never fetched it (no updater);
  the frozen pointer is caused by H5 + H1, not a broken activation flip.
- **H3 (scope shadowing) — REFUTED.** No livespec plugin has a user-scope entry.
- **H4 (master-vs-release mismatch) — CONFIRMED (deepest).** ensure-plugins
  tracks marketplace master; pin discipline targets release tags; release
  pipeline is stalled so master ≫ latest release, and the fix is master-only.
- **H5 (fleet non-uniformity) — CONFIRMED.** Only 4/10 governed repos run the
  SessionStart ensure-plugins hook; the console (the failure) is not one.
- **H6 (unmanaged surfaces) — CONFIRMED for Codex; REFRAMED for Fabro.** Fabro
  doesn't use host plugins (fresh clone + pinned image + uv pins); Codex is
  host-wide with no updater/gate.
- **H7 (cache hygiene) — PARTIAL/CONFIRMED.** `.in_use/<pid>` sweep exists but
  retains many snapshots; semver-named dirs are content-ambiguous
  (manifest-version trap); stale snapshots stay resolvable while pointed-to.

## Hypotheses — not established

All seven candidate root causes (H1–H7) resolved to the verdicts above. Two
residual claims rest on documented mechanism + Phase 0 evidence rather than a
controlled scratch-project reproduction, and are flagged here so they are not
read as directly-observed fact:

- **The manifest-version-trap collision was inferred, not reproduced.** The
  last-writer-wins collision between the release-tag `0.4.0` content and a
  post-release master `0.4.0` build is inferred from the observed coexistence of
  a `0.4.0` dir WITH self-heal and a SHA-named dir WITHOUT it (§2). A controlled
  scratch-project run forcing the collision was not performed; the mechanism is
  consistent with the evidence but not independently reproduced.
- **Source-repo `/livespec:*` resolution is projected, not observed.** The
  `driver-claude`, `driver-codex`, `dev-tooling`, and `runtime` repos do not
  project-install the livespec-ecosystem plugins, so what a `/livespec:*`
  invocation there would actually resolve (whatever user/global path exists) is
  a projection from the registry model in §1, not a captured observation.
