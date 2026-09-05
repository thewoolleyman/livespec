# 003 — Independent verification of the 2026-09-05 state flush, with corrections and the findings it produced

Recorded 2026-09-05 by the `pr-gate-master-parity` plan session running on
the Fable 5.1 model, executing the single next action the 2026-09-05T03:14Z
handoff named: re-derive sections A–D of that handoff from the forge and from
every fleet repository's `origin/master`, not from the handoff text itself.
Every claim below was read from a `git show origin/master:<path>` in the
named repository, from a GitHub API response, or from a file in the
livespec-dev-tooling package on `origin/master`; nothing was taken from the
handoff on trust.

## Plain-language bottom line

The plan's core claims hold. The specification change is ratified as v217 and
says what the handoff says it says; the `ci_gate_parity` check exists and
does what the handoff describes; five of the six carrier repositories have the
zero-`.py` skip removed and the new check wired and armed on `origin/master`;
the sixth (livespec-orchestrator-beads-fabro) is built and verified on an
unpushed branch that still needs the maintainer's own push. Two handoff claims
were wrong and are corrected here: the cause of livespec-runtime's missing
fan-out (it was excluded by the conformance preflight, not by a hardcoded
target list), and the location of the hook that blocks an agent's
`--no-verify` (it is the fleet-shipped per-repository hook, not a file under
the home directory). The verification also produced one new finding: the
ratified clause promises detection of event-conditioned gating jobs that the
shipped check does not implement. All four follow-ups are now filed in the
livespec-dev-tooling ledger; their identifiers are in §"Filed follow-ups".

## What was verified, per handoff section

### A — the done work

| Requirement | Handoff claim | Verified how | Result |
|---|---|---|---|
| R1 spec | v217 ratifies PR gate ≡ master gate | `diff` of `history/v216/` against `history/v217/` for `contracts.md` and `non-functional-requirements.md` in livespec | Holds. `contracts.md` §"Pre-commit step ordering" keeps the pre-commit doc-only subset as a non-gate local optimisation, deletes the v050 clauses (a)–(d) and the false "soundness" paragraph, and states the invariant; the detection-surface sentence at line 164 was swept. `non-functional-requirements.md` gains the **PR gate ≡ master gate** paragraph under §"CI as a merge gate (branch protection)" and sweeps the `comment_no_historical_refs` enforcement sentence. No `## ` heading changed. |
| R2 check | `ci_gate_parity` in livespec-dev-tooling v1.43.0 | `git show origin/master:livespec_dev_tooling/checks/ci_gate_parity.py` and `_ci_matrix_parse.py` in livespec-dev-tooling | Holds, with the caveat in §"D5". Gating job = a job in `ci-green.needs`; finding = such a job whose job- or step-level `if:` matches `\bpy_changed\b`; warn by default, exit 4 under `LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST`; graceful on a missing workflow or a missing gate job. |
| R3 carriers | five of six retired, wired, armed | For each repository, grep of `origin/master:.github/workflows/ci.yml` excluding comment lines, plus the `check-pre-push` recipe | Holds for livespec, livespec-dev-tooling, livespec-orchestrator-git-jsonl, livespec-runtime, livespec-overseer: no live `py_changed` or `detect-py-changes` (the remaining mentions are explanatory comments), `check-ci-gate-parity` exactly once inside `check-metadata-batch` adjacent to `check-ci-matrix-completeness`, the lever set to `"true"` in that step's `env:`, and pre-push delegating to the full `just check` behind the green-token memoisation only. |
| R4 template | copier template retired the skip | `git log` of livespec #2562 | Holds. |
| R5 measurement | full aggregate on a config-only PR ran green in about three minutes | livespec run 33910137349 | Holds as recorded. |

### B — the unlanded piece

Branch `ci-gate-master-parity` in the livespec-orchestrator-beads-fabro
worktree `~/.worktrees/livespec-orchestrator-beads-fabro/ci-gate-master-parity`
is at commit c0c72f11, exactly one commit ahead of the current `origin/master`
tip 2fda6bee (so no rebase is needed), clean, and not on the forge (no
`origin/ci-gate-master-parity`, no PR). Its diff is three files: `ci.yml`
(the `setup`/`detect-py-changes` job and every `py_changed` condition
removed, the lever armed, the slug added to `check-metadata-batch`),
`dev-tooling/just-check-pre-push.sh` (the zero-`.py` branch deleted), and the
justfile comments. This is the described change and nothing else. It still
needs the maintainer's own `git push --no-verify -u origin ci-gate-master-parity`
from that worktree; the repository's hard workflow-edit guard and the
fleet-shipped footgun hook together make that push human-only by design.

### C — the maintainer's decisions

Unchanged; they are instructions, not claims, so there is nothing to
re-derive. The recommendation recorded under C.5 was re-examined rather than
accepted; the result is §"D1" below.

### D — the findings, re-derived

#### D1 — the workflow-edit guard is one rule with eight implementations

The handoff's table was broadly right and its framing was incomplete. The
verified table (every member defines a `check-no-workflow-edits` recipe):

| Member | Implementation | In the `check` aggregate | Runs in CI | Agent-settable escape |
|---|---|---|---|---|
| livespec-orchestrator-beads-fabro | `workflow_guard.py` via `_dispatcher_workflow_guard.py` | yes | no | none |
| livespec-overseer | `scripts/check-no-workflow-edits.sh` | yes | yes (`check-metadata-batch`) | a self-authored tracked `.livespec-workflow-edit-exemption` declaration, plus a mechanical allowance for pin and reconciler lines |
| livespec | inline justfile recipe | no | no | none |
| livespec-dev-tooling | `scripts/just/check-no-workflow-edits.sh` (the reference copy no consumer uses) | no | no | none |
| livespec-driver-claude | `dev-tooling/just/check-no-workflow-edits.sh` | no | no | none |
| livespec-driver-codex | `dev-tooling/check-no-workflow-edits.sh` | no | no | `LIVESPEC_FACTORY_BASE_REF` base-ref override |
| livespec-driver-pi | `dev-tooling/check-no-workflow-edits.sh` | no | no | `LIVESPEC_FACTORY_BASE_REF` base-ref override |
| livespec-orchestrator-git-jsonl | `dev-tooling/just-check-no-workflow-edits.sh` | no | no | `LIVESPEC_WORKFLOW_EDIT_BASE` base-ref override |
| livespec-runtime | `.github/scripts/no-workflow-edits.sh` | no | no | none |
| livespec-console-beads-fabro | inline justfile recipe | no | no | none |

Two facts the handoff did not have, which change the recommendation:

1. **The factory path is already uniform.** The Dispatcher's host-janitor
   check suite (`JANITOR_CHECK_SUITE_DEFAULT` in
   livespec-orchestrator-beads-fabro's `_dispatcher_integration_defaults.py`)
   invokes `check-no-workflow-edits` explicitly, ahead of `check`, in every
   governed repository. A Dispatcher-driven implementation therefore cannot
   publish a workflow edit anywhere. The non-uniform layer is the LOCAL
   pre-push aggregate, which only matters for a session-dispatched agent
   pushing from a worktree — which is exactly how the five landed carrier
   PRs went through. The handoff's sentence "livespec (core): in aggregate
   yet the ci.yml PRs landed (has some escape — unverified)" is resolved:
   livespec's guard is simply NOT in its aggregate, so there was no escape
   to find.
2. **The escapes exist because one repository runs the guard in CI.**
   livespec-overseer is the only member that runs the guard in CI, and the
   fleet's bot lanes (pin bumps, the canonical-slug reconciler,
   release-please) legitimately rewrite workflow files, so overseer needed a
   declaration and a mechanical allowance to keep its bump lane green.
   Removing the guard from CI removes the need for both escapes. The base-ref
   overrides in the two drivers and git-jsonl exist for adopters whose
   default branch is `main`; livespec-orchestrator-beads-fabro already solved
   that with the shared default-branch resolution rule and no override.

The refined recommendation, recorded on `livespec-dev-tooling-fy02`: one
shared hard-block body shipped from livespec-dev-tooling as a carrier
constant with a byte-identity check (the pattern the commit-refuse hooks and
the neutral no-shadow-ledger body already use); wired into every member's
`check` aggregate; base ref from the shared default-branch rule; no env
override and no declaration file; NOT run in CI and therefore NOT a canonical
CI slug; one documented human landing path (the maintainer's own
`git push --no-verify`, which the fleet-shipped footgun hook denies to every
agent). The docstring must say plainly that this is an authorship control at
the agent boundary, not a master-safety gate: master is protected by PR gate
≡ master gate, which this guard neither weakens nor strengthens.

Correction to the handoff: the hook that blocked the previous session's
`--no-verify` attempt is the fleet-shipped per-repository
`.claude/hooks/livespec_footgun_guard.py` (eight copies, tracked as
`livespec-dev-tooling-qv3k`), not a file under `~/.claude/hooks/` — the copy
there is a `.bak` and is not wired into the user's settings.

#### D2 — the reconciler's mis-placement, root-caused

Confirmed live on `origin/master` in all three drivers: the v1.43.0 bump put
`just check-ci-gate-parity || failed="$failed check-ci-gate-parity"` inside
the `check-per-file-coverage` job's run step (livespec-driver-claude
ci.yml:322, livespec-driver-codex ci.yml:422, livespec-driver-pi
ci.yml:378), where `$failed` is never read, and left the lever unarmed. The
five carrier PRs corrected this by hand; the drivers had not been touched.

Root cause, read in livespec-dev-tooling
`livespec_dev_tooling/cross_repo/_ci_yaml_reconcile_parse.py` on
`origin/master`: `_BATCH_RUN` (line 74) matches every `just check-<slug>`
line in the whole file, so single-target job steps count as "batch entries";
`batch_insert_index` (line 250) then inserts before the first existing
canonical entry, in FILE order, whose slug sorts after the new one.
`check-per-file-coverage` is canonical, sorts after `check-ci-gate-parity`,
and appears in the file before the metadata batch — so that job's own run
step becomes the insertion point. Any future slug sorting before
`check-per-file-coverage` will be misplaced the same way in every consumer.
Filed as `livespec-dev-tooling-qknd` (P1). The three driver repositories are
being corrected and armed by three parallel PRs opened from this session
(§"Driver consistency PRs").

#### D3 — corrected: runtime was excluded by the preflight, not omitted from a list

The handoff said the release fan-out "omits livespec-runtime (a fleet gap)".
That is not what happened. `reusable-release-dispatch.yml` reads the fleet
manifest from livespec master (livespec-runtime is in it) and then applies a
per-member fleet-conformance preflight filter. On the v1.43.0 run
(33911246882) that filter annotated two exclusions: livespec-runtime (failing
conformance row `cross-repo-public-api-declared`) and
livespec-console-beads-fabro (row `required-role-keys-declared`). Seven
members were dispatched and the run concluded success. The v1.43.1 run
(33918056143) excluded runtime again for the same reason. The filter is by
design; what is defective is that livespec's doctor-static
`wiring-completeness-cross-repo` check requires the excluded sibling to carry
the new slug anyway, so livespec's own bump PR (#2563) went red until the
previous session dispatched runtime by hand — a hand dispatch that bypassed
the preflight's verdict. Filed with the corrected cause and two remedies as
`livespec-dev-tooling-lfgk` (P2).

#### D4 — sub-agent stall pattern

Not a forge fact; carried forward as operating guidance. The three driver
PR briefs opened from this session instruct a foreground `just check` and
the two install recipes a fresh worktree needs.

#### D5 — new: the ratified clause overclaims the check

`non-functional-requirements.md` (v217) says `ci_gate_parity` "FAILS when a
gating job — at the job level or in its real steps — is conditioned on the
triggering event or on a changeset predicate in the FORBIDDEN DIRECTION".
The shipped check recognises only the literal `py_changed` token. A gating
job carrying `if: github.event_name != 'pull_request'` would pass it. No
fleet member has such a job today: the only event-conditioned jobs on any
`origin/master` are `export-telemetry` (push-only and absent from every
`ci-green.needs`, so non-gating) and livespec's `release-gate-pre-tag`
(pull-request-only, stricter). This is a spec-versus-guard gap, not an
incident. Filed as `livespec-dev-tooling-d99z` (P2) with the recommendation
to widen the check rather than narrow the clause.

## Fleet sweep, all fourteen manifest repositories, `origin/master` on 2026-09-05

| Repository | Live `py_changed` skip | `check-ci-gate-parity` placement | Lever armed | Note |
|---|---|---|---|---|
| livespec | none | `check-metadata-batch`, beside matrix-completeness | yes | carrier, done |
| livespec-dev-tooling | none | same | yes | carrier, done |
| livespec-orchestrator-git-jsonl | none | same | yes | carrier, done |
| livespec-runtime | none | same | yes | carrier, done |
| livespec-overseer | none | same | yes | carrier, done |
| livespec-orchestrator-beads-fabro | PRESENT (44 references) | mis-placed | no | carrier; fixed on the unpushed branch |
| livespec-driver-claude | none | mis-placed in `check-per-file-coverage` | no | PR in flight from this session |
| livespec-driver-codex | none | mis-placed in `check-per-file-coverage` | no | PR in flight from this session |
| livespec-driver-pi | none | mis-placed in `check-per-file-coverage` | no | PR in flight from this session |
| livespec-console-beads-fabro | none | not present | not applicable | Rust repository; carries no canonical dev-tooling slugs at all (`livespec-dev-tooling-739o`), so `ci_gate_parity` cannot reach it; its own `check-ci-parity` is a different check |
| dolt-server (adopter) | none | not present | not applicable | no aggregate gate (`livespec-dev-tooling-739o`) |
| homelab (adopter, `main`) | none | not present | not applicable | |
| resume (adopter) | none (`check.yml`) | not present | not applicable | |
| openbrain (adopter, `main`) | no CI check workflow | not present | not applicable | |

The scope event's deferral D1 (drivers untouched) is superseded in one narrow
respect by the maintainer's later instruction to make the `ci_gate_parity`
wiring consistent across all tenants: the drivers carry no skip and needed no
retirement, but they carry the mis-placed, unarmed slug, which the three
in-flight PRs correct. Deferral D2 (adopters and the console) stands.

## Driver consistency PRs

Three parallel sub-agents were dispatched from this session, one per driver
repository, each in its own fresh worktree on a branch named
`ci/ci-gate-parity-placement-arm`: move the slug into `check-metadata-batch`
after `check-ci-matrix-completeness`, arm
`LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST`, run the full gate in the
foreground, commit without `--no-verify`, open the PR with auto-merge, verify
on `origin/master`, remove the worktree. The drivers' workflow-edit guard is
not in their aggregate (table in §"D1"), so an agent push passes pre-push
there; the maintainer's approval for landing these CI changes fleet-wide
covers it. PR numbers are recorded on the plan epic's handoff timeline once
they exist.

## Filed follow-ups (livespec-dev-tooling ledger, 2026-09-05)

| Identifier | Finding | Priority |
|---|---|---|
| `livespec-dev-tooling-qknd` | D2 — reconciler mis-placement root cause and fix direction | P1 |
| `livespec-dev-tooling-d99z` | D5 — check under-enforces the ratified clause | P2 |
| `livespec-dev-tooling-fy02` | D1 — one shared hard-block workflow-edit guard, the verified table, the refined recommendation | P2 |
| `livespec-dev-tooling-lfgk` | D3 (corrected) — preflight-excluded sibling reddens livespec's cross-repo wiring check | P2 |

Two pre-existing dev-tooling items describe the hole this plan closed and
will be closed with this plan's evidence once the last carrier lands:
`livespec-dev-tooling-zi29` (P1, "a py-gated check job reports SUCCESS while
skipping the check itself" — its required positive control is the
livespec-orchestrator-beads-fabro pair run 33895801359 green / 33895911436
red, and its "measure what removing the optimisation costs" condition is R5)
and `livespec-dev-tooling-ozuv` (P1, "a release that WIDENS a check reaches
consumers as a zero-.py pin bump, so the widened check never runs on the
adopting PR" — resolved because a pin-bump PR now runs the full aggregate).

## Read-first chain

This note → the plan epic `livespec-citqsd` 2026-09-05T03:14Z state flush
(sections A–E) → `002-design-decision.md` → livespec
`SPECIFICATION/history/v217/` → livespec-dev-tooling
`livespec_dev_tooling/checks/ci_gate_parity.py` and
`cross_repo/_ci_yaml_reconcile_parse.py` (lines 74 and 250) →
livespec-orchestrator-beads-fabro `_dispatcher_integration_defaults.py`
(`JANITOR_CHECK_SUITE_DEFAULT`) → livespec-dev-tooling fan-out run
33911246882's preflight annotations → the four filed items above.
