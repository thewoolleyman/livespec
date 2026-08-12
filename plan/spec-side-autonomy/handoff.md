# spec-side-autonomy — handoff

Updated 2026-08-12. **Epic `livespec-jvdvx4` is FULLY CLOSED, and NOTHING here
is waiting on a human.** The thread took `livespec-4kwu`, decided its fix shape
on evidence, moved it upstream as `livespec-dev-tooling-ep8n` — and has now
HANDED that item off, so the thread owns no in-flight work at all.

There is NO uncommitted work and NO worktree belonging to this thread. Every
worktree under `$HOME/.worktrees/livespec/` is FOREIGN — **enumerate rather
than trusting this sentence**, it drifts. Never run the reaper in this repo.

**Ledger anchor:** epic `livespec-jvdvx4` (closed).

Also live, and NOT under that epic: `livespec-4kwu` (closed as MOVED),
`livespec-dev-tooling-ep8n` (open in the `livespec-dev-tooling` tenant, and NO
LONGER this thread's), and `livespec-5qu1` (open, P2).

## Disposition of the one open decision — SETTLED, do not reopen

The predecessor left exactly one question for a human: authorise an independent
adversarial reviewer so this thread could ratify the amendment
`livespec-dev-tooling-ep8n` needs and land the fix, or hand the item to whoever
grooms `livespec-dev-tooling`.

**The maintainer chose HAND OFF, 2026-08-12.** `livespec-dev-tooling-ep8n`
stays open in the `livespec-dev-tooling` tenant with its decided shape intact
and now carries a comment recording that it is unblocked in substance and
blocked only on that review authorization. This thread does not carry it
further, and a later session picking this document up should NOT re-offer the
choice — it was asked and answered.

The reason the item is blocked at all, preserved so the receiving groomer need
not re-derive it: the SUFFIX half of the scanner widening extends a normative
clause in `livespec-dev-tooling`'s `SPECIFICATION/contracts.md` §"Pin
autodiscovery rules", so it needs a ratified amendment THERE, and the fleet
rule requires an independent adversarial review by a separately-spawned
reviewer ahead of that accept. Do not implement the code without the amendment
— shipping widened behaviour unamended creates drift in the one document the
pin-currency policy calls the source of truth for pin-format definitions.

A third option was put to the maintainer and DECLINED: landing only the
directory half, on the theory that it needs no amendment. It buys nothing —
all five missed pins are wrong on both counts, so a one-count fix discovers
none of them.

## What landed (epic `livespec-jvdvx4`)

- **v202 ratified** (`45de58f2`, PR #2195) — the shared-CI-logic lane plus the
  single-authority channel partition. Closed `livespec-n0ka`.
- **`livespec-odkk` fixed and closed** (`56854664`, PR #2197).
- **`.9` slice 1** — `72967098` (PR #2200): the pure derivation module.
- **`.9` slice 2a** — `28b2850e` (PR #2204): the entry point plus the thin I/O
  layer. Touched zero workflow files.
- **`.9` slice 2b-i** — `97b9bddf` (PR #2205): core's root
  `auto-enable-merge.yml` repointed at that module (the ~250-line embedded bash
  DELETED, not disabled), plus
  `.github/workflows/reusable-spec-pr-merge-policy.yml`.
- **`.9` slice 2b-ii** — `15e52ca1` (PR #2207): the copier template's twin,
  pinned `@v0.32.0`.
- **The consumer** — `thewoolleyman/livespec-orchestrator-git-jsonl` PR #591
  (merged `c304d1c9`) carries the gate.

`.9`'s live leg ran on BOTH decision branches in that consumer, each read as
three legs in order: known-empty (PR #591, run `31565785374`, `decision: auto`,
auto-merge registered) and governed (PR #593, run `31566136098`, a true `R100`
rename, `decision: blocked`, auto-merge correctly withheld, closed unmerged).
Full evidence is on the ledger item; it is not repeated here.

## Open items

- **`livespec-dev-tooling-ep8n`** (P2, in the `livespec-dev-tooling` tenant) —
  pin autodiscovery misses workflow-template pins on BOTH directory and suffix.
  Shape DECIDED; HANDED OFF to that repo's groomer, so it is listed here for
  continuity only and is not this thread's to advance. See "What the next
  session must not re-derive".
- **`livespec-5qu1`** (P2) — a full `copier update` in any consumer still on the
  old generated form swaps the App-token step from
  `actions/create-github-app-token@v1` + `app-id:` to `@v3` + `client-id:`. The
  two inputs are NOT interchangeable.

  **Which FORM each repository carries is now MEASURED, and that half of the
  question is CLOSED.** Measured 2026-08-12 against each repository's freshly
  fetched `origin/master`: BOTH repositories carrying `.copier-answers.yml` —
  `livespec-orchestrator-git-jsonl` AND `livespec-orchestrator-beads-fabro` —
  carry the OLD `actions/create-github-app-token@v1` + `app-id:` form, while the
  `livespec` copier template
  (`templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja`)
  and `livespec`'s own root `.github/workflows/` both carry `@v3` +
  `client-id:`. So `livespec-orchestrator-beads-fabro`'s form is no longer an
  open question — stop describing it as one.

  **Do not overstate that.** What is measured is the FORM each generated
  workflow uses. What each consumer's `APP_ID` secret actually HOLDS — an App id
  or a client id — is still unreadable from outside those repositories and still
  needs the maintainer. `livespec-5qu1` therefore stays OPEN and P2 on that
  second half, and the risk is UNVALIDATED rather than untested.
- **`livespec-jvz8`** (P2) — `livespec-dev-tooling` and `livespec-runtime`
  ratify their own specs with no merge-policy gate, permanently excluded by
  v202. Pre-existing and architecturally forced. **Do NOT close it by having
  either repo consume the core channel.**
- **`livespec-jvdvx4.2`** — leg 2 (twelve-repo backfill) is NOT AUTHORIZED.
- **`livespec-orchestrator-beads-fabro` does not carry the spec-PR gate.** It
  will receive it on its next template re-sync. That is propagation, and
  `livespec-5qu1` is the item that must measure it.

## What the next session must not re-derive (`ep8n`)

All of this is measured, not reasoned. Re-verify if cheap; do not redo. The
load-bearing points are ALSO mirrored onto the ledger item itself, so the
receiving groomer gets them without reading this document — but this remains
the fuller record.

- **The rewriter needs NO change.** `pin_rewrite._compile_github_workflow_uses`
  matches `^\s+uses: <pin_key>@<current>` against whatever `PIN_FILE` names, so
  it is path- and suffix-agnostic. **Discovery is the only missing piece.**
- **The core-side check is ELIMINATED, not merely unchosen.** It only DETECTS,
  leaving a human in the loop every release; and it is a category error against
  the fifth pin, which is `livespec`'s OWN reusable workflow at `@v0.32.0` and
  has no counterpart in core's `.github/workflows/` (those pin
  `livespec-dev-tooling` at `@v1.20.4`).
- **The fifth pin is reached ONLY by freshness.** `release-dispatch` excludes
  the releasing repo from its own dispatch matrix, so no `livespec` release
  ever fans out to `livespec`. Core's `pin-freshness.yml` runs daily with NO
  source filter and opens a bump PR per stale triple, so it reaches it.
- **The shortest fix is the BANNED one.** Do not put
  `templates/orchestrator-plugin/` — or any consumer-specific path — into
  upstream code. Stay generic: any-depth `.github/workflows/`, plus the
  `.jinja` suffix.
- **False positives measured:** across `livespec`, `livespec-dev-tooling` and
  both `livespec-orchestrator-*` repos, the ONLY `.github/workflows/` other
  than each repo's root is core's single template one. Zero today.
- **The two halves are NOT in the same position.** The suffix half extends the
  contract and must be ratified. The DIRECTORY half is weaker: the clause says
  "any GitHub Actions workflow file (under `.github/workflows/`)" with NO root
  qualifier while the code hardcodes root, so widening it arguably brings the
  IMPLEMENTATION into conformance rather than changing the contract.

## What this thread paid for that the next should not

- **Verify a platform mechanism before building on it, in the shape a consumer
  uses.** `github.job_workflow_sha` DOES NOT RESOLVE — measured from both a
  same-repository and a genuine cross-repository caller; it is the empty string
  and `GITHUB_JOB_WORKFLOW_SHA` is unset. Neither neighbour substitutes:
  `github.workflow_sha` and `github.workflow_ref` describe the CALLER's entry
  workflow. Unverified, it would have made `actions/checkout` resolve
  livespec's DEFAULT BRANCH from an empty `ref:`. **What works:** the run's own
  `referenced_workflows[]` from the Actions API, costing one `actions: read`
  grant. A same-repo probe alone could NOT have established this — there
  `workflow_sha` happens to equal the right answer.
- **A probe is not a fixture; the SHAPE is what matters.** The line is
  **merge-base existence**, which makes a rename classification genuine.
  `livespec-jvdvx4.6`'s first leg proved nothing because it hand-ADDED a file.
- **A red CI job is not a failed check.** Master's
  `check-copier-template-smoke` went red with its own command step SKIPPED —
  the failure was step 7, "Install Python dev deps via uv". Read the step list,
  not the job colour. Three egress/TLS flakes were seen in one night; re-run
  before diagnosing.
- **Order a pin against the artifact, not the calendar.** Test tag containment
  with a control that DISCRIMINATES (ABSENT at `v0.31.0`, PRESENT at
  `v0.32.0`), never a bare presence check.
- **Gate affirmatively.** `decision == 'auto'`, never `!= 'blocked'`: an
  explicit `if:` on a job with `needs:` REPLACES the implicit success
  requirement, so a skipped or failed job yields an empty output that
  `!= 'blocked'` reads as permission.
- **A ratifying PR here needs a MANUAL merge.** Core inherits the safe `manual`
  default. A proposal-FILING PR auto-merges while review is still running.
- **The `github_rate_limit_guard` hook matches loop keywords as SUBSTRINGS, in
  ordinary prose.** "be**for**e" and "**for** audit" both trip it. Write bodies
  to a file in one call and run `gh` in another; `map`/`filter` instead of a
  list comprehension; no `jq select(...)`.

## Standing constraints

- Dedicated worktree per PR; never edit tracked files in
  `/data/projects/livespec`, the pane's cwd. After creating one:
  `just install-worktree-pack`, then `git checkout -- .livespec.jsonc`.
- Never `--no-verify`; halt and report on hook failure. Full `just check`
  before pushing.
- Each sibling repo governs itself — read its own rules before pushing there,
  and treat Red-Green-Replay scope as a per-repo question, not a fleet
  constant.
- Another session lands on this `master` concurrently. Rebase; force-push ONLY
  your own branch.
- This repo rebase-merges, so one change has TWO SHAs. Ask the forge; never
  `--is-ancestor` on a branch tip.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- Milestone trail: `tmp/overseer/spec-side-autonomy/worker-status.log`.
