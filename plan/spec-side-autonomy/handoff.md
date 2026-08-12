# spec-side-autonomy — handoff

Updated 2026-08-12. **`livespec-jvdvx4.9` is CLOSED.** Both halves of slice 2
shipped and the live leg ran on BOTH decision branches in a real consumer. The
epic's remaining open items are listed under "Open items"; none of them blocks
another.

There is NO uncommitted work and NO worktree belonging to this thread. Every
worktree under `$HOME/.worktrees/livespec/` is now FOREIGN — **enumerate rather
than trusting this sentence**, it drifts. Never run the reaper in this repo.

**Ledger anchor:** epic `livespec-jvdvx4`

## What landed

- **v202 ratified** (`45de58f2`, PR #2195) — the shared-CI-logic lane plus the
  single-authority channel partition. Closed `livespec-n0ka`.
- **`livespec-odkk` fixed and closed** (`56854664`, PR #2197).
- **`.9` slice 1** — `72967098` (PR #2200). The pure derivation module
  `spec_governance/pr_merge_derivation.py` plus 11 unit tests.
- **`.9` slice 2a** — `28b2850e` (PR #2204). The entry point and the thin I/O
  layer: `commands/spec_pr_merge_policy.py`,
  `commands/_spec_pr_merge_gather.py`, `io/_git_pull_request.py`,
  `gh.list_pull_request_files`, `fs.append_text`, and the
  `bin/spec_pr_merge_policy.py` wrapper. Touched zero workflow files.
- **`.9` slice 2b-i** — `97b9bddf` (PR #2205). Core's root
  `auto-enable-merge.yml` repointed at that module — the ~250-line embedded
  bash DELETED, not disabled — plus
  `.github/workflows/reusable-spec-pr-merge-policy.yml`.
- **`.9` slice 2b-ii** — `15e52ca1` (PR #2207). The copier template's twin,
  pinned `@v0.32.0`.
- **The consumer** — `thewoolleyman/livespec-orchestrator-git-jsonl` PR #591
  (merged `c304d1c9`) carries the gate.

## The two findings worth carrying forward

**`github.job_workflow_sha` DOES NOT RESOLVE.** The design record named it as
the mechanism satisfying the ratified Pinning clause, flagged unverified. It
was verified and it failed: measured on GitHub-hosted runners from BOTH a
same-repository and a genuine cross-repository caller, it is the empty string
and `GITHUB_JOB_WORKFLOW_SHA` is unset. Neither neighbour substitutes —
`github.workflow_sha` and `github.workflow_ref` describe the CALLER's entry
workflow, so in a real consumer they name the consumer's own commit. Shipping
it unverified would have made `actions/checkout` resolve livespec's DEFAULT
BRANCH from an empty `ref:`, so a consumer pinning a release tag would have run
master with nothing in the decision to show it. **What works instead:** the
run's own `referenced_workflows[]` from the Actions API, which carries each
resolved reusable workflow's `path` (with the `@ref` as written) and its `sha`.
That is the revision the clause names, still derived from the consumer's single
pin. Cost: one `actions: read` grant on the calling job.

**The same-repository probe was not enough to establish it.** A same-repo
caller could plausibly have been treated as local, and `workflow_sha` happens
to equal the right answer there. Only the cross-repo probe was decisive. When a
platform behaviour differs between "our repo" and "a consumer's repo", the
same-repo measurement is the wrong source.

## `.9`'s acceptance, and how it was met

The item's DESCRIPTION carried a clause naming a target that CANNOT EXIST —
"exercised live in a real adopter" — when `.copier-answers.yml` is present in
exactly two repositories, both `livespec-orchestrator-*`, and in ZERO adopters.
That is now corrected IN THE DESCRIPTION, with the original quoted in the notes
so the correction is auditable, and a sixth clause added requiring the live leg
to cover BOTH decision branches.

Both branches ran in `thewoolleyman/livespec-orchestrator-git-jsonl` through its
template-derived workflow, each read as three legs IN ORDER:

- **Known-empty** — PR #591, run `31565785374`: run CONCLUDED SUCCESS; the
  policy step EMITTED ITS OWN OUTPUT (pin resolved to `e38b8e61`, which equals
  `git rev-parse v0.32.0^{commit}`, then `decision: auto`, `proposal_stems: []`);
  only then auto-merge registered.
- **Governed** — PR #593, run `31566136098`, closed UNMERGED: a probe MOVED
  `archive/README.md`, present at the merge-base, into
  `SPECIFICATION/history/v018/proposed_changes/live-rename-probe.md`, which git
  scored `R100`; run CONCLUDED SUCCESS; the policy step EMITTED ITS OWN OUTPUT
  (`decision: blocked`, `effective_policy: manual`, `effective_source: proposal`,
  `proposal_stems: ["live-rename-probe"]`); only then auto-merge NOT registered.

**Why the governed leg nearly did not run, and why that would have been the
worst outcome available.** This thread first declined it as "manufacturing
evidence", because both orchestrator repositories have ZERO pending proposals.
That call was challenged and withdrawn. The line is not probe-versus-real; it is
**merge-base existence**, which is what makes the rename classification genuine
rather than simulated — `livespec-jvdvx4.6`'s first leg proved nothing because
it hand-ADDED a file, the wrong SHAPE. And the challenge was factually right:
until PR #593 the reusable workflow had NEVER executed the governed branch,
because core's root workflow invokes the script directly, so core's own
ratifying pull requests exercise the script but not the reusable workflow.
Closing on the non-governed leg alone would have repeated `livespec-jvdvx4.13`
exactly — a gate that looked fine because every exercise avoided the shape
production makes.

**Propagation was PARTIAL and the evidence must not be read otherwise.** PR #591
propagated the GATE BLOCK ONLY, byte-identical to the template render, leaving
the App-token step untouched. It validates THE GATE, not the copier propagation
path. A full `copier update` in that repository is UNEXERCISED: it sits on
`_commit: v0.4.0` and conflicts in seven files plus a new `.ai/` tree.

## Open items

- **`livespec-5qu1`** (P2, NEW) — a full `copier update` in any consumer still
  on the old generated form swaps the App-token step from
  `actions/create-github-app-token@v1` + `app-id:` to `@v3` + `client-id:`. The
  two inputs are NOT interchangeable, and which one each consumer's `APP_ID`
  secret holds cannot be read from `livespec`, so it is UNVALIDATED rather than
  untested. `livespec-orchestrator-beads-fabro`'s form is an open question, not
  an assumption.
- **`livespec-4kwu`** (P2) — template `.jinja` pins sit outside bump-pin rewrite
  and pin-freshness coverage, so the new fifth pin `@v0.32.0` will not be bumped
  automatically. Two constraints are recorded on the item: the shortest fix is
  the BANNED direction, and the tenant question is decided.
- **`livespec-jvz8`** (P2) — `livespec-dev-tooling` and `livespec-runtime`
  ratify their own specs with no merge-policy gate, permanently excluded by
  v202. Pre-existing and architecturally forced. **Do NOT close it by having
  either repo consume the core channel.**
- **`livespec-jvdvx4.2`** — leg 2 (twelve-repo backfill) is NOT AUTHORIZED.
- **`livespec-orchestrator-beads-fabro` does not yet carry the gate.** It will
  receive it on its next template re-sync. That is propagation, and
  `livespec-5qu1` is the item that must measure it.

## What this thread paid for that the next should not

- **Verify the platform mechanism before building on it, and verify it in the
  shape a consumer uses.** See the `job_workflow_sha` finding above. The guard
  that caught it is permanent: the reusable workflow fails the job with a named
  cause rather than defaulting, because an empty `ref:` silently means "default
  branch".
- **Separate the risky half from the safe half before declaring work
  indivisible.** Slice 2a touched zero workflow files and so could not alter a
  gate decision; only 2b could.
- **Order a pin against the artifact, not against the calendar.** At the moment
  slice 2b-i merged, the latest release was `v0.31.0`, cut sixteen minutes
  earlier and containing no reusable workflow. Pinning "the latest release"
  without looking would have rendered a workflow that fails closed in every
  generated repository. Test containment with a control that DISCRIMINATES:
  ABSENT at `v0.31.0`, PRESENT at `v0.32.0`.
- **A red CI job is not a failed check.** Master's `check-copier-template-smoke`
  went red with its own command step SKIPPED — the failure was step 7,
  "Install Python dev deps via uv". Read the step list, not the job colour.
- **Gate affirmatively.** `decision == 'auto'` rather than `!= 'blocked'`: an
  explicit `if:` on a job with `needs:` REPLACES the implicit success
  requirement, so a skipped or failed policy job yields an empty output that
  `!= 'blocked'` would read as permission.
- **A ratifying PR here needs a MANUAL merge.** Core inherits the safe `manual`
  default. A proposal-FILING PR auto-merges while review is still running.
- **`* [new branch]` on a second push** means the branch was auto-deleted after
  merging and your push recreated it, orphaning the commit.
- **The `github_rate_limit_guard` hook matches loop keywords as SUBSTRINGS, in
  ordinary prose.** "be**for**e" trips it. Write bodies to a file in one call and
  run `gh` in another; `map`/`filter` instead of a list comprehension; no
  `jq select(...)`.

## Standing constraints

- Dedicated worktree per PR; never edit tracked files in
  `/data/projects/livespec`, the pane's cwd. After creating one:
  `just install-worktree-pack`, then `git checkout -- .livespec.jsonc`.
- Never `--no-verify`; halt and report on hook failure. Full `just check`
  before pushing.
- Another session lands on this `master` concurrently. Rebase; force-push ONLY
  your own branch.
- This repo rebase-merges, so one change has TWO SHAs. Ask the forge; never
  `--is-ancestor` on a branch tip.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- Milestone trail: `tmp/overseer/spec-side-autonomy/worker-status.log`.
