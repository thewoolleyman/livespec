# Prompt: build the Worktree Discipline Pack for the livespec orchestrator

You are executing the epic in `prompts/worktree-discipline-pack-epic.md`
(tracked as openbrain **ob-0x5**; dogfood precedent openbrain **ob-apw**).

Goal: make worktree discipline a DEFAULT, enforced, ecosystem-correct
capability that every livespec-orchestrator consuming repo gets without a
human telling each agent session — first-class for Python, Rust, and
JavaScript.

## Startup checks

1. Read `prompts/worktree-discipline-pack-epic.md` (the full design).
2. Read this repo's `AGENTS.md` "Repository mutation protocol" — it is the
   reference behavior to generalize and distribute.
3. Map the carrier: `templates/impl-plugin/` is a copier scaffold
   (`copier.yml`, `copier-questions.yml`, `*.jinja`, `copier-update-drift.yml`)
   — so changes propagate to existing consumers via `copier update`.
   Inspect `justfile.jinja`, `lefthook.yml.jinja`, `dev-tooling/git-hook-wrapper.sh`,
   `.github/workflows/` (note `auto-enable-merge`, `release-dispatch`), and
   `AGENTS.md`.
4. DOGFOOD: do all of this work in a worktree under
   `~/.worktrees/livespec/<branch>` and land via PR — never commit on the
   primary checkout.

## What to build (phased)

1. **Portable core + gate (ecosystem-neutral):** a dependency-light
   worktree-lifecycle implementation (create / hydrate / land / reap +
   `git-common-dir` vs `git-dir` primary detection) and a "refuse commits
   on the primary checkout" check. Pure-git, no language assumptions.
2. **Invocation = `just worktree-*` recipes** calling the portable core
   (`dev-tooling/worktree-lib.sh`) DIRECTLY. The worktree lifecycle is
   driven by `just` — `just` is mandated non-functionally, not optional.
   Where the ecosystem has a native tool, emit a STRICT PASS-THROUGH
   wrapper that literally invokes `just worktree-*` with no logic of its
   own (rust: `cargo xtask worktree create` → `just worktree-create`;
   javascript: package.json `"wt:create": "just worktree-create"`); never
   an alternative runner/framework. DERIVE the native tool from
   `ecosystem` — there is NO `task_runner` copier question.
3. **Three first-class ecosystem hydrate profiles** (`ecosystem` copier
   question: python | rust | javascript), each presetting the hydrate cmd
   (overridable). Critically, the Rust profile's hydrate = warm/share the
   BUILD cache (sccache or shared `CARGO_TARGET_DIR`), NOT copying a dep
   dir (there is none — crates live in `$CARGO_HOME`). JS hydrate =
   node_modules incl. workspace sub-packages; Python hydrate = `.venv`.
4. **Wire enforcement via `lefthook`** (the mandated commit-time framework,
   per the conformance `lefthook → just check` tier): the
   `refuse-primary-commit.sh` gate runs first in pre-commit AND as the
   commit-msg backstop, plus a server-side tripwire mirror. There is NO
   `hook_framework` copier choice. The server-side mirror reuses the GitHub
   branch-protection PRIMITIVE (not a bespoke per-consumer workflow):
   `just protect-default-branch` (Installer) + `just check-branch-protection`
   (the fail-closed, capability-aware Verifier, wired into `just check`), both
   via the portable `dev-tooling/branch-protection.sh`.
5. **Default path:** make `implement`/dispatcher auto-provision a worktree
   per work-item.
6. **Spec it** via the livespec lifecycle (orchestrator `contracts.md` +
   `non-functional-requirements.md`): the worktree contract is mandated,
   and `just`/`lefthook` are mandated non-functionally as the mechanism —
   while NEVER entering livespec core's public functional surface or the
   `/livespec:*` skills.
7. **Distribute:** ship in the copier template; verify `copier update`
   propagates cleanly; the drift workflow flags divergence.

## Constraints / non-negotiables

- `just` and `lefthook` are mandated non-functionally (fleet+adopter-wide)
  as the worktree pack's mechanism — Installer = a `just` recipe; commit
  gate wired via `lefthook → just check`. They NEVER enter livespec core's
  public functional surface or the `/livespec:*` skills. Any native
  wrapper (cargo xtask, pnpm/npm scripts) is a strict pass-through to `just
  worktree-*`, never an alternative runner/framework.
- Rust is first-class: handle "hydrate = warm build cache" explicitly.
- The portable core (`worktree-lib.sh`) is the single source of truth; the
  `just worktree-*` recipes call it directly and carry no logic (or
  ecosystems drift — the thing `copier update` + the drift workflow exist
  to catch).
- Dogfood the discipline while building it (worktree + PR; never the primary).

## Close criteria

A freshly scaffolded OR `copier update`-d Python/Rust/JS repo gets, by
default: the worktree lifecycle driven by `just worktree-*` (with a strict
pass-through native wrapper where the ecosystem has one); a
`lefthook`-wired gate blocking primary-checkout commits; ecosystem-correct
hydration (incl. Rust shared build cache); a reaper; PR/merge landing —
with zero manual per-session instruction. Update openbrain ob-0x5 status
and archive this prompt pair when the epic closes.
