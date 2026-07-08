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
  restates core's `livespec/` paths verbatim). Read BOTH research docs before
  acting:
  - `plan/fleet-check-coverage/research/root-cause.md` — why the allowlist model
    fails open, with reproduce commands.
  - `plan/fleet-check-coverage/research/design.md` — the target
    (filesystem-derived universe via `git ls-files`, fail-closed empty guard,
    partition-completeness meta-check), the exemption policy (`_vendor/` + tests +
    generated code), the three-phase rollout, and the open questions.
- **Companion adversarial prompt.**
  `plan/fleet-check-coverage/live-adversarial-review-prompt.md` — hand this to an
  independent reviewer session; a NO-BLOCKERS verdict is a precondition for
  accepting any Phase-2 flip.
- **No epic yet (deliberate).** This thread was authored plan-first; the ledger
  epic is intentionally NOT created. Anchoring it is the FIRST action below.
  Until then there is no ledger status to read and none is stored here.
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
| `livespec-console-beads-fabro` | operator console app | likely same hidden backlog class |
| `livespec-orchestrator-git-jsonl` | orchestrator | real coverage; verify |
| `livespec-runtime` | library | real coverage; verify |
| `livespec-driver-claude` | thin runtime binding | may be genuinely codeless → empty-walk guard MUST pass, not error |
| `livespec-driver-codex` | thin runtime binding | same as above |

The empty-walk guard's correctness on the (near-)codeless Driver repos is a
first-class acceptance case, not an afterthought — see the adversarial prompt.

## The next action

> **Phase 0 — mechanism, warn-only. Start here.**
>
> 1. **Anchor the epic.** File via the `capture-work-item` operation an `epic`
>    titled *"fleet-check-coverage: filesystem-derived structural-check coverage
>    across the fleet (staged warn → burndown → fail)"*. Then file the Phase-0
>    child items below as its children (`depends_on` the epic, typed-dict form).
> 2. **Enumerate + classify the check set.** In `livespec-dev-tooling`, list
>    `checks/*.py` and classify each: *applies-to-all* (derive its universe from
>    `git ls-files '*.py'` minus exemptions) vs *role-scoped* (keep semantic
>    config, gain the partition guard). This classification is Phase 0's first
>    real artifact.
> 3. **Resolve the two blocking open questions** (design.md): the "generated
>    code" marker, and the empty-walk guard's "first-party `.py`" predicate that
>    distinguishes a codeless Driver repo (pass) from a mis-config (fail). These
>    two gate the mechanism; the others (flip mechanism, test-ceiling) can wait.
> 4. **Implement, WARN severity only.** Route `file_lloc` (drop its hardcoded
>    `_COVERED_TREES`) and every applies-to-all check through the shared
>    filesystem-derived `iter_py_files`; add the empty-walk guard and the
>    partition-completeness meta-check. All new/changed diagnostics emit at
>    `warning` (exit 0) this phase.
> 5. **Release + fan-out.** Cut a `livespec-dev-tooling` release; let `bump-pin`
>    rewrite every consumer's pin AND reconcile each consumer's `check:` canonical
>    block (wiring, not just availability).
> 6. **Confirm the fanned-out state:** every repo with product `.py` now WARNS
>    and its true coverage is visible (dispatcher.py et al. appear); every
>    codeless Driver repo PASSES on an empty universe without erroring.
>
> **Then Phase 1** — dispatch the per-repo burndown in parallel through the
> factory (over-ceiling refactors, other check findings, claim/exempt unclaimed
> files); one child track per repo under the epic.
>
> **Then Phase 2** — flip warn→fail per repo the moment it is warning-clean,
> after an independent adversarial review (companion prompt) returns NO-BLOCKERS.
>
> Do NOT archive this thread until every in-scope repo is warning-clean AND
> flipped to hard-fail, and the maintainer explicitly accepts archival.
