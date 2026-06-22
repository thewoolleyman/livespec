# Agent instructions

This file is the canonical agent-orientation surface for this repo;
`.claude/CLAUDE.md` is a symlink to it — never maintain a separate copy.
The sections through "Red-Green-Replay commit protocol" are the livespec
family-universal agent-instruction core (shared by every family member via
the impl-plugin template); repo-specific guidance is additive on top.

## Repository mutation protocol

Every repo change uses a worktree → PR → merge → cleanup path. Treat leaving
dirty state, committing on the primary checkout, or asking the user whether to
commit as failures of the workflow, not as acceptable stopping points.

1. Confirm the primary checkout before editing:

   ```bash
   git config --get livespec.primaryPath
   git status --short --branch
   ```

2. If the change will modify tracked files, create a dedicated worktree from the
   primary checkout's `master` and do all edits there:

   ```bash
   mise exec -- git worktree add -b <branch> <worktree-path> master
   ```

3. Use `mise exec -- git commit ...` and `mise exec -- git push ...` so the
   mise-managed lefthook hooks actually run. Never pass `--no-verify`; if a hook
   fails, fix the cause or halt with the failure.
4. Open a PR, wait for required checks, and merge through the PR using the repo's
   rebase-merge discipline.
5. After merge, refresh the primary checkout to `origin/master`, remove the
   feature worktree, delete the local branch, and verify the primary checkout is
   clean on `master`.

Do not leave orphaned worktrees. If a session must stop before cleanup, record
the active worktree path, branch, PR, validation state, and next action in the
relevant handoff document.

## Agent prerequisites for plugin work

When investigating or changing anything related to the Claude Code plugin
installation, marketplace, or distribution, establish execution context FIRST —
do not assume how the system works:

1. Run `claude plugin marketplace list` to see which marketplaces are configured
   and whether they point to local files or remote repos. Changes to a local
   `marketplace.json` do NOT affect installs from a remote GitHub marketplace.
2. Trace where the actual install command fetches from (local vs remote) before
   changing anything, and verify your change affects that code path.
3. For remote marketplaces, push to GitHub then test; for local, use
   `/plugin marketplace add ./.claude-plugin/marketplace.json`. Never test local
   changes against a remote marketplace and assume they apply.

## Beads runtime prerequisites

This plugin's work-item store is a per-repo beads/Dolt TENANT on the shared
family dolt-server — NOT JSONL files. Installing the plugin does NOT provision
the backend; a clone connects to its tenant only when ALL of the following are
present:

- **`bd` CLI, pinned**, at an absolute path (NEVER the mise shim), with
  `LIVESPEC_BD_PATH` pointing at it.
- **A running Dolt `sql-server`** reachable over **TCP `127.0.0.1:3307`**. Family
  tenants force TCP (not the unix socket); `.beads/config.yaml` carries `dolt.*`
  host/port keys with NO `socket` key.
- **The shared family password** in env as a single **bare
  `BEADS_DOLT_PASSWORD`** — all livespec-family beads tenants share ONE Dolt
  password, injected by the family 1Password Environment wrapper
  `with-livespec-env.sh` (canonical copy at
  `/data/projects/1password-env-wrapper/with-livespec-env.sh`). There is NO
  per-tenant `BEADS_DOLT_PASSWORD_<tenant>` variable and NO per-tenant→bare
  mapping — the wrapper exports the one bare var directly. Real isolation comes
  from the per-tenant SQL user + DB-scoped grant, not from password distinctness.
  Secrets are probe-only — `printenv NAME | wc -c`, never echo values — and NEVER
  committed to `.livespec.jsonc` or `.beads/`.
- **The `.beads/` pointer files**: `config.yaml` (committed; the `dolt.*` server
  keys) and `metadata.json` (gitignored, regenerable). NEVER run `bd init` inside
  a primary checkout or worktree — it auto-commits and clobbers `.beads/`.

**Run beads commands from the target repo root.** Per-command `bd` resolves its
connection from the current directory's `.beads/config.yaml` (auto-discovery),
NOT from any resolved config object — so run from the intended repo's root, or
`bd` silently operates on the wrong tenant.

**An "Access denied" / "no beads database found" failure almost always means you
are running OUTSIDE the wrapper** (the bare `BEADS_DOLT_PASSWORD` is absent), not
that a secret is missing. Re-run under `with-livespec-env.sh -- <command>`. Never
hand-hunt the secret or reach around the seam with raw `mysql` / `dolt` / `sudo`.

## Daily commands

- `just bootstrap` — first-touch setup on a fresh clone; idempotently sets
  `livespec.primaryPath`, installs the canonical commit-refuse hook at
  `.git/hooks/pre-commit` + `.git/hooks/pre-push`, installs lefthook hooks, and
  resolves plugin dependencies.
- `just check` — the full enforcement aggregate (lint, types, tests, coverage,
  AST checks). It is the load-bearing safety net; it runs locally, in pre-push,
  and in CI.

## Revise co-edit discipline — `tests/heading-coverage.json`

Every revise pass that adds, changes, or removes a `## ` heading in any spec file
MUST update `tests/heading-coverage.json` in the same change (via the revise
`resulting_files[]` mechanism) so the heading-coverage map stays in lockstep with
the spec. Diff the proposed `## ` heading set against the current spec file's H2
set; add an entry (`test` MAY be the literal `"TODO"` with a non-empty `reason`)
for each new heading, and drop entries for removed headings.

## Red-Green-Replay commit protocol

Product `.py` changes are committed via a 2-step single-commit TDD ritual,
enforced by the `red_green_replay` commit-refuse hook (it inspects the staged
tree and writes `TDD-*` trailers). The final result is ONE commit carrying the
test, the impl, and both trailer sets.

1. **Red commit.** Stage the test file ALONE — no impl — and commit with a
   `fix:`/`feat:` subject. The hook runs pytest on the staged tree; the staged
   test MUST fail on pytest (non-zero exit). An `ImportError` or a collection
   error counts as a failure to the hook, BUT you SHOULD prefer a genuine
   assertion failure so Red proves the behavior is actually unimplemented
   rather than merely unimportable — see the new-module stub technique below.
   It records `TDD-Red-*` trailers (test path, failure reason, test-file
   checksum, output checksum, captured-at).
   - Gotcha: the impl must be UNMODIFIED on disk at the Red commit, because the
     hook's pytest reads the on-disk module. If the impl already carries the
     change the test passes, and the hook rejects with `test-passed-at-red`.
2. **Green amend.** Stage the impl and run `git commit --amend`. The hook sees
   the `TDD-Red-*` trailers + the staged impl, re-runs the SAME test (now
   passing), and records `TDD-Green-*` trailers. The test file bytes MUST be
   byte-identical across the Red→Green pair; to change the test, author a fresh
   Red commit.

### New-module stub technique (avoiding false reds)

When the impl module under test does NOT exist yet, the natural Red would be an
`ImportError` or a collection error rather than an assertion failure. The hook
accepts that as a failing Red, but it does not prove the behavior is
unimplemented — only that the module is unimportable. To make Red fail on a
genuine assertion instead:

1. At Red time, create the impl module as a minimal **stub** on disk — enough
   that the test imports and runs, but its assertion FAILS (e.g. a function
   that returns a wrong/sentinel value, or raises `NotImplementedError` only
   when that still yields an assertion failure rather than a collection error).
2. The stub must NOT make the test pass — a passing test at Red trips the
   hook's `test-passed-at-red` gate.
3. Then the **Green amend** replaces the stub with the real implementation that
   makes the assertion pass.

This keeps Red honest: it proves the behavior is unimplemented, not merely that
the module is missing.

**Exempt:** changesets with no product `.py` (docs, spec, work-items, shell,
config) use `chore(...)` / `docs(...)` / `chore(spec):` subjects and skip the
ritual entirely. Always use `mise exec -- git ...` so the hooks fire; never
pass `--no-verify`.
