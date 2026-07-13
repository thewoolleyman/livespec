# Handoff — codex-acp version auto-bump (factory-gated freshness)

**State (SHIPPED, 2026-07-13).** All code is built and merged across both owning
repos. The App permission grant is **DONE** (2026-07-13 —
`Commit statuses: Read & write` granted and approved on the installation). The
**only remaining maintainer-gated step** is one credentialed force-accept, after
which epic `livespec-3lev.4` (the last Phase 1 deliverable) closes. This document
is a self-sufficient resume anchor — whoever picks this up can run the accept and
close the epic from here alone. See `design.md` beside this file for the
architecture and the corrected mechanics.

## What shipped (all merged)

### `livespec-orchestrator-beads-fabro` (released 0.30.0, master tip 19fa82a)

- **PR-A #572** — version-less fetch-free adapter.
  `_dispatcher_fabro_argv.py`: `CODEX_IMPLEMENTER_ADAPTER = "npx --no-install
  @zed-industries/codex-acp"` (dropped `@0.16.0`, added `--no-install`). The two
  hardcoded-string tests updated. Independently valuable: the adapter launch is
  now network-free even without the automation.
- **PR-C gate #574** — `acceptance-live-golden-master.yml` gained a
  `repository_dispatch` trigger, a `--codex-acp-version` runtime overlay (`npm
  install -g @zed-industries/codex-acp@<ver>` prepare-step on the released image —
  OPTION 3, no candidate image), and a `codex-acp-golden-master` commit-status
  callback. Inert until dispatched.
- **PR-C-followup #579** — on a **green** gate run (repository_dispatch), the job
  enables the dev-tooling bump PR's auto-merge via the `livespec-pr-bot` App token
  (contents + pull-requests write). This IS the fail-closed merge gate.

### `livespec-dev-tooling` (PR-B #371, merged)

One PR carrying spec + code:
- Spec: propose `964cd49` + ratify `contracts.md` **v025** `2f1962c` — adds the
  6th autodiscovery pin format, the 2nd cross-repo event type
  (`codex-acp-golden-master`), the App's `statuses:write` requirement, and the
  factory-gate subsection. **Ratified as v025** — the revise was rebuilt from
  v024 → v025 after a concurrent v024 (`neutral-shared-hook-body`) landed on
  dev-tooling master first.
- Code `81b7da3` — the autodiscovery walker + `codex_acp_pin_rewrite` module +
  the composite-action rewrite arm + the `no_auto_merge` bump-PR mode + the
  freshness scan (queries `npm view @zed-industries/codex-acp version`, opens the
  bump PR, fires the cross-repo dispatch) + doc sweeps + a coverage-incremental
  flaky-test fix (per-invocation tempdir). `just check` 54 green; Red-Green-Replay
  trailers present.

The `park-parity` proposal on dev-tooling is **left pending** (untouched — not
part of this epic).

## Ratified cross-repo contract (dev-tooling `contracts.md` v025)

- **event_type** `codex-acp-golden-master`; payload `{codex_acp_version,
  head_sha, pr_number, source_repo: "livespec-dev-tooling"}`.
- **status context** `codex-acp-golden-master` (success|failure) posted to the
  dev-tooling head_sha via the `livespec-pr-bot` App token (owner
  `thewoolleyman`, repo `livespec-dev-tooling`).
- **Topology = OPTION 3 runtime overlay** — the gate runs the golden-master with
  an `npm install -g @zed-industries/codex-acp@<ver>` prepare-step (NO candidate
  image). Requires the orchestrator adapter be version-less (`npx --no-install`) —
  DONE in PR-A.
- **Merge gate = FAIL-CLOSED, NO required check** — the bump PR is opened WITHOUT
  auto-merge; a green gate ENABLES auto-merge; a red/errored gate leaves it open
  for a human. (A required check is impossible here: GitHub scopes required
  checks to the base branch, so it would deadlock every unrelated PR, and it
  violates dev-tooling's §"branch_protection_alignment check".) The cross-repo
  status is informational.
- **Pin source = npm** (`npm view @zed-industries/codex-acp version`), bump on
  ANY difference. `source_repo` for the pin is `zed-industries/codex-acp`.

## Independent Fable review

The dev-tooling PR-B spec ratification got an independent, read-only adversarial
Fable review before accept: **NO-BLOCKERS** verdict (after 3 blocker fixes + 3
concern fixes were applied). The chief blocker fix — Fable concern 1 — is the
merge-gate mechanic correction now recorded in `design.md`: gate-enables-auto-
merge, NOT a branch-protection required check.

## Lesson learned — the Codex sandbox constraint (record for future cross-repo work)

`codex:codex-rescue` scopes Codex's sandbox to the **current session's repo** and
mounts `$HOME/.worktrees` and `.git/refs` **read-only**; writes to
`/data/projects/<repo>` working files ARE allowed. Consequence: Codex **cannot**
run the worktree → commit → push → PR flow on sibling repos from a core session.
The working model adopted here was "Codex authors, I git-plumb": Codex edits
files in the primary checkout on master and validates targeted (no git); a Claude
agent does the stash → worktree → Red-Green-Replay → push → PR. PR-B's code was
built by a Claude agent for this reason.

## REMAINING — the only open items (maintainer-gated)

The maintainer chose "merge all + force accept." Step 1 (App permission grant) is
**DONE** (2026-07-13); steps 2–3 below are all that remains; run them in order.

### 1. App permission grant — ✅ DONE (2026-07-13)

On 2026-07-13, `Commit statuses: Read & write` was added to the
`livespec-pr-bot` GitHub App's default repository permissions, and the permission
update was **approved on the installation** (the installation covers
`livespec-dev-tooling` plus the other fleet repos). Verified on the installation
page, which now shows the App holding "Read and write access to code, commit
statuses, pull requests, and workflows" (plus Read access to metadata). So the
gate's cross-repo status callback can now post the `codex-acp-golden-master`
commit status to `livespec-dev-tooling` — it will no longer 403.

(For the record, the original to-do was: `github.com/settings/apps/livespec-pr-bot`
→ **Repository permissions** → **Commit statuses** → **Read & write** → **Save**,
then approve the new permission on the installation.)

### 2. Force-accept — exercise the gate end-to-end (credentialed / costly — surface before firing)

"Done means exercised live." Fire a real `codex-acp-golden-master` dispatch and
journal the live evidence on the epic:

1. Open a **throwaway dev-tooling PR** bumping `CODEX_ACP_VERSION` in
   `docker/fabro-sandbox/base/Dockerfile`. Use a **known-good** version (e.g.
   `0.16.0`, the empirically-verified baseline) so the overlay + projection are
   exercised on the happy path. Note its **head_sha** and **PR number**.
2. Fire the dispatch (needs the App token / a token with `repository_dispatch`):

   ```bash
   gh api repos/thewoolleyman/livespec-orchestrator-beads-fabro/dispatches \
     -f event_type=codex-acp-golden-master \
     -F 'client_payload[codex_acp_version]=0.16.0' \
     -F 'client_payload[head_sha]=<HEAD_SHA>' \
     -F 'client_payload[pr_number]=<PR_NUMBER>' \
     -f 'client_payload[source_repo]=livespec-dev-tooling'
   ```

3. Watch the self-hosted golden-master run. **Verify:** the overlay installs the
   requested version; the Codex golden-master goes green **including credential
   projection** (`project_codex_auth_snapshot`); the `codex-acp-golden-master`
   commit status is posted to the head_sha; and the bump PR's **auto-merge is
   enabled** by #579.
4. Journal this live-exercise evidence on epic `livespec-3lev.4` (per "done means
   rolled out and exercised live"). Close/discard the throwaway bump PR.

Simpler-but-insufficient alternative: `gh workflow run
acceptance-live-golden-master.yml -f mode=run` proves the version-less
golden-master works (accepts PR-A) but does NOT exercise the cross-repo
dispatch / callback / auto-merge. The full `repository_dispatch` above is the
real accept.

### 3. Close the epic

After the force-accept is journaled, close epic `livespec-3lev.4` — the last
Phase 1 (`fabro-ci-image-factoring`) deliverable. This closes Phase 1.

## Follow-ups (non-blocking)

- **dev-tooling `contracts.md` `workflows: write` drift.** While granting the
  commit-status permission (step 1), it was observed that the `livespec-pr-bot`
  App **already holds `Workflows: Read & write`** (added earlier for the
  cross-repo bump-pin `uses:`-ref automation). But dev-tooling's
  `SPECIFICATION/contracts.md` §"GitHub App auth model" enumerates only
  `contents: write`, `pull-requests: write`, `metadata: read` (and now
  `statuses: write` via v025) — it does **not** list `workflows: write`. A minor
  future `contracts.md` sweep should add `workflows: write` to that permission
  list to end this pre-existing drift. **Not blocking this epic.**

## Cross-references

- Design: `plan/codex-acp-auto-bump/design.md` (see §"Build outcome (2026-07-13)"
  for the corrected mechanics).
- Parent epic: `livespec-3lev` (`fabro-ci-image-factoring`), Phase 1 `.4`
  (journal the accept there). Parent handoff:
  `plan/fabro-ci-image-factoring/handoff.md`.
- Credential-projection tracker: `bd-ib-ss7rkr` — the whole point of the gate is
  to re-verify `project_codex_auth_snapshot` on each bump.
- No-Circular-Dependency Directive: `.ai/no-circular-dependency.md` — the version
  lives in dev-tooling; the credential test is orchestrator-side; the coupling is
  an event dispatch + status callback, never a code read from dev-tooling into
  the orchestrator.
