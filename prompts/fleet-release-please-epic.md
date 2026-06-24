# Epic: Wire release-please across the livespec fleet's unwired artifact repos

> Tracked in the livespec beads tenant as **livespec-4v7v** (children
> `livespec-4v7v.1`–`.5`, one per target repo). This file is the durable
> design; `fleet-release-please-prompt.md` is the runnable handoff.

## Goal

Make every livespec-fleet repo that ships a **versioned artifact other
repos pin to** auto-release on merge to `master` — version bump, tag,
GitHub Release, and cross-repo fan-out — with **no manual tagging**. Two
repos already do this; finish the other five.

## Why

The documented release mechanism (`livespec/SPECIFICATION/contracts.md`
§"Plugin versioning") is `release-please`: on every push to `master` it
opens a release PR carrying the next semver bump from the per-commit
Conventional Commits, and merging it tags `vX.Y.Z` + publishes a GitHub
Release. But release-please was only ever wired in **two** repos. In the
five artifact repos it was never added, so:

- `plugin.json.version` is frozen at `0.1.0`; nothing tags or publishes;
- the `release: published` event never fires, so `release-dispatch.yml`
  (and therefore `bump-pin-from-dispatch` → `pin-freshness`) never runs;
- **no master change has propagated to siblings/CI since the manual
  `v1.0.0` tag** (~657 commits), including the merged `livespec-kfjd` fix.

This is **not** a broken pipeline — it is an unfinished rollout. The hard
parts are already in place (below); only the release-please *actor* is
missing.

## What is already in place — DO NOT rebuild

- **Semantic-commit plumbing.** `master` is rebase-merge-only with linear
  history (`livespec/SPECIFICATION/non-functional-requirements.md` §838:
  `allow_squash_merge:false`, `allow_merge_commit:false`,
  `required_linear_history:true`), so every commit lands with its own
  Conventional Commits subject intact — exactly release-please's input. A
  separate subject *validator* is deliberately optional (NFR §842).
- **Downstream fan-out** — `release-dispatch.yml`, `bump-pin-from-dispatch.yml`,
  `pin-freshness.yml` — already present in every repo, waiting on
  `release: published`.
- **Two reference implementations to copy:** `livespec-dev-tooling`
  (`release-type: python`, releasing through `v0.16.0`) and
  `livespec-runtime` (`v0.4.0`). Each carries
  `.github/workflows/release-please.yml` + `release-please-config.json` +
  `.release-please-manifest.json` + `CHANGELOG.md`.

## Target repos (verified state, 2026-06-24)

| Repo | version SoT | auto-enable-merge.yml | existing tags |
| - | - | - | - |
| **livespec** (core) | `.claude-plugin/plugin.json` `$.version` (0.1.0) | present | stray `v1.0.0` |
| **livespec-driver-claude** | `.claude-plugin/plugin.json` (0.1.0) | **MISSING — add** | none |
| **livespec-driver-codex** | `livespec/.codex-plugin/plugin.json` | **MISSING — add** | none |
| **livespec-orchestrator-beads-fabro** | `.claude-plugin/plugin.json` (0.1.0) | present | none |
| **livespec-orchestrator-git-jsonl** | `.claude-plugin/plugin.json` (0.1.0) | present | `v0.1.0` |

Already wired (leave alone): `livespec-dev-tooling`, `livespec-runtime`.
Excluded: `livespec-console-beads-fabro` — leaf consumer (only `ci.yml`,
no `plugin.json`, no tags, nothing pins to it). Confirm before skipping.

## The wiring (copy-and-adapt from the references)

Per repo, add the four files modelled on `livespec-dev-tooling`:

1. `.github/workflows/release-please.yml` — `on: push: branches:[master]`
   + `workflow_dispatch`; `permissions: contents:write, pull-requests:write`.
2. `release-please-config.json` — drives the version bump.
3. `.release-please-manifest.json` — seeds the starting version.
4. `CHANGELOG.md` — auto-maintained.

Three non-obvious adaptations (each is a per-repo trap):

- **Bump `plugin.json`, not `pyproject`.** The references are libraries
  (`release-type: python` bumps `pyproject.toml`). These are plugins: the
  version source of truth is `.claude-plugin/plugin.json` `$.version`
  (driver-codex: `livespec/.codex-plugin/plugin.json`), and
  `marketplace.json` carries NO version (contracts.md §"Plugin
  versioning"). The config MUST bump that file via an `extra-files` JSON
  updater (`{"type":"json","path":"…/plugin.json","jsonpath":"$.version"}`).
- **App-token auth, never `GITHUB_TOKEN`.** release-please MUST mint a
  livespec GitHub App installation token (`APP_ID` / `APP_PRIVATE_KEY`,
  via `actions/create-github-app-token@v1`) and pass it to
  `googleapis/release-please-action@v4`. A Release authored by
  `github-actions[bot]` (the default token) does **not** fire
  `release: published`, so the entire cross-repo fan-out silently never
  triggers. (Documented in dev-tooling's `release-please.yml` header.)
- **auto-enable-merge for the two driver repos.** They lack
  `auto-enable-merge.yml`; without it the release PR opens but never
  merges, so nothing releases. Add it (App-authored), copied from a repo
  that already has it.

## Per-repo specifics

- **core** (`livespec-4v7v.1`): seed manifest at `0.1.0`; **void/delete the
  stray `v1.0.0` tag** (origin + local — maintainer-approved) so `v0.x`
  release tags don't sort beneath it. Wiring closes the existing
  contracts.md §"Plugin versioning" spec/impl gap (no spec change needed).
  Do this repo FIRST — it both validates the pattern end-to-end and ships
  the merged `livespec-kfjd` fix to siblings.
- **driver-claude** (`.2`): + add `auto-enable-merge.yml`.
- **driver-codex** (`.3`): manifest version lives at
  `livespec/.codex-plugin/plugin.json`; + add `auto-enable-merge.yml`.
- **orchestrator-beads-fabro** (`.4`): standard.
- **orchestrator-git-jsonl** (`.5`): already has `v0.1.0`; seed manifest at
  `0.1.0` so the next computed release sits above it.

For each non-core repo, confirm whether its own spec already states the
release-please contract (core's does); if not, file a `propose-change`
in that repo rather than leaving an undocumented mechanism.

## Acceptance

Each of the five repos: a push to `master` opens/updates a release PR;
merging it bumps `plugin.json`, tags `vX.Y.Z`, and publishes an
**App-authored** GitHub Release that fires `release: published`;
`release-dispatch` fans out `sibling-released`; each sibling's
`bump-pin-from-dispatch` opens an auto-merge pin PR. Verified end-to-end
on **core** so the merged `livespec-kfjd` fix actually reaches
siblings/CI. The two driver repos additionally carry `auto-enable-merge.yml`.
Every repo green on its own `just check` + `/livespec:doctor`. Children
`livespec-4v7v.1`–`.5` and the epic closed; this prompt pair archived.
