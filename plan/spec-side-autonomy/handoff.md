# spec-side-autonomy — handoff

Updated 2026-08-12. **Epic `livespec-jvdvx4` is FULLY CLOSED.** The thread took
`livespec-4kwu`, decided its fix shape on evidence, moved it upstream as
`livespec-dev-tooling-ep8n`, and has HANDED that item off.

**The thread owns exactly ONE live item: `livespec-5qu1`.** Its direction is
decided and its template change has landed and RELEASED; it is open on a single
named leg, the live auto-merge exercise, which **will not discharge on its own**
— see §"Open items". An earlier revision of this paragraph said the thread
"owns no in-flight work at all"; that was written before the maintainer chose
the `app-id:` direction and is retracted.

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

## Also landed — opportunistic repairs, NOT ledger items

These were found by exercising shipped surfaces rather than by working an item,
so they have no work-item and would otherwise leave no trace here.

- **`livespec-5qu1`'s template fix** — `88842637` (PR #2214), released in
  `v0.33.1`. See §"Open items" for what remains.
- **Two `doctor-static` path-resolution crashes**, found by running the shipped
  CLI while checking whether the spec tree was healthy:
  - `fix(doctor)` `6180d10b` (PR #2222) — a RELATIVE `--spec-target` raised an
    unhandled `ValueError` from `spec_root.relative_to(project_root)` and
    produced ZERO findings. Only an absolute target had ever been exercised.
  - `fix(doctor)` `be4cd0b1` (PR #2225) — a relative `--project-root` left the
    spec root relative, so a finding's `spec_root` was absolute or not depending
    on how an unrelated flag was spelled. **The two had to be normalised
    together**: fixing only the spec root would have reintroduced the first
    crash under a different flag.

  Both follow the `revise` / `propose-change` idiom already in the repository —
  `is_absolute()`, else anchor to `Path.cwd()`. Scope was checked, not
  pattern-matched: every `relative_to(project_root)` call site lives under
  `doctor/static/`, and `next` was exercised live to confirm it is unaffected.

- **A verification trap** filed as instance 31 in
  `.ai/verifying-against-the-right-source.md` — `4c603e86` (PR #2220), with the
  `AGENTS.md` enumeration extended in lockstep.

**The spec tree itself is HEALTHY.** `doctor-static` passes every check
(20 pass, 1 skipped, exit 0). There is one `proposed_changes/` queue only; the
repo has no sub-spec trees.

**TWO spec→implementation DRIFTS were found and FILED, so the queue is no longer
empty.** An earlier revision of this paragraph said it was, then said one; both
were true when written and this same session filed past them. These are
retractions of its own claims, not corrections of anyone else's.

- **`doctor-spec-target-drift.md`** (PR #2229, merge `3ae4123e`) —
  `contracts.md` says in TWO places that the `doctor` static wrapper takes only
  `--project-root`, while `doctor_static.py` has accepted and honoured
  `--spec-target` since `8486f955` (2026-07-01). **The direction is an open
  design call**: document the flag (recommended — every sibling
  spec-tree-scoped wrapper already declares one) or delete it from the
  implementation and its asserting test. The proposal records both.
- **`spec-governance-flag-drift.md`** (PR #2232, merge `6a5f5435`) —
  `contracts.md` enumerates the spec-governance control CLI's modes as a CLOSED
  list of three, while the CLI has a fourth, `--check-default-block`, appearing
  ZERO times anywhere under `SPECIFICATION/`, added in `e2f2232d` (2026-08-04).
  **This one has NO alternative direction**: the mode is consumed by an
  enforcement check inside `just check`, so deleting it would remove live guard
  coverage rather than tidy an unused surface.

**BOTH are FILED, NOT RATIFIED, and must not be cleared as routine queue-keeping.**
Ratification needs the independent adversarial review.

**Two mechanical checks BEFORE ratifying either — the filing-time ones do not
carry over.** At filing, each proposal's quoted replacement targets were
verified to exist verbatim and exactly once, and each file's front-matter
`topic` was confirmed equal to its stem. Both were re-verified against
`origin/master` at 2026-08-12T14:58Z and still held. **Neither result survives
the next commit to `contracts.md`**, which any session may land, so re-run both
rather than citing this paragraph:

1. **Replacement-target fidelity.** Read the live file with
   `git show origin/master:SPECIFICATION/contracts.md`, never the working tree,
   and confirm each quoted target appears EXACTLY ONCE. A `resulting_files[]`
   entry replaces the whole file, so a drifted target is not a near-miss — it
   silently ratifies the wrong bytes.
2. **Topic/stem equality.** The front-matter `topic` MUST equal the file stem
   (`doctor-spec-target-drift`, `spec-governance-flag-drift`). A mismatch makes
   revise exit 3 SILENTLY, which reads as "nothing to do" rather than as an
   error.

**The audit behind them is COMPLETE — do not redo it.** All nine
§"Wrapper CLI surface" rows were checked against each wrapper's actual `--help`.
`seed`, `propose-change`, `critique`, `prune-history`, `resolve-template` and
`next` match exactly.

One row was deliberately NOT filed. `revise` carries three flags absent from the
whole spec tree — `--post-step-doctor`, `--skip-stale-branch-check`,
`--run-stale-branch-check` — but that is INCOMPLETENESS, not contradiction: the
table's preamble says each wrapper "adds its own flags above that baseline", so
nothing in the contract is falsified. The two filed drifts are different in kind
— each contradicts an explicit completeness claim (`takes only`, `one of`). If a
maintainer wants the table exhaustive, `revise` is the row to add; that is a
judgement call, not a defect, and it was left rather than inflated into a third
proposal.

`next` therefore now ranks `revise` (queue depth 2) and `prune-history`, both at
LOW urgency. Neither is urgent, and a LOW-urgency ranking is not a mandate.

## Open items

- **`livespec-dev-tooling-ep8n`** (P2, in the `livespec-dev-tooling` tenant) —
  pin autodiscovery misses workflow-template pins on BOTH directory and suffix.
  Shape DECIDED; HANDED OFF to that repo's groomer, so it is listed here for
  continuity only and is not this thread's to advance. See "What the next
  session must not re-derive".
- **`livespec-5qu1`** (P2) — **RESOLVED IN DIRECTION, and the template change has
  LANDED.** The maintainer chose on 2026-08-12 to keep `app-id:` in the copier
  template rather than migrate consumers to `client-id:`. PR #2214 (merge
  `88842637`) changed
  `templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja`
  to mint with `actions/create-github-app-token@v3` passing `app-id:`, corrected
  the auth-model comment block, and inverted the paired assertion in
  `tests/dev-tooling/checks/test_copier_template_smoke.py` that had pinned the
  old form. Do NOT re-open the choice.

  **Why that is auth-neutral.** Measured 2026-08-12 against each repository's
  freshly fetched `origin/master`: BOTH repositories carrying
  `.copier-answers.yml` — `livespec-orchestrator-git-jsonl` AND
  `livespec-orchestrator-beads-fabro` — carry `@v1` + `app-id:`, so keeping
  `app-id:` means the next `copier update` changes no input name in either.
  `livespec`'s OWN root `.github/workflows/` deliberately stays on `@v3` +
  `client-id:`, because livespec's own `APP_ID` secret holds the client ID;
  making it "consistent" would break the one repository that is currently
  correct. `app-id` is deprecated but NOT removed at `@v3` — upstream's
  `action.yml` declares it `required: false` with `deprecationMessage` — so the
  fleet carries that warning deliberately.

  **The `client-id:` migration is decoupled, not cancelled.** It requires each
  consumer's `APP_ID` secret to be reset to the App's OAuth client ID first,
  which only the maintainer can do. That is why nothing here reads a secret.

  **Still OPEN and P2 on ONE named leg: the LIVE auto-merge exercise.**
  Rendering is not evidence.

  **Propagation step 1 is DONE: release `v0.33.1` carries the fix.** Measured
  with a control that DISCRIMINATES rather than a bare presence check — at
  `v0.32.0` and `v0.33.0` the template's token step is `client-id:` with
  `app-id:` ABSENT, and at `v0.33.1` it is `app-id:` with `client-id:` ABSENT.
  Do not re-derive this by date; re-run the containment check if you doubt it.

  **Propagation step 2 is MANUAL and will NOT happen on its own.** The template
  ships `copier-update-drift.yml`, and it only DETECTS: it runs `copier update
  --dry-run --vcs-ref=master` on pull requests, pushes to master, and a weekly
  Monday cron, then tells a human to run `copier update --vcs-ref=master`
  locally and resolve conflicts. **It opens no pull request.** So no consumer
  will pick up `@v3` + `app-id:` until someone deliberately re-syncs one. A
  session that waits for this leg to discharge by itself will wait forever.

  (The workflow's `--vcs-ref=master` pin looks like it contradicts the fleet
  rule that pins track the latest RELEASE, and it does not: a bare `copier
  update` resolves the latest git TAG, which is `v1.0.0` — semver-greater than
  every `v0.x` release and predating the entire template workflow set. Checked,
  so it is not re-raised as a defect.)

  Consumer pull requests open today cannot serve as the exercise either, because
  each runs its own committed `@v1` + `app-id:` workflow, so a green one would
  prove only that the OLD form works. The ledger item records what discharges
  the leg and the order to read it in.
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
