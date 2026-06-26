> **ARCHIVED 2026-06-26 — ob-0x5 CLOSED.** This handoff is historical; do NOT
> "run" it. Its track was reconciled into the livespec Conformance Pattern and
> its only residual (Phase-7 distribution) was **re-scoped**: a fleet-wide audit
> found the copier-COPY delivery of the worktree pack is the same drift-prone
> anti-pattern as the commit-refuse hook (3+ already-divergent vendored
> `git-hook-wrapper.sh` copies fleet-wide). Per zs22.7's "reuse, no copies"
> delivery rule, Phase-7 distribution + the hook de-dup are now ONE work item —
> **`livespec-zs22.7.9` (dev-tooling single-source convergence)** — which is the
> live home for any remaining work. Snapshot of disposition at close:
> Mechanism + Phases 1-4 DONE (shipped in livespec release **v0.4.0**);
> Phases 5-6 superseded (Fabro Architecture C) / inherited; git-jsonl got the
> pack via copier-copy as an **interim** (PR #126, merged); beads-fabro
> distribution **paused** (no copies vendored); console already installs
> from-package (at the convergence target — sidecar concern **retired**).
> Authoritative status: the livespec ledger (`livespec-zs22.7.9`), the commits,
> and the spec — never this file.

# Handoff: Worktree Discipline Pack (epic ob-0x5)

**Track:** worktree-discipline · **Epic:** openbrain **`ob-0x5`** (cross-repo:
the implementation lands in the livespec fleet) · **Dogfood precedent:**
openbrain `ob-apw` (the JS/pnpm local adoption).

This is the SINGLE consolidated, resumable handoff for this track — it
supersedes and replaces the former three-file set (`worktree-discipline-pack-epic.md`,
`worktree-discipline-pack-prompt.md`, and `tmp/worktree-discipline-pack/HANDOFF.md`),
all now deleted. It carries the durable *design* AND the current *plan*; the
*authoritative status* lives in the ledger, never in this file.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-openbrain-env.sh bd -C /data/projects/openbrain show ob-0x5
```

`ob-0x5` lives in the **openbrain** tenant (it has its OWN env wrapper —
`with-openbrain-env.sh` — not the livespec one). Derive "what's done / what's
next" from that plus `git log` in each target repo. NOTE: the worktree-discipline
CONCERN has been substantially reconciled into the livespec **Conformance Pattern**
(`livespec-zs22.7`, concern #1 "Worktree-discipline — reconciles ob-0x5"); read
that epic too (`with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7`).

## Read first

1. This file (the design + plan, below).
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   Conformance Pattern that now OWNS the worktree-discipline concern as its
   five-slot concern #1. The pack's Mechanism/Installer/Verifier are that
   pattern's slots.
3. `/data/projects/livespec/AGENTS.md` §"Repository mutation protocol" — the
   reference behaviour this pack generalizes and distributes.
4. The copier carrier: `templates/impl-plugin/` (`copier.yml`,
   `copier-questions.yml`, `*.jinja`, `copier-update-drift.yml`) — how the pack
   propagates to consumers.

## Objective (and the reconciliation reality)

Original goal: bundle worktree discipline into the orchestrator (the copier
impl-plugin template + skills + spec) so EVERY consuming repo gets it **by
default** — enforced, ecosystem-correct (Python/Rust/JS first-class) — WITHOUT a
human instructing each agent session.

**Most of this is now DONE or SUPERSEDED; the residual is distribution.** Triple-
checked 2026-06-26 (verify before relying — repos move):

- The worktree-discipline **Mechanism** (the structural commit-refuse hook:
  refuse when `git rev-parse --git-dir` == `git rev-parse --git-common-dir`)
  landed and was reconciled fleet-wide under `livespec-zs22.7.3` (M2). It is
  installed from the `livespec-dev-tooling` installer module
  (`python -m livespec_dev_tooling.install_commit_refuse_hooks`, v0.19.0), NOT
  from the old `refuse-primary-commit.sh` (that file was DELETED — every former
  WDP doc referenced it; this handoff is reconciled to the structural wrapper).
- The cross-cutting-instruction-conformance half ob-0x5 absorbed is now tracked
  as SEPARATE items: `livespec-a244` (the keystone NFR), `livespec-co9h`
  (block-auto-memory hook), `livespec-8njn` (durable-memory capture convention).
  This handoff POINTS at them; it does not own them (no shadow ledger).

## Current state (verified 2026-06-26)

### DONE (landed on livespec-core master)

- **Phase 1** (PR #586) — ecosystem-neutral portable core + gate:
  `templates/impl-plugin/dev-tooling/worktree-lib.sh` (create / hydrate / land /
  reap + `git-common-dir` vs `git-dir` primary detection), wired in
  `lefthook.yml.jinja`.
- **Phase 2/3** (PR #591) — `ecosystem` copier question (python | rust |
  javascript) + per-ecosystem hydrate profiles (python `.venv`; js
  `node_modules` incl. workspaces; **rust = warm/shared BUILD cache (sccache or
  shared `CARGO_TARGET_DIR`), NOT a dep-dir copy**).
- **`just`+`lefthook` reconciliation** (PR #595) — `just worktree-*` recipes call
  `worktree-lib.sh` directly; ecosystem wrappers are STRICT pass-throughs to
  `just`; `just`/`lefthook` mandated NON-functionally (never in core's functional
  surface or `/livespec:*`).
- **Phase 4** (PR #599, master `68e4a02`) — server-side tripwire via the GitHub
  branch-protection PRIMITIVE: `templates/impl-plugin/dev-tooling/branch-protection.sh`
  + `just protect-default-branch` (Installer) + `just check-branch-protection`
  (fail-closed, capability-aware Verifier, wired into `just check`). Exemption =
  `LIVESPEC_BRANCH_PROTECTION_CHECK=fail|warn|skip`.
- **Bootstrap parse fix** (PR #601) — the template's `bootstrap:` recipe is a
  shebang recipe (so the rendered justfile parses under `just` 1.36.0); the copier
  smoke check now `just --summary`s the rendered justfile.
- **Mechanism reconciliation** (`livespec-zs22.7.3` / M2) — the gate is the
  structural single-wrapper installed from the dev-tooling module; the legacy
  `refuse-primary-commit.sh` was deleted fleet-wide.

### SUPERSEDED (do NOT build these as originally scoped)

- **Phase 5 (auto-provision a host worktree per work-item) — SUPERSEDED by the
  orchestrator's Fabro "Architecture C".** The Fabro dispatcher does NOT create a
  host worktree per item; it clones FRESH inside a docker sandbox, so "the host
  owns no git working state" and the sandbox clone IS "the secondary-worktree
  EQUIVALENT under the family discipline" (`_dispatcher_engine.py`,
  `.fabro/workflows/implement-work-item/workflow.toml`). Isolation-by-
  construction — the Phase-5 GOAL — is already met. The only host `git worktree
  add` is the post-merge janitor venue, not per-item work. Building host
  worktrees now would CONTRADICT Architecture C.
- **Phase 6 (restate the contract in the orchestrator's `SPECIFICATION/`) —
  SATISFIED BY INHERITANCE.** The orchestrator has `contracts.md` but no
  `non-functional-requirements.md`; its `constraints.md` §"Inherited from
  livespec" inherits every livespec-core NFR by reference, and the worktree-
  discipline contract lives in livespec core's `non-functional-requirements.md`
  §"Conformance Pattern" (concern #1). A local restatement would duplicate, not
  add. (If a maintainer wants an explicit orchestrator-local pointer, that is a
  one-line spec cycle, not a phase.)

### GENUINELY REMAINING — Phase 7: distribute the pack

The pack files (`worktree-lib.sh`, `branch-protection.sh`, the hydrate profiles,
the `just worktree-*` recipes) live ONLY on the template's `origin/master` and
have NEVER been cut into a release tag. Both impl-plugin consumers are pinned at
`.copier-answers.yml` `_commit: v0.3.0` (which PRE-DATES the pack) and their trees
do NOT contain the pack files:

- `livespec-orchestrator-beads-fabro` — STALE + MISSING the pack.
- `livespec-orchestrator-git-jsonl` — STALE + MISSING the pack.

So the residual work is:

1. **Cut a release tag** that includes the pack (the fleet pins track the latest
   RELEASE, not master — per the zs22 locked decision), OR drive a
   `copier update --vcs-ref=master` to each consumer; then `bump-pin` fan-out so
   each consumer's `.copier-answers.yml` `_commit` advances and the pack files
   land in its tree. Confirm `copier update` applies cleanly (the drift workflow
   flags divergence).
2. **The console question (`livespec-console-beads-fabro`).** It is Rust and is
   NOT copier-scaffolded (no committed `.copier-answers.yml`). Its temporary
   `prompts/worktree-discipline-sidecar.md` was ALREADY removed from
   `origin/master` (it lingers only on side branches) — i.e. removed AHEAD of its
   own stated retire condition (delivery via `copier update`). Decide: onboard the
   console to the copier template so it gets the pack by default, or accept its
   M3-landed structural commit-refuse hook + `just check` verifier (see
   `livespec-zs22.7.4`, DONE) as sufficient and formally retire the sidecar
   concern. The console already carries the Mechanism; what it lacks is the
   `just worktree-*` LIFECYCLE recipes + hydrate profile.

## Design (durable — fold-in from the retired epic, reconciled)

**`just`+`lefthook` keystone + portable core + per-ecosystem profiles.** Per the
zs22 Conformance Pattern, `just` and `lefthook` are mandated NON-functionally
across all fleet + adopter repos — never in livespec core's public functional
surface or the `/livespec:*` skills.

- **Contract (tool-agnostic):** every mutation in an isolated worktree; the
  primary checkout is never committed to; landing via PR/merge; orphans reaped; a
  commit-time gate enforces it.
- **Portable core:** `dev-tooling/worktree-lib.sh` — dependency-light POSIX shell;
  create / hydrate / land / reap + primary-vs-linked detection. Pure-git; correct
  under any runner.
- **Invocation:** `just worktree-{create,hydrate,land,reap}` call `worktree-lib.sh`
  directly. Any ecosystem-native wrapper (rust `cargo xtask worktree create`; js
  package.json `"wt:create"`) is a STRICT pass-through to `just worktree-*` with
  no logic of its own. DERIVE the native tool from `ecosystem`; there is NO
  `task_runner` copier question.
- **Enforcement:** the structural commit-refuse hook (installed from
  `livespec-dev-tooling`'s `install_commit_refuse_hooks` module) wired via
  `lefthook` as the first pre-commit job + commit-msg backstop, with
  `lefthook → just check` as the commit-time tier + the branch-protection
  server-side tripwire. There is NO `hook_framework` copier choice — `lefthook` is
  mandated.
- **Three first-class ecosystems** (`ecosystem` = python | rust | javascript),
  each presetting `hydrate_cmd` (overridable). "Hydrate" differs per ecosystem:
  JS = `node_modules` (incl. workspace sub-packages — the openbrain `dashboard/`
  gotcha); Python = `.venv`; **Rust = warm/share the BUILD cache** (crates live in
  `$CARGO_HOME`, shared; the real cost is a cold `target/` recompile → default to
  sccache / shared `CARGO_TARGET_DIR`). Do NOT model Rust as "JS but with cargo".
- **Config keys (copier questions):** `ecosystem`; `hydrate_cmd`; `worktree_root`
  (default `~/.worktrees/<repo>/<branch>`); `land_mode` (pr | merge-queue |
  direct); `uses_mise`.

## Next concrete action

**Drive Phase 7 distribution.** Cut/confirm a release tag of the copier template
that includes the pack, then fan the pin/`copier update` out to
`livespec-orchestrator-beads-fabro` and `livespec-orchestrator-git-jsonl` so each
gets the `worktree-lib.sh` + `branch-protection.sh` + `just worktree-*` recipes +
its ecosystem hydrate profile by default; verify `copier update` applies cleanly
and `just check` stays green on each. Then resolve the console question (onboard
to copier vs. formally retire the sidecar concern given the M3 Mechanism already
landed). Each consumer change is its own worktree → PR → rebase-merge.

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in `~/.worktrees/<repo>/<branch>`; land via
  PR → rebase-merge; never commit on a primary checkout. `mise exec -- git …`;
  never `--no-verify`; halt and report on any hook failure.
- **`just`/`lefthook` mandated NON-functionally only** — never in livespec core's
  functional surface or `/livespec:*`. Native wrappers are strict pass-throughs.
- **Pins track the latest RELEASE, not master HEAD** (zs22 locked decision).
- **No shadow ledger.** This handoff points at ledger ids; status comes from the
  FIRST ACTION query.

## Open question for the maintainer (ledger reconciliation)

ob-0x5's Mechanism is fully reconciled into `livespec-zs22.7` (concern #1) and
its instruction-conformance half into `a244`/`co9h`/`8njn`. Phases 5–6 are
superseded/inherited. The ONLY residual is Phase-7 distribution, which overlaps
zs22.7's M6 (fleet-time / four-tier enforcement) and the general copier-distribution
+ pin-and-bump machinery. **Recommendation:** consider folding the Phase-7
residual into zs22.7 M6 and CLOSING ob-0x5 (with a note pointing at M6 + the
console decision), rather than carrying a near-complete P1 epic. The maintainer
owns that call.

## Literal next-session command (one path)

```
run prompts/worktree-discipline-pack-handoff.md
```

A fresh session opening only this handoff and its Read-first chain can execute
the next action (Phase-7 distribution) after confirming live status via the FIRST
ACTION ledger query.

## Archive condition

When ob-0x5 closes (Phase 7 distributed OR folded into zs22.7 M6, the console
decision made), `git mv` this file to `archive/prompts/` with a completion
banner. Durable history then lives in the spec, the commits, and the ledger.
