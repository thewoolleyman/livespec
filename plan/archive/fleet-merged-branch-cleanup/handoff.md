# Handoff — fleet-merged-branch-cleanup

The single resumable entry point for the **fleet merged-branch cleanup**
thread: make every fleet repo delete merged-PR head branches automatically
and identically, enforced DRY via `livespec-dev-tooling` shared logic. A
fresh session can execute the next action from this file alone via the
read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** Four pieces: (1) operator setting rollout — **DONE
  2026-07-04** (all nine repos `true`, see §"State snapshot"); (2) one-time
  merged-stale sweep (dev-tooling module, factory-built, operator-run) —
  in flight; (3) the durable fleet-conformance Verifier in dev-tooling —
  filed, not yet dispatched; (4) provisioning parity for new fleet
  members — filed, not yet dispatched. Evidence table + full design:
  the read-first chain's `research/01-evidence-and-design.md`.
- **Epic anchor:** `livespec-ixap` (livespec core tenant). Status is READ
  from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-ixap
  ```
- **Working model.** A livespec-core session coordinates; the dev-tooling
  code work is filed in the `livespec-dev-tooling` tenant and
  factory-dispatched via `real-work-dispatch.sh`; the sweep execution is
  an OPERATOR step (repo-admin `gh` auth; no App has Administration —
  verified 2026-07-04).
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready,
  factory-safe slices through the factory — NEVER hand-code the
  dev-tooling module or Verifier inline in the planning session.
- **⚑ Dispatch mechanics:** promote `backlog→ready` + `--add-label
  admission:auto --add-label acceptance:ai-only` + a formal
  `--acceptance` field, then
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh \
    bash /data/projects/livespec-orchestrator-beads-fabro/orchestrator-image/real-work-dispatch.sh \
    --target-repo livespec-dev-tooling --item <ready-id> --keep-container --run
  ```
  `--target-repo` takes the bare repo NAME. Dispatches are strictly
  SERIAL — a second concurrent dispatch kills the in-flight one (open
  beads-fabro bug `bd-ib-h55`). The pre-dispatch conformance gate
  hard-blocks on ANY tenant item with beads-native `open` status —
  normalize new items `open→backlog` immediately after `bd create`
  (open beads-fabro bug `bd-ib-cur` tracks the systemic fix). The `bd`
  mutation forms (all under the same `with-livespec-env.sh` wrapper;
  the dev-tooling tenant's `<repo-path>` is literally
  `/data/projects/livespec-dev-tooling`):
  file = `bd -C <repo-path> create "<title>" -t task -p 2 -d "<desc>"
  --acceptance "<criteria>" --labels origin:freeform`; normalize =
  `bd -C <repo-path> update <id> --status backlog`; promote =
  `... update <id> --status ready --add-label admission:auto --add-label
  acceptance:ai-only`; close = `... update <id> --status closed` (+ a
  completion comment via `bd -C <repo-path> comment <id> "<text>"`).
- **⚑ Publish-token hazard (why `--keep-container` above is REQUIRED
  until fixed).** The in-sandbox PR node rides the GH_TOKEN projected at
  sandbox creation; a run whose implement/janitor/review legs exceed the
  ~60-minute installation-token TTL FAILS at publish with the work
  committed inside the sandbox, and without `--keep-container` the
  dispatcher's EXIT trap destroys that work (this killed dispatch 1 of
  `livespec-dev-tooling-iia`, 79 min, 2026-07-03). Filed as **P1
  `bd-ib-4sy`** in the `livespec-orchestrator-beads-fabro` tenant
  (sibling of `bd-ib-umno37`; read either via
  `bd -C /data/projects/livespec-orchestrator-beads-fabro show <id>`
  under the same wrapper). With `--keep-container`, rescue a
  publish-failed run from the preserved container:
  ```bash
  # inner sandbox name: docker exec livespec-orch-realwork docker ps
  docker exec livespec-orch-realwork docker exec <fabro-run-...> \
    git -C /workspace/livespec-dev-tooling log --oneline origin/master..HEAD
  # then push that HEAD to feat/<item-id> with fresh auth (operator gh
  # or a freshly minted App installation token), open the PR, arm
  # auto-merge, and after merge close the item with a completion comment.
  # Finally: docker rm -f livespec-orch-realwork
  ```
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-merged-branch-cleanup`.

## State snapshot (2026-07-04, verify live before acting)

- **Rollout DONE:** `delete_branch_on_merge` verified `true` on all nine
  repos (eight fleet + openbrain). Re-verify:
  ```bash
  for repo in livespec livespec-dev-tooling livespec-driver-claude livespec-driver-codex livespec-orchestrator-beads-fabro livespec-orchestrator-git-jsonl livespec-runtime livespec-console-beads-fabro openbrain; do
    echo -n "$repo: "; gh api "repos/thewoolleyman/$repo" --jq .delete_branch_on_merge
  done
  ```
- **Adopter-scope decision SETTLED (maintainer, 2026-07-04):** the
  Verifier binds the manifest `fleet` array ONLY; openbrain was PATCHed
  opportunistically and codified its own invariant via its own livespec
  lifecycle (openbrain `SPECIFICATION/constraints.md` §"Merged-branch
  cleanup", revision v093, commit `2e91919` on openbrain `main`).
- **Ledger items (livespec-dev-tooling tenant):**
  `livespec-dev-tooling-iia` (sweep module — dispatch 1 failed at
  publish per the token hazard above; dispatch 2 failed at the Red
  commit because dev-tooling MASTER CI went red at 2026-07-03T23:19Z,
  see the next bullet),
  `livespec-dev-tooling-g8j` (Verifier — `backlog`, dispatch after iia),
  `livespec-dev-tooling-5o2` (provisioning parity — `backlog`, dispatch
  after g8j).
- **Red-master interlude (2026-07-04, RESOLVED).** Between dispatches
  1 and 2, another track's commit (`ad807ea`, "feat: enforce Claude
  plugin currency wiring") added the `claude-plugin-currency`
  fleet-conformance row at error severity with zero members wired —
  dev-tooling master CI went red by construction and
  `check-master-ci-green` blocked every factory Red commit (dispatch
  2 died there). The owning track repaired it themselves at
  2026-07-04T00:08Z (`caab92a`: row demoted to warning until the
  core-tenant `livespec-c1k9.11` rollout flips it back, PLUS the
  `LIVESPEC_MASTER_CI_GREEN=warn` repair lever that breaks the
  repair-circularity). This thread's parallel repair PR
  https://github.com/thewoolleyman/livespec-dev-tooling/pull/248 was
  closed as superseded, and its follow-up items
  (`livespec-dev-tooling-h7z`, `livespec-dev-tooling-3ab`) closed as
  duplicate/already-fixed. If a dispatch ever fails at the Red commit
  with a `check-master-ci-green` message again, check master CI
  first:
  ```bash
  gh run list --repo thewoolleyman/livespec-dev-tooling --workflow CI --branch master --limit 1
  ```
- **Core spec proposal FILED + merged (proposal only):**
  `SPECIFICATION/proposed_changes/fleet-merged-branch-cleanup.md` via
  https://github.com/thewoolleyman/livespec/pull/824. Content is
  maintainer-gated at the next attended `/livespec:revise` — do NOT
  auto-revise. (At that revise, the clause adds no `## ` heading, so no
  `tests/heading-coverage.json` co-edit is owed.)

## The next action

1. **Confirm dev-tooling master CI is green** (command in the
   §"Red-master interlude" bullet). Nothing in that repo can be
   dispatched or committed normally while master is red; if it is red
   again, root-cause the new breakage first.
2. **Settle `livespec-dev-tooling-iia` and re-dispatch.** Classify
   from durable state (a fresh session has no handle to the launching
   session's processes):
   ```bash
   # (a) ledger status: closed = success; active/ready = not settled
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec-dev-tooling show livespec-dev-tooling-iia
   # (b) did a PR publish and merge?
   gh pr list --repo thewoolleyman/livespec-dev-tooling --state all --head feat/livespec-dev-tooling-iia
   # (c) is a preserved orchestrator container still around?
   docker ps -a --filter name=livespec-orch-realwork
   ```
   Outcome mapping: PR merged + item closed → SUCCESS:
   `docker rm -f livespec-orch-realwork`, proceed to step 3. PR open
   or run still in flight (item `active`, container up, no terminal
   state) → WAIT: re-run the probes until it settles, then
   re-classify. No PR + container present + committed work inside
   (the `git log origin/master..HEAD` probe in the §"Publish-token
   hazard" block) → PUBLISH FAILURE: rescue per that block. No PR +
   no committed work (or container gone) → re-dispatch: normalize the
   item to `ready` if needed and dispatch per the mechanics block
   (with `--keep-container`). As of this handoff's writing dispatch
   attempt 3 was launched 2026-07-04 (after the red-master interlude
   resolved), so the probes above most likely find it settled or in
   flight.
3. **Dispatch `livespec-dev-tooling-g8j`** (promote + dispatch per the
   mechanics block; serial — only after step 2 fully settles).
4. **Dispatch `livespec-dev-tooling-5o2`** (same, after step 3).
5. **Run the sweep** (operator): `--dry-run` first, review the per-repo
   report, then the real run; expect the ~460 stale branches in the
   research note's table to collapse to near-zero on the six affected
   repos. NEVER delete a branch that is not a merged-PR head.
6. **Verify the invariant end-to-end, then close.** All repos `true`, a
   consumer repo's `just check` runs the Verifier green, stale counts
   swept → close `livespec-ixap` (completion comment carrying the PR
   map: openbrain `2e91919`, core PR #824, plus the three dev-tooling
   PRs) and archive this thread
   (`git mv plan/fleet-merged-branch-cleanup/ plan/archive/`).

## Read-first chain (in order)

1. **`research/01-evidence-and-design.md`** — the verified evidence table,
   the four design pieces with their implementation homes, the adopter
   decision, and the deliberate out-of-scope list. (The only companion
   file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-merged-branch-cleanup
```
