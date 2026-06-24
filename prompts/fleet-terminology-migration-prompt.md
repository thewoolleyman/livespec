# Prompt: migrate livespec terminology from family to fleet

You are executing the epic in `prompts/fleet-terminology-migration-epic.md`.

Goal: migrate active livespec domain language from the legacy term `family` to
the product term `fleet` across the livespec fleet.

## Rules

Do not do a blind global replacement.

For each occurrence of `family`, inspect the surrounding text and classify it:

- If it means the livespec-governed collection of repos, shared automation,
  shared secrets, shared observability, shared hooks, shared templates, or a
  shared tenant, rewrite it to `fleet`.
- If it is generic English, rewrite it to a better non-domain word such as
  `group`, `category`, `class`, `set`, or a local phrase that preserves meaning.
- If it is in immutable history/archive, leave it alone and report it as an
  intentional exclusion.
- If it is ambiguous, read the relevant spec/code context and resolve it before
  editing.

Use these domain mappings unless context proves otherwise:

- `livespec family` -> `livespec fleet`
- `family repo` -> `fleet member`
- `family-wide` -> `fleet-wide`
- `family-scoped` -> `fleet-scoped`
- `family-standard` -> `fleet-standard`
- `family infrastructure` -> `fleet infrastructure`
- `family observability surface` -> `fleet observability surface`
- `family secrets` -> `fleet secrets`
- `family tenant` -> `fleet tenant`
- `non-family tenant` -> `non-fleet tenant`
- `family-universal agent-instruction core` -> `fleet-universal agent-instruction core`
- `family/dev-tooling coordination surface` -> `fleet/dev-tooling coordination surface`

Avoid bad mechanical phrases:

- `AST-shape fleet`
- `style fleet`
- `test-infrastructure fleet`
- `fleet of checks`
- `fleet of errors`

Use `category`, `group`, or `class` for those cases.

## Repos

Audit and migrate these repos:

- `/data/projects/livespec`
- `/data/projects/livespec-dev-tooling`
- `/data/projects/livespec-driver-claude`
- `/data/projects/livespec-driver-codex`
- `/data/projects/livespec-orchestrator-beads-fabro`
- `/data/projects/livespec-orchestrator-git-jsonl`
- `/data/projects/livespec-runtime`

## Process

For each repo:

1. Confirm the primary checkout and status.
2. Create a dedicated worktree from `master`.
3. Make scoped terminology edits.
4. Run an active terminology scan:

   ```bash
   rg -n '\bfamily\b' \
     --glob '!SPECIFICATION/history/**' \
     --glob '!archive/**' \
     --glob '!**/history/**' \
     --glob '!.git/**'
   ```

5. Run a bad-phrase scan:

   ```bash
   rg -n 'AST-shape fleet|style fleet|test-infrastructure fleet|fleet of checks|fleet of errors'
   ```

6. Run the repo's required checks. For product Python changes, follow the repo's
   Red-Green-Replay protocol.
7. Commit with `mise exec -- git commit ...`, push, open a PR, wait for checks,
   merge, refresh the primary checkout, remove the worktree, and delete the
   local branch.

## Verification

Before reporting done, run this cross-repo active scan:

```bash
rg -n '\bfamily\b' \
  --glob '!SPECIFICATION/history/**' \
  --glob '!archive/**' \
  --glob '!**/history/**' \
  --glob '!.git/**' \
  /data/projects/livespec \
  /data/projects/livespec-dev-tooling \
  /data/projects/livespec-driver-claude \
  /data/projects/livespec-driver-codex \
  /data/projects/livespec-orchestrator-beads-fabro \
  /data/projects/livespec-orchestrator-git-jsonl \
  /data/projects/livespec-runtime
```

Every result must be either fixed or explicitly reported as an intentional
historical/quoted exclusion. Also verify that `.livespec-fleet-manifest.jsonc`
still exists in `livespec` and that no active references to the old
`fleet-manifest.jsonc` filename were reintroduced.

## Final Report

Report:

- PRs merged by repo
- checks run by repo
- remaining excluded `family` occurrences, if any
- any wording choices where generic `family` became `group`, `category`,
  `class`, or `set`
- final cross-repo scan result
