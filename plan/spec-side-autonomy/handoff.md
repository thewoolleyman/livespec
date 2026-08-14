# spec-side-autonomy — handoff

Updated 2026-08-14. **Epic `livespec-jvdvx4` is FULLY CLOSED, and the
`proposed_changes/` queue is now EMPTY.** Both drifts this thread filed on
2026-08-12 were ratified on 2026-08-14 as **v204** and **v205**, in
`thewoolleyman/livespec` PR
[#2290](https://github.com/thewoolleyman/livespec/pull/2290) (merge
`d95e699b`).

## START HERE — nothing is in flight, and NOTHING here is autonomously actionable

**Read this section before planning anything.** The thread is at a clean stop:
no uncommitted work of its own, no branch, no worktree, every pull request
merged. Every worktree under `$HOME/.worktrees/livespec/` is FOREIGN —
**enumerate rather than trusting this sentence**, it drifts. Never run the
reaper in this repo.

Measured 2026-08-14 after the merge:

- `proposed_changes/` holds only `README.md`. Nothing pending.
- `doctor-static` is fully clean: 20 pass, 1 skipped, ZERO warnings.
- `next` ranks exactly ONE candidate: `prune-history` at **LOW**. That is
  not a mandate; 205 unpruned versions is unremarkable.

The thread owns two remaining things, and **both are gated on a human**:

| What | State | Why you cannot just do it |
|---|---|---|
| `livespec-5qu1` (open, P2) | direction decided, template fix landed AND released in `v0.33.1` | Its ONE remaining leg is a LIVE auto-merge exercise in a consumer. It **will not discharge on its own** — propagation is manual, and doing it means a `copier update` in a consumer, which is OUT of scope. |
| `livespec-jvz8` (open, P2) | pre-existing, architecturally forced | Needs a maintainer design call. Do NOT close it by having either repo consume the core channel. |

`livespec-dev-tooling-ep8n` is handed off; `livespec-jvdvx4.2` leg 2 is not
authorised. So **the correct first move is to ask the maintainer what they
want**, not to pick from this list.

**If you are told to keep working anyway** — the standing instruction to a
worker above the wind-down line — do NOT invent ledger work. What actually
produced value on 2026-08-12 and 2026-08-14, in order of yield:

1. **Exercise shipped surfaces rather than reading them.** Running
   `doctor_static.py` with a relative `--spec-target` found a crash that had
   survived because every caller and test passed an absolute path. Two real bug
   fixes came out of it.
2. **Audit contract text against actual behaviour.** Comparing
   `contracts.md` §"Wrapper CLI surface" row-by-row against each wrapper's real
   `--help` found BOTH drifts, now ratified. **That audit is COMPLETE — do not
   redo it**; see §"Open findings not yet filed" for the one thing it did not
   cover.
3. **Re-run the cheap health checks**: master CI (`--workflow CI`, and read the
   STEP list, not the job colour), `doctor-static`, and `next`.

Whatever you do, re-measure before acting. This document has been wrong several
times — each time because the session that wrote a fact then changed the state
behind it.

**Ledger anchor:** epic `livespec-jvdvx4` (closed).

Also live, and NOT under that epic: `livespec-4kwu` (closed as MOVED),
`livespec-dev-tooling-ep8n` (open in the `livespec-dev-tooling` tenant, and NO
LONGER this thread's), and `livespec-5qu1` (open, P2).

## What ratified on 2026-08-14 (v204 + v205)

Both were spec→implementation drifts in
`thewoolleyman/livespec`'s `SPECIFICATION/contracts.md`, each contradicting an
explicit COMPLETENESS claim (`takes only`, `one of`) rather than merely being
incomplete.

- **v204 — `spec-governance --check-default-block`.** `contracts.md`
  enumerated the control CLI's modes as a closed list of three, in two places,
  while the shipped CLI has had a fourth since `e2f2232d` (2026-08-04).
- **v205 — `doctor --spec-target`.** `contracts.md` said in two places that
  the doctor static wrapper takes only `--project-root`, while the shipped CLI
  has accepted and honoured `--spec-target` since `8486f955` (2026-07-01).
  Direction (document vs delete) was a genuine design call, decided by the
  maintainer 2026-08-12: **document**. v205 ALSO carries a co-edit to
  `.claude-plugin/prose/doctor.md`.

**Do not re-derive the direction on either.** v204's is forced (see below);
v205's was a human decision.

**v204's direction rationale was WRONG as originally filed, and the corrected
version is the one that ratified.** The proposal claimed the mode is consumed
by an enforcement check inside core's own `just check`, so deleting it would
remove live guard coverage. It is not: `dev-tooling/checks/spec_governance_template.py`
imports `verify_default_block` and compares IN-PROCESS; it never invokes the
CLI mode, and NO invoker exists in any fleet repo. The true ground — recorded in
the ratified v204 record — is that `--check-default-block` is the shipped
CONSUMER-SIDE distribution surface, so a governed downstream repo runs the
comparison against itself and core never reads INTO a consumer
(No-Circular-Dependency). Same conclusion, different reason. If you find
yourself citing the `just check` version, you are reading a pre-ratification
draft.

## The review gate earned its keep — read this before the next ratification

Both proposals were reviewed by separately-spawned, read-only Fable reviewers,
one per proposal so the two verdicts were genuinely independent rather than one
verdict counted twice. **Both returned BLOCKERS on the first pass. None were
waived.** Neither proposal was safe to ratify as filed, and both had already
passed their author's own filing-time checks.

- v204: two blockers, both against the proposal's own ARCHIVED RECORD rather
  than the contract text — a test-file miscount ("five", actually four), and
  the false rationale above.
- v205: one blocker — `.claude-plugin/prose/doctor.md` enumerated doctor's
  flags without `--spec-target`, so amending the contract ALONE would have left
  core contradicting itself in the artifact both Drivers actually read at
  invocation time.

Three transferable lessons:

1. **Sweep beyond `SPECIFICATION/`.** The v205 blocker was one step outside the
   spec tree. On re-review the reviewer widened across ALL of
   `.claude-plugin/prose/` and confirmed no other prose file asserts doctor's
   flag surface — a partial sweep would have been worse than none.
2. **Delete magnitudes rather than correcting them.** v204's miscount was fixed
   by removing the count ("a dev-tooling check and its tests"), so it cannot rot
   again.
3. **A blocker's named site may not be its only site.** v204's false rationale
   appeared in a SECOND place the reviewer had not named. Grep for the claim,
   do not just patch the cited line.

## Ratification mechanics that cost real time — do not rediscover these

- **The ratification evidence is cryptographically bound to the OUTPUT, not
  just the proposal.** `content_digest` is a SHA-256 over the proposal bytes
  PLUS every `resulting_files[]` path and content (uint64-BE length-framed,
  sorted by path). So a reviewer who saw only the proposal has not covered what
  the digest attests. Send the reviewer the FINAL BYTES and have it verify them
  before recording the verdict. Verify any reimplementation of the digest
  against the real `_canonical_ratification_digest` before trusting it.
- **`reviewer_identity` MUST equal `reviewer_model` STRING-FOR-STRING.**
  `_reviewer_error` in `.claude-plugin/scripts/livespec/commands/_revise_ratification_errors.py`
  rejects anything else with `ratification reviewer identity/model mismatch`. So
  with `ratification_reviewer_model: "fable"`, `reviewer_identity` must be the
  literal string `fable` — a descriptive agent name FAILS. This makes one of the
  two fields redundant; see §"Open findings not yet filed".
- **`verdict` must be the exact string `NO BLOCKERS`** — with a space. Not
  `NO-BLOCKERS`.
- **TWO decisions targeting the SAME spec file in ONE revise pass will
  SILENTLY DISCARD the first.** `_bind_resulting_files` applies decisions in
  order and each entry is a whole-file `write_text`, so the second decision's
  content overwrites the first's edit unless it already contains it. v204 and
  v205 both edit `contracts.md`; they were therefore run as **two sequential
  revise passes**, the second built on the first's output. Do the same, or
  compose both edits into the last decision's content.
- **`resulting_files[]` CAN reach outside the spec tree** via the `../` path
  form (`../.claude-plugin/prose/doctor.md`), the same mechanism
  `../tests/heading-coverage.json` uses. That is how v205 kept the contract and
  prose edits atomic.
- **`reviewed_at`** must be UTC ISO-8601 seconds, must not precede the
  proposal's `created_at`, and must be at least
  `ratification_min_review_age_seconds` (1) before the revise runs.
- **A ratifying PR needs a MANUAL merge, and the gate correctly withholds
  auto-merge** — `autoMergeRequest` was `null` on #2290, as designed. Core
  inherits the safe `manual` default. A proposal-FILING PR auto-merges while
  review is still running.

## Open findings not yet filed

Both surfaced during the 2026-08-14 review and are deliberately NOT folded into
v204/v205 — each deserves its own proposal rather than inflating a ratification.

- **`api_configurable_keys.json` path drift.** `contracts.md`'s
  §"Spec-governance control wrapper" paragraph names a committed manifest at
  `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`,
  which does NOT exist on master — it was relocated to
  `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json`
  in `d2ab3cbf`. Same defect class as the two just ratified. **Verify it is
  still true before filing** — this is exactly the kind of fact that expires.
- **`reviewer_identity` is redundant with `reviewer_model`.** The validator
  requires them equal, so the schema carries two required fields that can only
  ever hold one value. Either the identity field should record the actual
  reviewer (agent name / session) and be validated differently, or it should be
  dropped. This is a design question, not a typo — it needs a maintainer call.

One §"Wrapper CLI surface" row was deliberately NOT filed and still is not.
`revise` carries three flags absent from the whole spec tree —
`--post-step-doctor`, `--skip-stale-branch-check`, `--run-stale-branch-check` —
but that is INCOMPLETENESS, not contradiction: the table's preamble says each
wrapper "adds its own flags above that baseline", so nothing in the contract is
falsified. If a maintainer wants the table exhaustive, `revise` is the row to
add; that is a judgement call, not a defect.

## Open items

- **`livespec-dev-tooling-ep8n`** (P2, in the `livespec-dev-tooling` tenant) —
  pin autodiscovery misses workflow-template pins on BOTH directory and suffix.
  Shape DECIDED; HANDED OFF to that repo's groomer (maintainer chose HAND OFF
  on 2026-08-12), so it is listed here for continuity only and is not this
  thread's to advance. **Do not re-offer the choice — it was asked and
  answered.** See "What the next session must not re-derive".
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
- **A red CI job is not a failed check.** Seen AGAIN on 2026-08-14: eleven jobs
  red on a doc-only commit, every one failing at `mise trust + install` with an
  HTTP **503** fetching `shellcheck-v0.11.0` from GitHub's release CDN, each
  leaving its own `just check-*` step SKIPPED. Read the step list, not the job
  colour; re-run before diagnosing. The re-run passed all eleven.
- **Order a pin against the artifact, not the calendar.** Test tag containment
  with a control that DISCRIMINATES (ABSENT at `v0.31.0`, PRESENT at
  `v0.32.0`), never a bare presence check.
- **Gate affirmatively.** `decision == 'auto'`, never `!= 'blocked'`: an
  explicit `if:` on a job with `needs:` REPLACES the implicit success
  requirement, so a skipped or failed job yields an empty output that
  `!= 'blocked'` reads as permission.
- **Re-derive counts; never inherit them, including from a reviewer.** A brief
  written for the v205 reviewer stated "three total deltas against
  origin/master". It was FOUR — v204 carries two edits, not one. The reviewer
  caught it and said so. The composition was correct either way, but a wrong
  count in an evidence record reads as an unexplained extra hunk to the next
  verifier.
- **`origin/master` moves under you here.** It advanced FOUR times during one
  session on 2026-08-14 (`8e2b6453` → `280540db` → `d134fc6b` → `cd6b892b`).
  Re-verify replacement-target fidelity and re-hash any file your built bytes
  depend on immediately before ratifying; a fidelity result does not survive the
  next commit to `contracts.md`.
- **The `github_rate_limit_guard` hook matches loop keywords as SUBSTRINGS, in
  ordinary prose.** "be**for**e" and "**for** audit" both trip it. It ALSO
  denies `jq select(...)`. Write bodies to a file in one call and run `gh` in
  another; `map`/`filter` instead of a list comprehension.
- **You cannot background a gate command, and the hook's suggested remedy does
  not exist in this repo.** `pretooluse_background_guard` DENIES bare
  backgrounding of `just check*`, `git commit`, `git push` and `gh pr …`, and
  its hint tells you to use `just gate-start` / `just gate-wait`. **This repo's
  justfile has no such recipes** — confirmed by `just --list`. So the working
  pattern is a FOREGROUND call with a generous explicit timeout
  (`gh pr checks <n> --watch --interval 30`; a full `just check` took ~4 min and
  a push ~25s). Do not go hunting for the recipe.
- **CI egress/install flakes are frequent.** Signature: a dependency- or
  network-touching step fails (checkout TLS, `uv` fetching the
  `livespec-runtime` git dependency, `mise` installing shellcheck) and the check
  that NAMES the job is left `skipped`, so the job reads red having never run
  its own command. Threads `phase0-selfhosted-shadow-lane` and
  `livespec-ci-on-hetzner` own that surface; report, do not file into their lanes.

## Standing constraints

- Dedicated worktree per PR; never edit tracked files in
  `/data/projects/livespec`, the pane's cwd. After creating one:
  `just install-worktree-pack`, then `git checkout -- .livespec.jsonc`.
- Never `--no-verify`; halt and report on hook failure. Full `just check`
  before pushing.
- Each sibling repo governs itself — read its own rules before pushing there,
  and treat Red-Green-Replay scope as a per-repo question, not a fleet
  constant. A spec/docs-only changeset carries no product `.py` and is exempt.
- Another session lands on this `master` concurrently. Rebase; force-push ONLY
  your own branch. A dirty `plan/` file in the primary belongs to ANOTHER live
  session — examine, never discard.
- This repo rebase-merges, so one change has TWO SHAs. Ask the forge; never
  `--is-ancestor` on a branch tip. `git branch -d` warning "not yet merged to
  HEAD" is EXPECTED here and is not a signal of unmerged work.
- Never kill the acting overseer daemon (tmux `livespec-overseer:1.1`).
- Milestone trail: `tmp/overseer/spec-side-autonomy/worker-status.log`.
