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

## Design: `just`+`lefthook` keystone + portable core + per-ecosystem profiles

**`just` and `lefthook` are the mandated keystone (non-functionally, fleet+adopter-wide).**

Per the zs22 locked decision and the Conformance Pattern
(`research/factory-conformance/cross-repo-conformance-pattern.md`), `just`
and `lefthook` are mandated NON-FUNCTIONALLY across ALL fleet + adopter
repos — but NEVER inside livespec core's public functional surface or the
`/livespec:*` skills. The Conformance Pattern makes them the mechanism:
Installer = a `just` recipe; Verifier = fail-closed in `just check`;
commit-time tier = `lefthook → just check`. The worktree pack realizes
that keystone:

- **Contract (tool-agnostic):** every mutation happens in an isolated
  worktree; the primary checkout is never committed to; landing is via
  PR/merge; orphans are reaped; a commit-time gate enforces it.
- **Portable core:** dependency-light (POSIX shell) doing create / hydrate
  / land / reap + primary-vs-linked detection (`git rev-parse
  --git-common-dir` vs `--git-dir`). Config-driven; no ecosystem
  assumptions. This portable core (`dev-tooling/worktree-lib.sh`) and the
  commit-refuse gate (`dev-tooling/refuse-primary-commit.sh`) carry the
  logic; they are pure-git so they stay correct under any runner.
- **Invocation = `just worktree-{create,hydrate,land,reap}` recipes** that
  call `dev-tooling/worktree-lib.sh` DIRECTLY. The worktree lifecycle is
  driven by `just`. Any ecosystem-native wrapper (cargo xtask, pnpm/npm
  scripts) is a STRICT PASS-THROUGH that literally invokes `just
  worktree-*` with NO logic of its own — never an alternative runner or
  framework. e.g. `cargo xtask worktree create` → `just worktree-create`;
  package.json `"wt:create": "just worktree-create"`.
- **Enforcement = the portable "no commit on primary" check, wired via
  `lefthook`** (the mandated commit-time framework) as the first pre-commit
  job AND the commit-msg backstop, with `lefthook → just check` as the
  commit-time tier + a server-side tripwire mirror (hooks are bypassable). The
  server-side mirror reuses the GitHub branch-protection PRIMITIVE — not a
  bespoke per-consumer detection workflow: `just protect-default-branch`
  establishes baseline protection (Installer) and `just check-branch-protection`
  is the fail-closed, capability-aware Verifier (the tripwire), both delegating
  to the portable `dev-tooling/branch-protection.sh`. The authoritative bite is
  the Fleet-time conformance/orchestrator tier, where an admin token exists.
- **Default path:** orchestrator `implement`/dispatcher auto-provision a
  worktree per work-item so the happy path is disciplined by construction.
- **Distribution:** ship in the copier impl-plugin template; `copier
  update` propagates to existing consumers; the drift workflow flags
  divergence. Spec it in orchestrator contracts.md / non-functional-requirements.md.
- **Core boundary:** `just`/`lefthook` are dev-tooling mechanism only —
  they never enter livespec core's public functional surface or the
  `/livespec:*` skills.

## Three first-class ecosystems (closed set): Python, Rust, JavaScript

A copier question `ecosystem = python | rust | javascript` selects a
profile of presets; EVERY key stays individually overridable.

| | Python | Rust | JavaScript/TS |
| - | - | - | - |
| Runner (mandated) | `just` | `just` | `just` |
| Native pass-through wrapper | — | `cargo xtask worktree …` → `just worktree-…` | package.json `"wt:…": "just worktree-…"` |
| Hydrate cmd | `uv sync` (or poetry/pip) | `cargo fetch` + warm cache | `pnpm install` |
| Per-worktree dep state | `.venv/` (cache-cheap) | NONE in-tree (see below) | `node_modules/` incl. workspaces |
| Hook framework (mandated) | `lefthook` | `lefthook` | `lefthook` |
| Verify gate (under `just check`) | pytest + ruff + pyright | cargo build/test/clippy/fmt | build + lint + test |

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

`ecosystem` (python | rust | javascript); `hydrate_cmd` (install/hydrate
cmd, defaulted per ecosystem); `worktree_root` (default
`~/.worktrees/<repo>/<branch>`); `land_mode` (pr | merge-queue | direct);
`uses_mise` (gates the auto-trust step). There is NO `task_runner`
question — the runner is `just` (mandated); where a wrapper needs the
ecosystem's native tool it DERIVES it from `ecosystem` (python → none;
rust → cargo-xtask; javascript → pnpm-scripts), as a strict pass-through
to `just`. There is NO `hook_framework` choice — `lefthook` is mandated
(the conformance `lefthook → just check` commit-time tier).

## What stays identical across all three

The runner (`just`), the hook framework (`lefthook`), the contract, and the
enforcement check are identical across all three ecosystems; the portable
core and the gate are pure-git. Only the per-ecosystem HYDRATE profile
varies (and, where a repo exposes its native tool, a strict pass-through
wrapper onto `just worktree-*`). Adding a 4th ecosystem later = a new
hydrate branch, no core/gate/runner change.

## Rollout (dogfood -> promote)

1. Build the pieces in openbrain (ob-apw) — the JS/pnpm dogfood instance,
   template-shaped (pure-git core driven by `just worktree-*` recipes + a
   `lefthook` gate + an AGENTS.md protocol section).
2. Extract/promote into `templates/impl-plugin/` as this pack; add the
   Python and Rust hydrate profiles.
3. Spec it (orchestrator contracts.md + non-functional-requirements.md).
4. `copier update` propagates to openbrain + other consumers; the drift
   workflow flags divergence.

## Acceptance

A freshly scaffolded OR copier-updated repo in Python, Rust, OR JavaScript
gets BY DEFAULT: the worktree lifecycle driven by `just worktree-*`
(with a strict pass-through native wrapper where the ecosystem has one); a
`lefthook`-wired gate that blocks commits on the primary checkout;
ecosystem-correct hydration (including Rust's shared build cache); a
reaper; PR/merge landing. No agent needs manual instruction. `just` and
`lefthook` are mandated non-functionally, and never enter livespec core's
public functional surface or the `/livespec:*` skills.
