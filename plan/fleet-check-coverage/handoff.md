# Handoff — fleet-check-coverage

The single resumable entry point for the **fleet-check-coverage** thread: make
every structural check shipped by `livespec-dev-tooling` cover every tracked
first-party `.py` in every fleet repo, automatically — by replacing per-repo
coverage allowlists (which fail OPEN) with filesystem-derived coverage plus
fail-closed guards, rolled out **warn → burndown → per-repo-fail** so nothing
breaks all at once. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** A `dispatcher.py` of 2,616 lines
  (`livespec-orchestrator-beads-fabro/.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/dispatcher.py`)
  sailed past the fleet's per-file logical-line ceiling because the `file_lloc`
  check walks a HARDCODED `.claude-plugin/scripts/livespec/` tree that does not
  exist in a repo whose package dir is named `livespec_orchestrator_beads_fabro/`
  — so it walked zero files and exited 0. Every other structural check has the
  same class of blindness there (its per-repo `[tool.livespec_dev_tooling]` block
  restates core's `livespec/` paths verbatim). Read the research docs before
  acting:
  - `plan/fleet-check-coverage/research/root-cause.md` — why the allowlist model
    fails open, with reproduce commands.
  - `plan/fleet-check-coverage/research/design.md` — the target
    (filesystem-derived universe via `git ls-files`, fail-closed empty guard,
    partition-completeness meta-check), the exemption policy (`_vendor/` + tests +
    `@generated`-marked + `templates/**`), the three-phase rollout, and the
    (now-resolved) open questions.
  - `plan/fleet-check-coverage/research/check-inventory.md` — the Phase-0
    classification: which checks derive their universe vs stay role-scoped, the
    per-repo first-party `.py` counts, and the wiring/severity facts.
- **Companion adversarial prompt.**
  `plan/fleet-check-coverage/live-adversarial-review-prompt.md` — hand this to an
  independent reviewer session; a NO-BLOCKERS verdict is a precondition for
  accepting any Phase-2 flip.
- **Epic anchored.** `livespec-i5ebqd` [EPIC] is the thread's status anchor; the
  Phase-0 mechanism is tracked as child `livespec-fa3eu5` (MAINTAINER-DRIVEN,
  blocked/needs-human — do NOT auto-dispatch). Status is READ live from the ledger
  (`bd show <id>`), never stored here.
- **⚑ Golden rules.**
  - Ready, factory-safe implementation is **factory-dispatched** — never
    hand-coded inline in the overseer session. The overseer FILES and DISPATCHES;
    the factory (Dispatcher / the `drive` operation) builds each item under the
    `just check` + `/livespec:doctor` janitor gate.
  - **Parallel, not sequential.** Phase 1 burndown runs every repo's track
    concurrently through the factory; do NOT serialize repo-by-repo. The only
    real ordering edge is that a repo's burndown wants the Phase-0 dev-tooling
    release pinned first — so Phase 0 is the one barrier; after it, fan out wide.
  - The Phase-0 MECHANISM lands as a normal `livespec-dev-tooling` PR (host-side,
    maintainer-driven). The Phase-1 BURNDOWN is factory work. The Phase-2 per-repo
    FLIP adds **NO escape hatch / severity lever / skip** to pass
    (`.ai/ci-gate-discipline.md`) — it is severity, never a bypass.
  - Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
  - The overseer session **rotates before ~50% context**: refresh THIS file
    (current state, in-flight PRs/agents per repo, next action), then print the
    resume command verbatim as the LAST line of the recap.
  - Once the epic exists, status is READ live from the ledger / GitHub PRs — never
    stored in this file (no shadow ledger).
  - Print an `Epic · Track (repo) · Status · %Complete` table (read live) before
    any gate or status report, and refresh it every ~15 minutes while tracks run.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-check-coverage`

## The fleet — every repo in scope

The mechanism lands in `livespec-dev-tooling`; the burndown + flip touch every
repo that ships first-party Python. Confirm the actual per-repo `.py` inventory
in Phase 0 (`git -C <repo> ls-files '*.py' | grep -v _vendor/`) rather than
trusting this table:

| Repo | Role | Expected under the new checks |
|---|---|---|
| `livespec-dev-tooling` | the shared check package | mechanism lands here; also self-covers |
| `livespec` (core) | hub / dogfood | already covered today; verify no regression |
| `livespec-orchestrator-beads-fabro` | orchestrator | large backlog (dispatcher.py + siblings) — the trigger |
| `livespec-console-beads-fabro` | operator console app | **0 tracked `.py`** — the ONE genuinely empty-universe repo; empty-walk guard MUST PASS, not error |
| `livespec-orchestrator-git-jsonl` | orchestrator | real coverage; verify |
| `livespec-runtime` | library | real coverage; verify |
| `livespec-driver-claude` | thin runtime binding | NOT codeless: 2 first-party hook `.py` (`.claude-plugin/hooks/`, `.claude/hooks/`) — MUST be covered |
| `livespec-driver-codex` | thin runtime binding | NOT codeless: 3 first-party hook `.py` (`livespec/hooks/`) — MUST be covered |

The empty-walk guard's correctness on the ONE genuinely empty-universe repo
(`livespec-console-beads-fabro`, 0 tracked `.py` → MUST pass) is a first-class
acceptance case — as is confirming the Driver repos' hook `.py` are COVERED (they
are NOT codeless). See the adversarial prompt.

## The next action

> **Phase 0 — mechanism, warn-only.**
>
> **DONE (2026-07-08):** epic `livespec-i5ebqd` anchored; the dev-tooling check
> set enumerated + classified (→ `research/check-inventory.md`); the two blocking
> open questions resolved (→ `research/design.md`): OQ1 = generic `@generated`
> sentinel (native-comment-syntax registry); OQ5 = first-party predicate; plus
> OQ2 = cover each repo's own hooks, exempt the `templates/**` copier payload.
>
> **RIPE NEXT ACTION — drive the Phase-0 mechanism PR** (tracked as child
> `livespec-fa3eu5`: MAINTAINER-DRIVEN host-side `livespec-dev-tooling` PR, WARN
> severity — do NOT auto-dispatch to the factory). Read `bd show livespec-fa3eu5`
> and `research/check-inventory.md` for the full deliverable list. In brief:
> - Add a git-index-derived `iter_first_party_py_files(*, repo_root)` (shells
>   `git ls-files '*.py'` minus the exemptions); keep `iter_py_files(root=...)`
>   for role-scoped per-tree walks.
> - Add the generic `@generated` sentinel primitive (native-comment-syntax
>   registry) and the empty-walk guard (fail closed on non-empty-but-saw-zero;
>   pass on the genuinely-empty console repo).
> - Route the 13 applies-to-all checks through the git-derived universe (drop
>   `file_lloc`'s `_COVERED_TREES`; reroute the 6 raw-`rglob` checks); add the
>   partition-completeness meta-check; role-scoped checks keep config + gain it.
> - Exemptions: `_vendor/` + test tree (+conftest) + `@generated`-marked +
>   `templates/**`. Own hooks ARE covered. ALL new/changed diagnostics WARN
>   (exit 0) this phase.
> - Release + fan-out: cut a `livespec-dev-tooling` release; `bump-pin` rewrites
>   every consumer's pin AND reconciles each consumer's `check:` canonical block.
> - Confirm LIVE: `livespec-orchestrator-beads-fabro` now WARNS on `dispatcher.py`
>   (2,616 lines) + siblings; `livespec-console-beads-fabro` PASSES on empty; the
>   Driver hooks are covered; `just check` stays exit 0 fleet-wide.
>
> **Then Phase 1** — the per-repo burndown, in parallel through the factory
> (over-ceiling refactors, other check findings, claim/exempt unclaimed files).
> `groom` the epic into one ready track per repo. NOTE: do NOT link a child to the
> epic via `depends_on` — an OPEN-epic edge perpetually blocks the child
> (`lifecycle._entry_blocks`); narrate epic membership in the description and
> reserve `depends_on` for genuine cross-item blockers.
>
> **Then Phase 2** — flip warn→fail per repo the moment it is warning-clean, after
> an independent adversarial review (companion prompt) returns NO-BLOCKERS. The
> flip is severity only — NO new escape hatch (`.ai/ci-gate-discipline.md`). The
> flip mechanism itself (env lever vs committed marker) is still-open OQ3.
>
> Do NOT archive this thread until every in-scope repo is warning-clean AND
> flipped to hard-fail, and the maintainer explicitly accepts archival.
