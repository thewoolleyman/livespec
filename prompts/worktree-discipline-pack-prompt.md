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
   on the primary checkout" check. No task-runner or language assumptions.
2. **Invocation adapters:** thin wrappers mapping the repo's OWN task
   runner onto the core. `just` is ONE reference adapter — do NOT require
   it. Drive the choice from a `task_runner` copier question.
3. **Three first-class ecosystem profiles** (`ecosystem` copier question:
   python | rust | javascript), each presetting {runner, hydrate cmd,
   hook framework, verify gate}, all keys overridable. Critically, the
   Rust profile's hydrate = warm/share the BUILD cache (sccache or shared
   `CARGO_TARGET_DIR`), NOT copying a dep dir (there is none — crates live
   in `$CARGO_HOME`). JS hydrate = node_modules incl. workspace
   sub-packages; Python hydrate = `.venv`.
4. **Wire enforcement** via the repo's hook framework (`hook_framework`
   copier question: lefthook | husky | pre-commit | raw) + a server-side
   tripwire mirror.
5. **Default path:** make `implement`/dispatcher auto-provision a worktree
   per work-item.
6. **Spec it** via the livespec lifecycle (orchestrator `contracts.md` +
   `non-functional-requirements.md`): the contract is mandated, the task
   runner / hook framework are NOT.
7. **Distribute:** ship in the copier template; verify `copier update`
   propagates cleanly; the drift workflow flags divergence.

## Constraints / non-negotiables

- Mandate the CONTRACT, never a specific tool. No repo is required to use
  `just`, lefthook, or any one runner/framework.
- Rust is first-class: handle "hydrate = warm build cache" explicitly.
- The portable core is the single source of truth; adapters stay logic-free
  (or ecosystems drift — the thing `copier update` + the drift workflow
  exist to catch).
- Dogfood the discipline while building it (worktree + PR; never the primary).

## Close criteria

A freshly scaffolded OR `copier update`-d Python/Rust/JS repo gets, by
default: worktree lifecycle via its own runner; a gate blocking
primary-checkout commits; ecosystem-correct hydration (incl. Rust shared
build cache); a reaper; PR/merge landing — with zero manual per-session
instruction. Update openbrain ob-0x5 status and archive this prompt pair
when the epic closes.
