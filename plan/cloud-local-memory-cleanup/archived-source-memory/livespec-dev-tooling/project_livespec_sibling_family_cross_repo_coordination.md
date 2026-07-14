---
name: project-livespec-sibling-family-cross-repo-coordination
description: "The livespec sibling family (livespec, livespec-dev-tooling, livespec-runtime, livespec-impl-plaintext) carries cross-repo coordination automation per a multi-phase epic."
metadata: 
  node_type: memory
  type: project
  originSessionId: 48850880-6a8c-4e3b-a8e3-798911468efd
---

The livespec project is a 4-repo family sharing automation via a
cross-repo coordination surface owned by `livespec-dev-tooling`:

- `livespec` — the parent spec library
- `livespec-dev-tooling` — shared enforcement-suite library (now
  also the cross-repo coordination implementation owner)
- `livespec-runtime` — the runtime sub-library
- `livespec-impl-plaintext` — the canonical impl plugin

**Cross-repo coordination automation:** as of 2026-05-25, the family
ships three reusable workflows that implement pin-and-bump automation:

- `reusable-release-dispatch.yml` — fans out repository_dispatch on
  release publish
- `reusable-bump-pin-from-dispatch.yml` — handles incoming dispatch,
  rewrites pins, opens auto-merge PRs via a GitHub App
- `reusable-pin-freshness.yml` — daily cron safety-net for missed
  dispatches

All live under `livespec-dev-tooling/.github/workflows/`. Each
sibling repo (including dev-tooling itself, self-hosting) carries
3 thin shim workflows that delegate to the reusables.

**Sibling discovery:** uses the `livespec-sibling` GitHub topic on
every repo. Adding a new sibling requires only:
1. `gh api -X PUT /repos/<org>/<name>/topics -F "names[]=livespec-sibling"`
2. Drop the 3 shim workflows (templates at /tmp/drop-shims.sh in
   the prior session — pin pattern is `@<latest-tag>` after
   bootstrap, `@master` during bootstrap)
3. Install the livespec GitHub App on the new repo + propagate
   APP_ID + APP_PRIVATE_KEY secrets

**Why:** Why: a sibling release should trigger pin bumps across the family
automatically. Why: each repo's pins (4 formats supported:
.livespec.jsonc, pyproject.toml [tool.uv.sources], .vendor.jsonc,
.copier-answers.yml _commit) keep all consumers fresh against
their dependencies' latest releases.

**How to apply:** when working on any of the 4 repos, be aware that:
- A release in one repo triggers downstream PRs in the other 3.
- The `chore:` PR prefix convention is mandatory for bump-PRs (any
  other prefix triggers release-please cycles).
- The pin-freshness workflow is the auto-recovery path; manual pin
  edits are the v1 fallback for broken state.

**Epic status:** Phases 1-4 complete and merged as of 2026-05-25.
Phase 5 (App install + smoke test) is the blocking manual step.
See `/data/projects/livespec-dev-tooling/work-items.jsonl` epic
li-7z7gqj.

Related: [[feedback-revise-payload-format]],
[[feedback-livespec-commit-prefixes]],
[[feedback-heading-coverage-pairing]]
