# Epic: Worktree Discipline Pack for the livespec orchestrator (Python/Rust/JS first-class)

> Tracked in the openbrain beads tenant as **ob-0x5** (cross-repo: the
> implementation lands here in the livespec fleet). Dogfood / precedent:
> openbrain **ob-apw** (the JS/pnpm local adoption). This file is the
> durable design; `worktree-discipline-pack-prompt.md` is the runnable
> handoff.

## Goal

Bundle worktree discipline into the orchestrator (the copier impl-plugin
template + orchestrator skills + orchestrator spec) so EVERY consuming
repo gets it **by default** — easy to follow and enforced — WITHOUT a
human instructing each agent session.

## Why

A consuming repo (openbrain) had no worktree default, so agents committed
on the single shared primary checkout and collided: pushes blocked (the
pre-push gate needs a clean tree ON the default branch), an orphaned
release worktree that detached the primary HEAD, and a build-gate failure
on another track's mid-refactor uncommitted churn. The discipline only
happened when each session was told MANUALLY. livespec core has the
"Repository mutation protocol" in its own AGENTS.md, but as repo-local
prose — not distributed or enforced to consumers.

## Design: contract + portable core + per-ecosystem profiles

**Mandate the contract, never a tool.**

- **Contract (tool-agnostic):** every mutation happens in an isolated
  worktree; the primary checkout is never committed to; landing is via
  PR/merge; orphans are reaped; a commit-time gate enforces it.
- **Portable core:** dependency-light (POSIX shell or a small single
  binary) doing create / hydrate / land / reap + primary-vs-linked
  detection (`git rev-parse --git-common-dir` vs `--git-dir`).
  Config-driven; no ecosystem or task-runner assumptions.
- **Invocation = thin adapters onto the repo's OWN task runner.** Do NOT
  mandate `just`; it is ONE reference adapter. Emit aliases for the repo's
  runner (cargo/xtask, pnpm/npm scripts, just, make, mise, taskfile, raw).
- **Enforcement = portable "no commit on primary" check**, wired via the
  repo's hook framework (lefthook / husky / pre-commit / raw git hook) +
  a server-side tripwire mirror (hooks are bypassable).
- **Default path:** orchestrator `implement`/dispatcher auto-provision a
  worktree per work-item so the happy path is disciplined by construction.
- **Distribution:** ship in the copier impl-plugin template; `copier
  update` propagates to existing consumers; the drift workflow flags
  divergence. Spec it in orchestrator contracts.md / non-functional-requirements.md.

## Three first-class ecosystems (closed set): Python, Rust, JavaScript

A copier question `ecosystem = python | rust | javascript` selects a
profile of presets; EVERY key stays individually overridable.

| | Python | Rust | JavaScript/TS |
| - | - | - | - |
| Default runner | just/uv (or make/nox) | cargo (+ xtask/just) | pnpm/npm/yarn scripts |
| Hydrate cmd | `uv sync` (or poetry/pip) | `cargo fetch` + warm cache | `pnpm install` |
| Per-worktree dep state | `.venv/` (cache-cheap) | NONE in-tree (see below) | `node_modules/` incl. workspaces |
| Hooks default | lefthook / pre-commit | lefthook / raw | lefthook / husky |
| Verify gate | pytest + ruff + mypy | cargo build/test/clippy/fmt | build + lint + test |

"Hydrate" means something DIFFERENT per ecosystem; the core delegates it
to the profile:

- **JS** = populate `node_modules` (cheap via the pnpm store /
  rsync-of-symlinks); remember workspace sub-packages (openbrain's
  `dashboard/` sub-package was the gotcha that broke worktree builds).
- **Python** = create `.venv` (cheap via the uv cache).
- **Rust** = warm/share the BUILD cache. Crates already live in
  `$CARGO_HOME` (shared across all worktrees — `cargo fetch` is ~free), so
  there is NO per-project dep dir to copy. The real per-worktree cost is a
  cold `target/` full recompile, so the Rust profile MUST default to
  `sccache` (shared compilation cache across worktrees AND branches) or a
  shared `CARGO_TARGET_DIR`, so a Rust worktree is as cheap to spin up as a
  pnpm-store one. Do NOT model Rust as "JavaScript but with cargo."

## Config keys (copier questions)

`ecosystem`; `task_runner`; `hook_framework`; install/hydrate cmd;
`worktree_root` (default `~/.worktrees/<repo>/<branch>`); `land_mode`
(pr | merge-queue | direct); `uses_mise` (gates the auto-trust step).

## What stays identical across all three

The contract and the enforcement check are pure-git, ecosystem-neutral.
Only the profile presets (runner, hydrate, verify, hooks) vary. Adding a
4th ecosystem later = a new profile, no core/gate change.

## Rollout (dogfood -> promote)

1. Build the pieces in openbrain (ob-apw) — the JS/pnpm dogfood instance,
   template-shaped (runner-agnostic core + a lefthook gate + an AGENTS.md
   protocol section).
2. Extract/promote into `templates/impl-plugin/` as this pack; add the
   Python and Rust profiles.
3. Spec it (orchestrator contracts.md + non-functional-requirements.md).
4. `copier update` propagates to openbrain + other consumers; the drift
   workflow flags divergence.

## Acceptance

A freshly scaffolded OR copier-updated repo in Python, Rust, OR JavaScript
gets BY DEFAULT: worktree lifecycle via its own task runner; a gate that
blocks commits on the primary checkout; ecosystem-correct hydration
(including Rust's shared build cache); a reaper; PR/merge landing. No agent
needs manual instruction. `just` is not required by any repo.
