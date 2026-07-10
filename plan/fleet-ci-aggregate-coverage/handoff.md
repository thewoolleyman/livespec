# fleet-ci-aggregate-coverage — handoff

**Epic anchor:** `livespec-cf4bcu` (core tenant, `type=epic`, `status=backlog`)
**Opened:** 2026-07-10
**Status:** open — **wiring rule DECIDED 2026-07-10** (single all-green
gate job); reference-impl re-audited; slices groomed below, not yet filed.

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
   sibling aggregates.
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
