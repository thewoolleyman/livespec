# fleet-shell-discipline — why this shape

**Archived 2026-08-03.** This file preserves the measurements and reasoning at
thread formation. Statements below that describe questions as open or either
epic as live are historical; the resolved outcome and terminal evidence are in
`handoff.md`, and the convention is ratified in livespec history `v187`.

**Owning repo:** `livespec` — the fleet's reference repo and the home of the
conventions the family follows. Placed here by maintainer direction
2026-08-02.

**Ledger anchor:** epic **`livespec-hhu5pn`** (this repo's tenant) — the thread's
status anchor. This thread is active if and only if that epic is open, and
archives to `plan/archive/fleet-shell-discipline/` when it closes.

**Status is not stored here.** Read it from the ledger
(`list-work-items` / `next`). Every id in this file is cited read-only.

## The mandate — set by the maintainer, not derived here

Three requirements, in the maintainer's own terms:

1. **Enforce usage of `shellcheck` across the fleet — mechanically.**
2. **Mechanically forbid any interpolated bash in `justfile` recipes.** Only
   direct invocations / calls out to `*.sh` files for any logic.
3. **Make the enforcement appropriate** — use `-e` and other `set -o` options
   *as appropriate for the script being called*, rather than one blanket rule.

Requirement 2 is the keystone and the reason this is one thread rather than
three; see "Why requirement 2 is load-bearing" below.

## What triggered it

`check-per-file-coverage` ran `set -uo pipefail` with **no `-e`**. A non-zero
`pytest` therefore did not abort the recipe, and the recipe's exit status became
the *last* command's — the coverage check. A test failing at an assertion whose
lines were already covered left coverage at 100% and the target exited **0**.

Proven asymmetrically in `livespec-overseer` rather than argued, with one
deliberately failing test (a single statement, so its file stays 100% covered —
precisely the masked mode):

| recipe form | recipe rc | verdict |
|---|---|---|
| `set -uo pipefail` | **0 — GREEN**, with `FAILED` in its own output | masked |
| `set -euo pipefail` | **1 — RED** | caught |

The sabotage was asserted to produce a real failure *before* either verdict was
read. Fixed for that one repo in `livespec-overseer` PR #470.

**It was never confined to developer hosts.** In that repo the target is its own
CI matrix job *and* was a required status check, so the masked green reached
branch protection and the Dispatcher's "latest master is green" pre-flight.

**`livespec` core already fixed this once**, in `bc5c9bce` (2026-07-01), with the
diagnosis written into the recipe as a comment — independently, a month before
the fleet rediscovered it. Five repos never caught up: `livespec-overseer` (now
fixed), `livespec-dev-tooling`, `livespec-orchestrator-beads-fabro`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime`. **That this repo's own fix
did not propagate is the real finding** — there was no mechanism to carry it.

## The measured surface (2026-08-02)

**Nothing lints shell anywhere in the fleet.** `livespec_dev_tooling/checks/`
holds **81** modules and not one of them reads shell. `shellcheck` **0.10.0** is
installed on the dev host and referenced in no workflow, `pyproject.toml`,
`justfile` or doc.

Tracked `.sh` files, per repo:

| repo | `.sh` |
|---|---|
| `livespec-dev-tooling` | 19 |
| `livespec-orchestrator-beads-fabro` | 16 |
| `livespec` | 4 |
| `livespec-orchestrator-git-jsonl` | 3 |
| `livespec-console-beads-fabro` | 2 |
| `livespec-overseer`, `livespec-runtime`, `livespec-driver-claude`, `livespec-driver-codex` | 1 each |
| **total** | **48** |

`justfile` recipes, per repo — the population requirement 2 governs:

| repo | recipes | bash shebang | multi-line | uses `{{…}}` |
|---|---|---|---|---|
| `livespec-orchestrator-beads-fabro` | 100 | 16 | 17 | 11 |
| `livespec` | 99 | 14 | 14 | 8 |
| `livespec-dev-tooling` | 85 | 13 | 13 | 8 |
| `livespec-orchestrator-git-jsonl` | 85 | 12 | 14 | 7 |
| `livespec-overseer` | 83 | 16 | 16 | 5 |
| `livespec-runtime` | 78 | 12 | 12 | 5 |
| `livespec-driver-codex` | 78 | 9 | 10 | 1 |
| `livespec-driver-claude` | 77 | 8 | 9 | 1 |
| `livespec-console-beads-fabro` | 33 | 5 | 13 | 3 |
| **total** | **718** | **105** | **118** | **49** |

**The encouraging number: ~83% of the 718 recipes are already single direct
invocations.** Requirement 2 largely *codifies existing practice*; the migration
surface is the ~118 recipes carrying logic, of which 49 interpolate. That is a
bounded, countable job rather than an open-ended rewrite.

## Why requirement 2 is load-bearing, not stylistic

Before it, shell in this fleet is **two populations, and only one is
lintable**:

- 48 `.sh` files — `shellcheck` reads these directly today.
- 105+ bash recipes embedded in `justfile`s — **shellcheck cannot read these**.
  A recipe is indented under a target, its shebang sits on the recipe's first
  line rather than the file's, and `{{…}}` is `just` interpolation that is not
  valid shell. Any gate covering them must extract and de-interpolate first.

**The defect that started this lived in the unlintable population.** So a
shellcheck rollout scoped to `.sh` files would have been fully green and would
still have missed it.

Requirement 2 dissolves that: if no logic lives inside a recipe, there is no
second population. `shellcheck` over `*.sh` becomes **total** coverage of fleet
shell logic, and the justfile returns to being a task index. This is why the
three requirements are one thread — 1 is not trustworthy without 2, and 3 is
only expressible once the logic lives in files that can declare their own
options.

## Requirement 3, and the trap it must avoid

**A blanket `set -euo pipefail` rule would be wrong, and this is measured, not
theoretical.** In `livespec-overseer`, **nine** recipes use `set -uo pipefail`
without `-e` and **exactly one** was defective. The others are correct:

- `check-prose-release-hygiene` documents the omission deliberately — `grep -c`
  exits 1 on a zero count, so `-e` would abort at the very violation the recipe
  exists to report;
- `check-coverage` and `changed-files` end on their load-bearing command, so the
  status propagates by construction;
- `check-pre-commit` / `check-pre-push` `exit $?` explicitly.

"Nine recipes are broken" was a false alarm caught only by reading each one.

**So the enforceable property is not "always `-e`". It is that a deviation must
be DECLARED rather than silent.** Today a deliberate, reasoned omission and an
accidental one are byte-identical, and that indistinguishability *is* the defect.
A workable shape is a shared preamble as the default plus an explicit, greppable
declaration for departures — which also gives requirement 1 something mechanical
to check beyond shellcheck's own rules.

Reference boilerplate supplied by the maintainer:
`https://github.com/thewoolleyman/bashstyle_examples` (`bash-boilerplate.sh`) —
sets `errexit`, `errtrace`, `noclobber`, `pipefail`, `nounset`; installs an
`onexit` trap on `HUP INT QUIT TERM ERR`; provides `enable_error_checking` /
`disable_error_checking` and `BASH_XTRACE` / `BASH_VERBOSE` toggles. Note it
pre-seeds `PROMPT_COMMAND` before `nounset` precisely because an unbound
variable under `-u` is a footgun — the same class of care this thread is about.

## Constraints any design must survive

1. **Measure the whole corpus before writing any rule.** The originating track
   killed four plausible gates exactly this way, each with a false positive
   already sitting in the tree. A gate is not justified by being correct on the
   example that motivated it.
2. **`shellcheck` will not be clean on first run over 48 files.** Adoption needs
   a severity floor or a baseline, or it lands red and gets disabled. Decide
   which before writing the check, and prefer a floor that can ratchet.
3. **A gate whose easiest remedy is the defect it prevents is worse than no
   gate.** Recorded from a provenance gate that was designed and rejected here
   for exactly that reason.
4. **This fleet runs zsh, and bash idioms fail silently in it.** `PIPESTATUS` is
   bash (`$pipestatus[1]` here, and clobbered by the next command); unquoted
   parameter expansions do **not** word-split in zsh, so `set -- $row` yields one
   argument. Both read as passes. Any tooling this thread ships must be tested in
   the shell it will actually run under.

## Relationship to the livespec-dev-tooling thread — DECIDED 2026-08-02

A sibling thread exists: `livespec-dev-tooling`
`plan/fleet-shell-quality-enforcement/`, epic **`livespec-dev-tooling-42t4az`**,
carrying the same triggering defect and the same shellcheck measurements. It
predates requirements 2 and 3.

**The maintainer decided the split, and NEITHER thread closes.** They divide by
what each repo is for:

| thread | owns |
|---|---|
| **this one** (`livespec`, `livespec-hhu5pn`) | **the convention and its enforcement design** — what the rule IS, which set-options suit which script, how a deliberate deviation is declared so a gate can tell it from an accident, and whether interpolated bash in recipes is forbidden outright or narrowly |
| `livespec-dev-tooling` (`42t4az`) | **building and shipping the check** — shellcheck adoption, the severity floor or baseline, the module itself, and its arrival in every consumer by pin bump |

**Why that split rather than an arbitrary one.** This repo already fixed the
triggering defect once — `bc5c9bce`, 2026-07-01, with the diagnosis written into
the recipe as a comment — and **the fix never propagated** to the five repos
carrying the same shape. A convention that lives only in the reference repo's own
code does not travel; a check that ships by pin does. So the reference repo owns
what the rule says, and the tooling repo owns the mechanism that carries it.

**The cost, stated because it is the real risk of not closing one:** two live
threads on one subject drift unless the boundary is written into both. It is
written into both, here and on each epic. If a piece of work does not obviously
belong to "what the rule is" or "how the rule ships", raise it rather than filing
it in whichever thread is closer to hand.

Cross-references are read-only in both directions; neither thread stores the
other's status.

## Related records, cited read-only

- `livespec-overseer` PR #470 — the single-repo `-e` fix and its asymmetric proof.
- `livespec-overseer` `overseer-jdo` — the flaky aggregate whose statistical
  acceptance cannot be measured while the gate can hide the failures it counts;
  unmasking is a precondition, not a follow-up.
- `livespec-dev-tooling` `livespec-dev-tooling-42t4az` — the sibling thread above.

## What is deliberately NOT decided here

Nothing is filed as ready work by this note. Open: whether requirement 2 is
enforced by a check that rejects any multi-line or `{{…}}`-bearing recipe body,
or something narrower; what the `.sh` extraction does about `just` variables the
recipes currently interpolate (49 of them); the shellcheck severity floor; and
how a declared deviation from the default option set is spelled so a gate can
tell it from an accident.
