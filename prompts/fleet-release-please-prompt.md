# Prompt: wire release-please across the livespec fleet

You are executing the epic in `prompts/fleet-release-please-epic.md`
(tracked in the livespec beads tenant as **livespec-4v7v**, children
`livespec-4v7v.1`–`.5`). Read the epic first — it carries the verified
per-repo state and the three non-obvious traps.

Goal: finish the release-please rollout so the five unwired fleet
artifact repos auto-release on merge to `master` (version bump → tag →
App-authored GitHub Release → cross-repo fan-out), with no manual
tagging. Two repos already do this and are your copy source.

## Startup checks

1. Read `prompts/fleet-release-please-epic.md` in full.
2. Read the **reference wiring** in `livespec-dev-tooling`:
   `.github/workflows/release-please.yml`, `release-please-config.json`,
   `.release-please-manifest.json`, `CHANGELOG.md`. Also skim
   `livespec-runtime`'s copy. These are the templates.
3. Read `livespec/SPECIFICATION/contracts.md` §"Plugin versioning" (the
   mandated mechanism) and §"GitHub App auth model".
4. **Re-verify per-repo state before touching each repo** — the fleet is
   non-uniform; treat the epic's table as a hypothesis to confirm in each
   target repo (`git show origin/master:…` for `plugin.json` version,
   `.github/workflows/` contents, existing tags). Confirm the livespec
   GitHub App (`APP_ID`/`APP_PRIVATE_KEY`) is installed with
   contents+pull-requests+releases on each target repo before relying on
   it; if a repo's secrets are absent, surface it rather than falling back
   to `GITHUB_TOKEN`.
5. **Dogfood:** do each repo's change in a worktree under
   `~/.worktrees/<repo>/<branch>` and land via PR → rebase-merge — never
   commit on a primary checkout. Use `mise exec -- git …`; never
   `--no-verify`; halt and report on any hook failure.

## What to do (per repo; core FIRST)

For each target repo, add the four release-please files adapted from the
reference, with the three traps handled:

1. `release-please.yml` — `on: push: branches:[master]` + `workflow_dispatch`;
   `permissions: contents:write, pull-requests:write`; mint an App
   installation token via `actions/create-github-app-token@v1`
   (`APP_ID`/`APP_PRIVATE_KEY`) and pass it to
   `googleapis/release-please-action@v4`. **Never `GITHUB_TOKEN`** — a
   `github-actions[bot]` Release does not fire `release: published`, which
   kills the entire fan-out.
2. `release-please-config.json` — bump the **plugin manifest**, not
   pyproject: an `extra-files` JSON updater on `.claude-plugin/plugin.json`
   `$.version` (driver-codex: `livespec/.codex-plugin/plugin.json`).
   Mirror the reference's `changelog-sections`.
3. `.release-please-manifest.json` — seed at the current
   `plugin.json` version (**`0.1.0`** for all five; maintainer-approved
   0.x lineage).
4. `CHANGELOG.md` — empty seed; release-please maintains it.

Per-repo extras (see the epic for detail):

- **core** (`.1`) — FIRST. Seed `0.1.0`; **delete the stray `v1.0.0` tag**
  on origin and locally (maintainer-approved) so `v0.x` tags don't sort
  beneath it. Doing core first validates the pattern AND ships the merged
  `livespec-kfjd` fix to siblings.
- **driver-claude** (`.2`) and **driver-codex** (`.3`) — also add
  `auto-enable-merge.yml` (App-authored, copied from a repo that has it);
  without it the release PR never merges. driver-codex's version file is
  `livespec/.codex-plugin/plugin.json`.
- **orchestrator-beads-fabro** (`.4`) — standard.
- **orchestrator-git-jsonl** (`.5`) — already has `v0.1.0`; seed manifest
  `0.1.0`.

After core's first release PR merges, **confirm end-to-end**: a `vX.Y.Z`
tag + an App-authored GitHub Release exist, `release-dispatch` fired, and
sibling pin-bump PRs opened. Only then proceed to the other four (they can
run in parallel).

For each non-core repo, check whether its own spec states the
release-please contract; if not, file a `propose-change` in that repo so
the mechanism is documented, not just wired.

## Constraints / non-negotiables

- App-token auth everywhere; never `GITHUB_TOKEN`.
- Bump `plugin.json` (`$.version`), not `pyproject` — these are plugins.
- Seed every manifest at `0.1.0`; do not jump to 1.x.
- Do NOT touch `livespec-dev-tooling` or `livespec-runtime` (already
  wired). Do NOT wire `livespec-console-beads-fabro` (leaf consumer) —
  confirm and record the exclusion.
- Each repo verified green on its own `just check` + `/livespec:doctor`
  before its child item closes.
- Dogfood: worktree + PR per repo; never the primary checkout.

## Close criteria

All five repos auto-release end-to-end (push → release PR → merge → tag +
App Release → fan-out → sibling pin PRs), verified on core so
`livespec-kfjd` reaches siblings/CI. Driver repos carry
`auto-enable-merge.yml`. Close `livespec-4v7v.1`–`.5` as each lands, close
the epic `livespec-4v7v` when all five are done, and archive this prompt
pair.
