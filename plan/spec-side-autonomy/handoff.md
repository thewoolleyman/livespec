# spec-side-autonomy — handoff

Updated 2026-08-12. **`livespec-jvdvx4.9` is mid-implementation: its safe half
is written and reviewed-by-CI, and what remains is the workflow wiring — the
part that can break a merge gate.** Read the ledger note on
`livespec-jvdvx4.9` before starting; it carries the confirmed design, the
ratified clauses quoted from the live spec, and the corrected acceptance.

**Slice 1 IS on `master`** — PR #2200 merged as `72967098`, confirmed against
the forge rather than assumed. Slice 2 builds directly on it.

There is NO uncommitted work and NO worktree belonging to this thread. Two of
this thread's branches may still exist on the forge:
`spec-pr-merge-derivation-module` (merged via #2200) and
`wrapup-jvdvx4-9-slice1` (this handoff, #2201). Delete them; they are MINE,
not foreign — every OTHER worktree under `$HOME/.worktrees/livespec/` belongs
to another session and must not be touched.

**Ledger anchor:** epic `livespec-jvdvx4`

## What landed

- **v202 ratified** (`45de58f2`, PR #2195) — the shared-CI-logic lane plus the
  single-authority channel partition. Closed `livespec-n0ka`.
- **`livespec-odkk` fixed and closed** (`56854664`, PR #2197) — the template's
  four reusable-workflow pins now read `@v1.20.4`, matching core's own five.
- **`.9` slice 1** — merged as `72967098` (PR #2200). The pure derivation
  module `.claude-plugin/scripts/livespec/spec_governance/pr_merge_derivation.py`
  plus 11 unit tests. **Touches zero workflow files by design**, so it cannot
  alter any gate decision. Green on `just check`: 78 targets, 100% coverage.

  **Measured, and it constrains slice 2:** the module runs under bare system
  `python3` with no venv, pip, or install step — but a NAKED import fails,
  because importing `livespec.spec_governance.*` triggers `livespec/__init__.py`
  → `livespec.io.structlog_facade` → vendored `structlog`. It resolves only
  with `.claude-plugin/scripts/_vendor` on `sys.path`. So slice 2's entry point
  MUST be a `bin/` wrapper following the existing `_bootstrap.py` convention,
  never a `python3 -c "import livespec…"` line in a workflow, which would fail
  closed with `ModuleNotFoundError`.

## THE LIVE TASK — `.9` slice 2: the workflow wiring

Everything below is the part deliberately NOT done yet, because it is the part
that can fail a merge gate open or closed without announcing itself.

1. **Core's root `auto-enable-merge.yml`** — replace the ~250-line embedded
   bash derivation with a thin call into the shipped module. The ratified text
   explicitly permits core to invoke the script directly rather than calling
   the reusable workflow, so do NOT restructure core into a `workflow_call`
   with secrets plumbing; that is avoidable risk for no contract gain.
2. **`.github/workflows/reusable-spec-pr-merge-policy.yml`** — new, for the
   template's consumers, which have no other way to obtain the code. It MUST
   check `livespec` out at the SAME revision through which it was resolved, so
   the consumer's single `uses:` pin governs both workflow and script.
   `github.job_workflow_sha` is the mechanism; **verify it resolves live** —
   that is platform knowledge, not measured here, and if it does not resolve
   the ratified clause still binds and the answer is a different mechanism,
   never a second consumer-side pin.
3. **The template twin** `.jinja` — `uses:` the reusable workflow, pinned
   `@vX.Y.Z`, never `@master`.
4. **A thin I/O layer** for the git/`gh` calls. Raises are confined to
   `io_trees` (`.claude-plugin/scripts/livespec/io`), so put anything that can
   throw there. The module already exposes `LOCAL_DIFF_ARGS` and
   `API_ACCEPTED_STATUSES` — USE THEM rather than re-spelling the flags, which
   is precisely the drift they exist to prevent.
5. **The live leg**, in a `livespec-orchestrator-*` repo — those are the only
   repos the template reaches. NOT an adopter; `.copier-answers.yml` exists in
   exactly two orchestrator repos and zero adopters.

**Read all three diagnostic legs IN ORDER**: the run CONCLUDED SUCCESS, the
policy step EMITTED ITS OWN OUTPUT, and only then the `auto_merge` field. A
crashed step and a manual-policy step both leave `auto_merge` unset, which is
exactly how `livespec-jvdvx4.13` shipped broken. A rendered template is not
acceptance.

**Not factory-dispatchable** — both surfaces are `.github/workflows/` and the
dispatch credential withholds the `workflows` grant. Land maintainer-side.

## Open items

- **`livespec-4kwu`** (P2) — template `.jinja` pins are outside bump-pin
  rewrite and pin-freshness coverage entirely, so the pins `livespec-odkk` just
  corrected will NOT be bumped when core's are, and `.9` adds a fifth to the
  same blind spot. Two constraints are recorded on the item: the shortest fix
  (adding a `templates/orchestrator-plugin/` literal to the upstream scanner)
  is the BANNED direction, and the tenant question is decided — it stays in
  `livespec`, with an explicit trigger to move it upstream if the generic-glob
  shape is chosen over the core-side check.
- **`livespec-jvz8`** (P2) — `livespec-dev-tooling` and `livespec-runtime`
  ratify their own specs with no merge-policy gate, and v202 permanently
  excludes them from this channel. Pre-existing, architecturally forced. **Do
  NOT close it by having either repo consume the core channel.**
- **`livespec-jvdvx4.2`** — leg 2 (twelve-repo backfill) is NOT AUTHORIZED.

## What this thread paid for that the next should not

- **Separate the risky half from the safe half before declaring work
  indivisible.** I called `.9` one unit; the maintainer challenged it, and the
  module was cleanly separable because new code under a source tree cannot
  change gate behaviour while every workflow still runs its old body. Ask that
  question first.
- **Review the FIX as adversarially as the original.** Across v202's four
  rounds, ten blockers were found and three were introduced by a fix round that
  was itself correcting real defects; the last was a citation made MORE precise
  and thereby FALSE.
- **Give each reviewer a DIFFERENT instrument.** Findings were disjoint every
  round. The mechanical-composition instrument — actually applying edits to a
  scratch copy and reading the product — found a doubled em dash that reading
  the edits could not.
- **A ratifying PR here needs a MANUAL merge.** Core inherits the safe `manual`
  default. A proposal-FILING PR, by contrast, auto-merges while review is still
  running, by design — so filing and review are not sequential gates on one PR.
- **`* [new branch]` on a second push** means the branch was auto-deleted after
  merging and your push recreated it, orphaning the commit. It happened twice.
- **Ratification evidence mechanics:** `reviewer_identity` must EQUAL
  `reviewer_model`, and that must equal the configured `fable`. Verify the
  digest by IMPORTING `_canonical_ratification_digest` rather than
  reimplementing its uint64-BE framing. Nothing downstream checks that the CLI
  wrote what you reviewed — diff it yourself.
- **The `github_rate_limit_guard` hook matches loop keywords as SUBSTRINGS, in
  ordinary prose.** "be**for**e" tripped it in a PR title. Write bodies to a
  file and use `--body-file`; capture a forge read in one call and parse it in
  another; `map`/`filter` instead of a list comprehension; no `jq select(...)`.

## Standing constraints

- Dedicated worktree per PR; never edit tracked files in
  `/data/projects/livespec`, the pane's cwd. After creating one:
  `just install-worktree-pack`, then `git checkout -- .livespec.jsonc`.
- Never `--no-verify`; halt and report on hook failure. Full `just check`
  before pushing.
- Every worktree under `$HOME/.worktrees/livespec/` other than your own is
  FOREIGN. **Enumerate rather than trusting any list here** — it drifts. Never
  run the reaper in this repo.
- Another session lands on this `master` concurrently; it moved several times
  during this work. Rebase; force-push ONLY your own branch.
- This repo rebase-merges, so one change has TWO SHAs. Ask the forge; never
  `--is-ancestor` on a branch tip.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- Milestone trail: `tmp/overseer/spec-side-autonomy/worker-status.log`.
