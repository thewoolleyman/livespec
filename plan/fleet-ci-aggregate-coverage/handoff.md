# fleet-ci-aggregate-coverage — handoff

**Epic anchor:** `livespec-cf4bcu` (core tenant, `type=epic`, `status=backlog`)
**Opened:** 2026-07-10
**Status:** open — charter recorded; slices not yet groomed/filed.

## Thesis

Every livespec-Python-governed repo's CI must **provably run the full
`just check` canonical aggregate** — either by invoking the aggregate,
or via a per-target matrix that a drift guard proves is a **superset**
of the canonical block — with each newly-wired slug added to
branch-protection required checks. Today most repos run a per-target CI
matrix that covers only a *subset* of what `just check` runs locally, so
many canonical checks run at pre-push but **never in CI**.

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
| livespec-driver-claude | **0** — already complete | **reference impl** |
| dolt-server | n/a (shell; single `shellcheck` aggregate) | n/a |

Method note: figures are per-repo comparisons of the justfile `check:`
aggregate `targets=(...)` block against the CI matrix entries; the large
tracks carry explicit "starter scaffold … add the corresponding
`check-<slug>` targets" comments in their `ci.yml`.

## Mechanism

1. **Drift guard (shared).** Extend `check-aggregate-completeness` (or a
   sibling check) in `livespec-dev-tooling` to assert
   **CI-matrix ⊇ canonical aggregate** — a slug that runs locally but
   not in CI must **fail CI**. This is the enforcement that makes the
   remaining coverage self-closing (a new canonical slug that isn't
   CI-wired reddens CI until it is).
2. **Per-repo wiring.** Add the missing `check-<slug>` matrix entries +
   branch-protection required checks, using **driver-claude** as the
   pattern (it already runs the full aggregate as a matrix).

## Scope boundary (what this epic is NOT)

- **Not `fleet-check-coverage` (`livespec-i5ebqd`).** That epic is
  hygiene-WARN burndown + per-repo severity flip; it *"deliberately does
  not edit CI matrices"* (PR #296). Confirmed distinct.
- **Absorbs** the orphaned `livespec-fgqgnk` Phase-G.4 CI-wiring intent.
- Not a change to *which* checks exist or their severity — purely
  whether CI *runs* the checks the aggregate already defines.

## First slices (worklist — not yet filed)

Per the sibling-repo tenanting model, per-repo slices live in **each
repo's own beads tenant**; this epic (`livespec-cf4bcu`) is the hub
anchor and coordination point.

1. **Drift-guard slice** (`livespec-dev-tooling` tenant) — land the
   CI-matrix ⊇ canonical assertion in the shared check package. Blocks
   the large tracks (they need the guard to be self-closing).
2. **Quick win: console** (`livespec-console-beads-fabro` tenant) — add
   `check-plugin-resolution` to the CI matrix (1 line).
3. **Quick win: driver-codex** (`livespec-driver-codex` tenant) — add
   `check-plugin-resolution` to the CI matrix (1 line).
4. **Large tracks** — runtime (~35), core (~27), both orchestrators
   (~40 / ~35), dev-tooling (~48). Groom each per repo; wire matrix
   entries + branch protection; use driver-claude as reference.

## Related work

- **livespec-runtime PR #161** (MERGED 2026-07-10) — propose-change
  `ci-invocation-clause-align-fleet-matrix`: revised runtime's NFR
  §"Task-runner discipline" clause (the sole fleet outlier that mandated
  CI invoke `just check`) to bless the completeness-guarded per-target
  matrix. Pending `/livespec:revise` ratification. Resolved gap
  `gap-rsfmjjzl` (runtime work-item `livespec-runtime-woe5gi`).
- Reference for the per-target matrix convention: livespec core
  `SPECIFICATION/contracts.md` §"Pre-commit step ordering" (zero-`.py`
  subsetting), which prescribes the matrix shape this epic completes.
