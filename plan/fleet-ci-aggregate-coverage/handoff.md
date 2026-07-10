# fleet-ci-aggregate-coverage — handoff

**Epic anchor:** `livespec-cf4bcu` (core tenant, `type=epic`, `status=backlog`)
**Opened:** 2026-07-10
**Status:** open — **wiring rule DECIDED 2026-07-10** (single all-green
gate job); reference pattern + both quick wins LANDED (slices 2–4 DONE,
2026-07-10); drift-guard + large tracks + codify remain. See "Progress"
below.

## Progress (2026-07-10)

| Slice | Repo | State | PR / evidence |
|---|---|---|---|
| Decision recorded | livespec (core) | ✅ DONE | PR #1005 (merged) |
| 2. Reference `ci-green` pattern | livespec-driver-claude | ✅ DONE | PR #116 merged; `ci-green` green on master; branch protection now requires only `ci-green` |
| 3. Quick win | livespec-console-beads-fabro | ✅ DONE | PR #137 merged; matrix += `check-plugin-resolution`; `ci-green` added + required; `ci-green.needs = [check, check-doctor-static]` |
| 4. Quick win | livespec-driver-codex | ✅ DONE | PR #95 merged; matrix += `check-plugin-resolution`; `ci-green` added + required; `ci-green.needs = [check, check-doctor-static, red-green-replay]` |
| 1. Drift-guard impl | livespec-dev-tooling | ⬜ not started | foundational; heaviest (product Python + TDD) |
| 5. Large tracks | runtime, core, orch-beads-fabro, orch-git-jsonl, dev-tooling | ⬜ not started | each: complete matrix + `ci-green` + arm guard + flip protection |
| 6. Codify rule | fleet NFR | ⬜ not started | coordinate w/ runtime PR #161 |

**Validated on driver-claude:** `ci-green` runs, passes, correctly
ignores the skipped push-only `export-telemetry` job (not in its
`needs`), and GitHub accepts `ci-green` as the sole required merge-gate
context. The three landed non-core repos each now require ONLY `ci-green`
(replacing their prior per-check required sets: driver-claude 4 contexts,
driver-codex 6, console 9).

**Per-repo `ci-green.needs` recipe (confirmed non-uniform).** List the
`check` matrix job plus every dedicated check-bearing top-level job, and
EXCLUDE telemetry/auto-merge jobs. Job names differ across repos —
driver-codex's replay job is `red-green-replay` (NOT
`check-red-green-replay`); console (Rust) has no replay job. So the
drift-guard (slice 1) must read each repo's real ci.yml, not assume a
uniform job set.

## Thesis

Every livespec-Python-governed repo's CI must **provably run the full
`just check` canonical aggregate** — either by invoking the aggregate,
or via a per-target matrix that a drift guard proves is a **superset**
of the canonical block — and must **block merges on all of it** via a
single all-green gate job (see "Decision" below). Today most repos run a
per-target CI matrix that covers only a *subset* of what `just check`
runs locally, so many canonical checks run at pre-push but **never in
CI**.

## Root cause (why this seam is orphaned)

- **`livespec-univck` (DONE)** — "Universal-check propagation + wiring
  completeness." Added `check-aggregate-completeness`, which proves the
  *justfile* aggregate wires every canonical slug. It never proved that
  *CI* mirrors the aggregate.
- **`livespec-fgqgnk` (DONE)** — "Extract livespec-dev-tooling as a
  sibling library." Its `ci.yml`-cited follow-up — "Phase G.4 migrates
  checks into `<repo>/checks/`; add the corresponding `check-<slug>`
  target to the CI matrix and to branch protection" — was never carried
  forward. Four repos' `ci.yml` headers still point at this closed epic.

The gap between "the aggregate wires every check" (univck, proven) and
"CI runs every check the aggregate wires" (unproven, unenforced) is the
uncovered seam this epic closes.

## Audit (2026-07-10)

Coverage gap = canonical slugs that `just check` runs locally but that
CI never runs. All Python repos run a per-target matrix; none invokes
`just check` as a single command (only `dolt-server` does — a trivial
shell repo, one `shellcheck`).

| Repo | Gap (slugs in aggregate, absent from CI) | Track |
|---|---|---|
| livespec-dev-tooling | ~48 (bootstrap-ordered; checks come online as migrated) | large |
| livespec-orchestrator-beads-fabro | ~40 ("starter scaffold" comment) | large |
| livespec-orchestrator-git-jsonl | ~35+ ("starter scaffold") | large |
| livespec-runtime | ~35 | large |
| livespec (core) | ~27 | medium |
| livespec-console-beads-fabro | **1** (`check-plugin-resolution`) | quick win |
| livespec-driver-codex | **1** (`check-plugin-resolution`) | quick win |
| livespec-driver-claude | **0** matrix-gap — matrix reference impl | **reference impl** |
| dolt-server | n/a (shell; single `shellcheck` aggregate) | n/a |

Method note: figures are per-repo comparisons of the justfile `check:`
aggregate `targets=(...)` block against the CI matrix entries; the large
tracks carry explicit "starter scaffold … add the corresponding
`check-<slug>` targets" comments in their `ci.yml`. Verified live
2026-07-10 for the two quick wins (each = exactly `check-plugin-resolution`)
and for driver-claude (matrix runs all 8 aggregate checks).

## Decision (2026-07-10) — wiring rule: single all-green gate job

"Done" for a repo = **CI provably runs the full aggregate AND blocks
merges on all of it**, realized via a **single all-green gate job**
(maintainer-chosen 2026-07-10 over per-check required contexts, which
are brittle: N context-names that deadlock master merges on any target
rename and live out-of-band from git — no PR, no history). Concretely,
each repo:

1. **Matrix ⊇ aggregate.** Every canonical `just check` target runs in
   CI — in the `check` matrix, or as a dedicated job (the pattern
   `check-doctor-static` / `check-red-green-replay` already use for
   targets that need a second checkout or full history).
2. **One all-green gate job.** A summary job `needs:` every
   check-bearing job and fails if any dependency failed or was
   cancelled — a pure GitHub-expression gate, no external action, no
   direct tool invocation (so it satisfies NFR §"Toolchain pins"):

   ```yaml
   ci-green:
     name: ci-green
     needs: [check, check-doctor-static, check-red-green-replay]
     if: always()
     runs-on: ubuntu-latest
     steps:
       - name: All required checks passed
         if: ${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}
         run: exit 1
   ```

3. **Branch protection requires only `ci-green`.** One stable
   context-name blocks merges on the entire matrix and never churns as
   checks are added — so no per-check protection edits ever again. The
   old curated per-check required contexts are replaced by `ci-green`
   (flip protection AFTER the PR that adds `ci-green` merges, so the
   context has reported on a real run and cannot deadlock PRs).
4. **Drift guard (shared, dev-tooling).** A new check in
   `livespec-dev-tooling` (sibling to `check-aggregate-completeness`)
   asserts, from **committed files only**, that the CI `check` matrix +
   dedicated check jobs are a **superset of the justfile aggregate**,
   and that `ci-green.needs` covers every check-bearing job. A canonical
   slug that runs locally but not in CI then FAILS CI. Branch-protection
   membership stays out-of-band — but `ci-green` is a single stable
   context set ONCE per repo, so it carries no drift risk the guard
   needs to police.

## Reference-impl finding (2026-07-10)

Under this rule **no repo is currently at target** — including the
"0-gap" reference `livespec-driver-claude`. It runs all 8 aggregate
checks across matrix + dedicated jobs (so it IS the matrix-coverage
reference), BUT its `export-telemetry` job
(`needs: [check, check-red-green-replay]`, `if: !cancelled()`) is a
telemetry exporter, **not** an all-green gate, and its branch protection
requires 4 individual contexts (`check-plugin-structure`, `check-lint`,
`check-format`, `check-e2e-cli`), not a gate job. So every repo
(driver-claude included) needs a NEW `ci-green` gate job + a
branch-protection flip. Branch-protection required-sets are non-uniform
today: console requires all 9 of its matrix entries; driver-codex 6 of
7; driver-claude 4 of 7 — the gate-job rule normalizes all of them to a
single `ci-green`.

## Scope boundary (what this epic is NOT)

- **Not `fleet-check-coverage` (`livespec-i5ebqd`).** That epic is
  hygiene-WARN burndown + per-repo severity flip; it *"deliberately does
  not edit CI matrices"* (PR #296). Confirmed distinct.
- **Absorbs** the orphaned `livespec-fgqgnk` Phase-G.4 CI-wiring intent.
- Not a change to *which* checks exist or their severity — purely
  whether CI *runs* the checks the aggregate already defines and *gates*
  merges on them.

## Groomed slices (2026-07-10 — not yet filed)

Per the sibling-repo tenanting model, per-repo slices live in **each
repo's own beads tenant**; epic `livespec-cf4bcu` (core tenant) is the
hub anchor and coordination point.

**Ordering invariants.**
- The drift guard is landed in dev-tooling FIRST, but each repo arms it
  in its `just check` aggregate only in the SAME PR that completes its
  matrix + `ci-green` job, so `just check` stays green throughout.
- Per-repo PRs merge FIRST (the `ci-green` context must report on a real
  run), THEN branch protection is flipped to require `ci-green`.
- Slices 1 (guard) and 2 (reference pattern) are foundational — do them
  first / in parallel; everything else copies slice 2's `ci-green` shape.

1. **Drift-guard impl** (`livespec-dev-tooling` tenant) — add the
   matrix-⊇-aggregate + `ci-green.needs`-completeness check to the
   shared check package, with a warn-vs-fail env lever so it can land
   before every repo is wired. Ships the check; does NOT yet arm it in
   sibling aggregates. **Full self-sufficient implementation brief for a
   clean session: see "Next session — drift-guard (slice 1) implementation
   brief" below.**
2. **Reference `ci-green` pattern** (`livespec-driver-claude` tenant) —
   add the `ci-green` job + flip branch protection to require it. Lowest
   matrix-gap repo, so it isolates the gate-job change; becomes the
   copy-source for every other repo.
3. **Quick win: console** (`livespec-console-beads-fabro` tenant) —
   matrix += `check-plugin-resolution`; add `ci-green`; require `ci-green`.
4. **Quick win: driver-codex** (`livespec-driver-codex` tenant) —
   matrix += `check-plugin-resolution`; add `ci-green`; require `ci-green`.
5. **Large tracks** — runtime (~35), core (~27),
   orchestrator-beads-fabro (~40), orchestrator-git-jsonl (~35),
   dev-tooling (~48). Each: complete the matrix, add `ci-green`, arm the
   drift-guard in the aggregate, flip protection. Groom each per repo.
6. **Codify the rule** — record the single-all-green-gate-job CI
   convention as a fleet contract (propose-change → revise on the
   relevant NFR), so it is a contract, not just working notes. Coordinate
   with runtime PR #161's pending clause alignment.

## Next session — drift-guard (slice 1) implementation brief

Self-sufficient brief to implement slice 1 in a **clean session**. All
paths verified live 2026-07-10. The check is a normal
change-verifying check (it inspects one repo's own committed CI config),
so the fleet's warn-vs-fail severity-lever convention APPLIES (it is not
a world-gate like `check-master-ci-green`).

### Goal

One new self-contained check module in the shared `livespec-dev-tooling`
package that, from a repo's **own committed files only**, asserts:

- **(a) CI runs the whole aggregate:** the set of canonical slugs CI
  runs (matrix `target:` list ∪ dedicated check-bearing jobs) is a
  **superset of** the justfile `check:` aggregate `targets=(...)`.
- **(b) `ci-green` gates the whole aggregate:** a `ci-green` job exists
  and its `needs:` lists **every check-bearing job** (so requiring only
  `ci-green` blocks merges on everything).

Naming to follow the sibling: module
`livespec_dev_tooling/checks/ci_matrix_completeness.py` → slug
`check-ci-matrix-completeness` (adjust the noun if a better one fits;
keep `check-` prefix).

### Patterns to mirror (do NOT invent; copy these — the package
convention is self-contained modules that each duplicate small regex
parsers rather than share one; see `livespec_dev_tooling/checks/CLAUDE.md`)

- **justfile aggregate parser + local structlog emitters + exit codes +
  hermetic override** → `livespec_dev_tooling/checks/aggregate_completeness.py`
  (+ test `tests/livespec_dev_tooling/checks/test_aggregate_completeness.py`).
  Reuse its 3-regex idiom (`^check:\s*$` header → `targets=(` … `)` block
  → keep `check-`-prefixed tokens), its `structlog`-JSON-to-stderr local
  `_emit_*` functions (records carry `check_id`/`failure_mode`/`status`),
  its exit codes (0 pass, 4 violation, 2 usage error), and its
  `--canonical-from <json>` override (`{"slugs":[...]}`) used ONLY for
  hermetic tests.
- **ci.yml matrix parser** → `livespec_dev_tooling/checks/tool_backed_check_completeness.py`
  (`_parse_ci_matrix_targets`, `_collect_ci_matrix_targets` — globs
  `*.yml`+`*.yaml`) and `branch_protection_alignment.py` (`_parse_ci_matrix`).
  3-regex idiom: `^\s*matrix:\s*$` → `^\s*target:\s*$` → `^\s*-\s*([\w-]+)\s*$`.
- **warn-vs-fail severity lever** → `no_todo_registry.py` /
  `no_lloc_soft_warnings.py`: env var `LIVESPEC_FAIL_IF_<CONDITION>_EXIST`
  (e.g. `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST`); the scan ALWAYS runs
  (no skip carve-out — the old `LIVESPEC_RELEASE_GATE` skip design is
  explicitly rejected in those docstrings); `fail = bool(os.environ.get(_ENV))`;
  `emit = log.error if fail else log.warning`; `return 1 if fail else 0`.
  Do NOT copy `check_mutation.py`'s `LIVESPEC_RUN_MUTATION` or
  `plugin_resolution.py`'s `LIVESPEC_E2E_HARNESS` — those are mode
  selectors, not severity levers.
- **test layout** → mirror `tests/livespec_dev_tooling/checks/test_tool_backed_check_completeness.py`:
  outside-in subprocess tests (`_run_check(*, cwd, extra_argv)` shells
  `python <module>` in `tmp_path`), fixture builders that write a
  synthetic `justfile` and `.github/workflows/ci.yml`
  (`_write_ci_workflow(*, cwd, matrix_targets, name="ci.yml")`), a
  `--…-from` JSON override to keep the canonical set hermetic, and
  assertions that parse the structlog JSON from `result.stderr` and check
  `finding["failure_mode"]`.

### The NOVEL work (beyond the mirrored parsers)

The existing parsers only read `matrix.target`. This check additionally
needs to (1) enumerate **top-level jobs** and their `needs:` lists, and
(2) decide which jobs are **check-bearing**. Recommended robust approach
(name-matching is fragile — driver-codex's replay job is
`red-green-replay`, NOT `check-red-green-replay`; console has no replay
job at all):

- **CI-covered slug set** = for the `check` matrix job, its `target:`
  list; PLUS, for every other top-level job, any canonical `check-<slug>`
  it runs — detect by scanning that job's `run:` lines for
  `just <canonical-slug>` (the matrix leg is `just ${{ matrix.target }}`).
  A job is **check-bearing** iff it contributes ≥1 canonical slug this
  way. Telemetry/export/`enable-auto-merge` jobs contribute none and are
  thus excluded automatically — no hardcoded exclude-list needed.
- Assert (a): CI-covered slug set ⊇ justfile aggregate.
- Assert (b): a job named `ci-green` exists and its `needs:` ⊇ the set of
  check-bearing job names.

### Registration + fleet-wide propagation — READ BEFORE SHIPPING

`livespec_dev_tooling/canonical_checks.py::canonical_check_slugs()` is
computed **dynamically** by `pkgutil.iter_modules` over `checks/`
(filename → `check-kebab` slug). So **merely dropping the new module
makes `check-ci-matrix-completeness` a canonical slug** — no registry
edit. Consequence: on the next dev-tooling release, the new slug
propagates to every repo (core `just stamp-canonical-slugs` → template
release → `copier update` per consumer + hand-add to non-templated
repos), and **`check-aggregate-completeness` will then FAIL any repo
whose justfile aggregate lacks the new slug** — this is the SAME
propagation hazard that reddened master on the v0.36.0 bump (see
`livespec-y9lb`).

**Two implications the clean session MUST honor:**

1. **Fix `livespec-y9lb` FIRST (or in lockstep).** That P1 makes the
   bump-pin fan-out auto-run `just stamp-canonical-slugs`, so the new
   canonical slug lands in each repo's aggregate cleanly instead of
   reddening it. Shipping this check before y9lb repeats the v0.36.0
   breakage.
2. **Ship warn-DEFAULT.** With the lever unset by default, when the slug
   propagates to a not-yet-wired repo the check WARNS about that repo's
   own CI gaps without reddening it. Each repo then flips to fail in its
   own wiring PR (below). This is what makes propagation safe.
3. **VERIFY (open question):** confirm how each repo gets the
   `check-ci-matrix-completeness:` **recipe body** (delegating to the
   module), not just the aggregate `targets=(...)` entry — is the recipe
   body generated by `templates/orchestrator-plugin/justfile.jinja`, or
   hand-added per repo? Resolve before rollout; a slug in the aggregate
   with no recipe body breaks `just check`.

### Rollout ordering

1. (Pre-req) fix `livespec-y9lb` so bump-pin auto-stamps.
2. Ship `ci_matrix_completeness.py` warn-default in dev-tooling via the
   TDD red-green-replay ritual (new-module stub technique: at Red, a stub
   that makes the one staged test's assertion FAIL — not merely
   unimportable; stage exactly ONE test file at Red, the rest + impl at
   the Green `--amend`).
3. Let it propagate (warns fleet-wide, reddens nothing).
4. Each large-track repo's wiring PR (slice 5) completes its matrix +
   `ci-green`, then sets `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST=true` for
   this check's CI job → flips it to fail for that repo.
5. Once every repo is wired, optionally flip the module default to fail
   (and drop the now-uniform per-repo env), or leave the self-documenting
   per-repo env in place.

### Standing constraints (both confirmed this epic)

- **CI-wiring stays maintainer-side.** The fleet App (`livespec-pr-bot`)
  deliberately lacks `workflows` permission, so factory-dispatched
  branches cannot touch `.github/workflows/`. Every `ci.yml`/gate edit in
  this epic must be pushed with maintainer credentials (worktree → PR),
  never via the factory. (See `.ai/ci-gate-discipline.md`.)
- **`ci-green.needs` is non-uniform per repo** — parse each repo's real
  `ci.yml`; never assume a uniform job set.

### Definition-of-Ready / acceptance for slice 1

- New check module + mirrored test land in `livespec-dev-tooling` via the
  red-green-replay ritual; `just check` green there.
- The check, run against a synthetic repo whose matrix omits an aggregate
  slug, reports finding (a); against one whose `ci-green.needs` omits a
  check-bearing job, reports (b); against a fully-wired repo, exits 0.
- Warn-default verified: unset lever → warning + exit 0; lever set → error
  + exit non-zero, same findings.
- Clean session's FIRST action: file the slice-1 work-item in the
  **`livespec-dev-tooling` tenant** (epic `livespec-cf4bcu` is the
  cross-tenant hub), then implement.

## Related work

- **livespec-runtime PR #161** (MERGED 2026-07-10) — propose-change
  `ci-invocation-clause-align-fleet-matrix`: revised runtime's NFR
  §"Task-runner discipline" clause (the sole fleet outlier that mandated
  CI invoke `just check`) to bless the completeness-guarded per-target
  matrix. Pending `/livespec:revise` ratification. Resolved gap
  `gap-rsfmjjzl` (runtime work-item `livespec-runtime-woe5gi`). Slice 6
  (codify the gate-job rule) should land alongside/after this revise so
  the NFR describes the final gate-job shape.
- Reference for the per-target matrix convention: livespec core
  `SPECIFICATION/contracts.md` §"Pre-commit step ordering" (zero-`.py`
  subsetting), which prescribes the matrix shape this epic completes.
- **`livespec-y9lb`** (core tenant, P1 bug, filed 2026-07-10) — bump-pin
  fan-out must re-stamp `canonical-slugs.yml` on slug-adding dev-tooling
  bumps. Discovered mid-session when the v0.36.0 pin bump reddened master
  (repaired via livespec PR #1008). NOT part of this epic, but a **hard
  pre-req for shipping the drift-guard** (slice 1): a new canonical slug
  propagates cleanly only once bump-pin auto-stamps. See the slice-1
  brief above.
