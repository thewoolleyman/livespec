# 003 — R8 live evidence: raw worktree push with no bootstrap after the pinned release (2026-09-06)

Plan `optimize-gates`, epic `livespec-xms725`, child `livespec-lnt6mf` (R8).
Companion to `002-…` (the proof taken before the dev-tooling release carrying
R1–R3 existed). This note is written FROM the worktree it describes.

## Setup

- livespec master pinned to livespec-dev-tooling `v1.52.3` (bump PR #2607,
  merged 2026-09-06T11:24:57Z), the release line carrying the six dev-tooling
  children (R1 proof, R2, R3, R5, R6, R7).
- Worktree created with a RAW `git worktree add` — not `just worktree-create`
  — so no pack was provisioned and no `just bootstrap` ran:

```bash
mise exec -- git -C /data/projects/livespec worktree add -b docs/optimize-gates-r8-live-evidence \
  "$HOME/.worktrees/livespec/docs/optimize-gates-r8-live-evidence" master
```

At creation `dev-tooling/` did not exist in the worktree.

## Commit (pre-commit hook transcript)

Commit `e809e6c1` (this note's first version), `mise exec -- git commit` from the
raw worktree, `dev-tooling/` empty beforehand:

```text
🥊 lefthook v1.13.6  hook: pre-commit
✔️ 00-install-worktree-pack (0.93 seconds)
✔️ 01-lint-autofix-staged (0.05 seconds)
✔️ 02-commit-pairs-source-and-test (0.69 seconds)
✔️ 03-check-pre-commit (6.34 seconds)
🥊 lefthook v1.13.6  hook: commit-msg
✔️ 00-no-commit-on-master (0.01 seconds)
```

After the commit `dev-tooling/` held the installed pack (17 entries).

## Push (pre-push gate transcript)

`mise exec -- git push -u origin docs/optimize-gates-r8-live-evidence` through the
detached gate runner, run `20260906T132617Z-1347361`, verdict PASSED, no
`just bootstrap` at any point:

```text
🥊 lefthook v1.13.6  hook: pre-push
  installed canonical worktree-pack file: worktree-lib.sh
  installed canonical worktree-pack file: branch-protection.sh
  installed canonical worktree-pack file: gate-run.sh
  installed canonical worktree-pack file: check-no-workflow-edits.sh
  installed canonical worktree-pack file: worktree.just
  installed canonical worktree-pack file: branch-protection.just
  installed canonical worktree-pack file: .gitignore
✔️ 00-install-worktree-pack (0.44 seconds)
✔️ 01-check-pre-push (218.22 seconds)
```

The `00-` command (re)installed all seven pack files before the aggregate read
them; the aggregate's `check-primary-checkout-commit-refuse-hook-installed`
pack arm then passed on the installed result. Compare `002-…`, where the same
shape was proven before the release: the difference here is that the
installer, verifier, and bootstrap row now walk the ONE enumeration
(`WORKTREE_PACK_FILES`, R2) and the central `worktree-pack-wired` row (R3)
asserts this wiring from the fleet vantage.

## Primary pack after `just worktree-create` (evidence 4)

On the primary `/data/projects/livespec` at pin `v1.52.3`, after this session's
`just worktree-create chore/dispatcher-prepare-toolchain` and the recipe's
own pack provisioning:

```bash
mise exec -- uv run python -m livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed
# verifier exit=0  (no BLOCKED; pack byte-identical)
```

## Absorbed items (evidence 5)

All eight closed with rationales naming the absorbing child or fix:
`livespec-qpk4` (absorbed by `livespec-ltthxr` + `livespec-dev-tooling-4wc3h4`);
`livespec-dev-tooling-ov9o`, `-5kcy`, `-1buh`, `-f7xs` (absorbed by the
optimize-gates dev-tooling children); `livespec-dev-tooling-zi4q`, `-3pre`,
`-sons` (fixed by `livespec-dev-tooling-2oip`).

## Fleet sweep (evidence 2 and 3)

_Recorded on the ledger item `livespec-lnt6mf` from the sweep runs of
2026-09-06; see that item's comments for the run ids and the
`worktree-pack-wired` row's per-member evaluation._
