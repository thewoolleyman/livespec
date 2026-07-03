# Handoff — fleet-merged-branch-cleanup

The single resumable entry point for the **fleet merged-branch cleanup**
thread: make every fleet repo delete merged-PR head branches automatically
and identically, enforced DRY via `livespec-dev-tooling` shared logic. A
fresh session can execute the next action from this file alone via the
read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** Only `livespec` (core) and `livespec-driver-claude`
  have GitHub's `delete_branch_on_merge` repo setting on; the other six
  fleet repos have it off and have accumulated ~460 stale remote branches
  (evidence table + full design: the read-first chain's
  `research/01-evidence-and-design.md`). Four pieces: (1) operator setting
  rollout, (2) one-time merged-stale sweep (dev-tooling module,
  factory-built, operator-run), (3) the durable fleet-conformance Verifier
  in dev-tooling (the DRY enforcement), (4) provisioning parity for new
  fleet members. Plus one maintainer decision (adopter scope) and one
  self-resolved recommendation (spec codification via propose-change).
- **Epic anchor:** `livespec-ixap` (livespec core tenant, `backlog`).
  Status is READ from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-ixap
  ```
- **Working model.** A livespec-core session coordinates (the invariant is
  fleet-wide, so the anchor lives in core); the dev-tooling code work
  (sweep module + Verifier) is filed and factory-dispatched into the
  `livespec-dev-tooling` tenant via `bd -C /data/projects/livespec-dev-tooling`
  + `real-work-dispatch.sh --target-repo livespec-dev-tooling`; the
  settings PATCH and the sweep execution are OPERATOR steps (repo-admin
  `gh` auth; the fleet App token was not provisioned for Administration —
  verify before assuming otherwise).
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready,
  factory-safe slices through the factory — NEVER hand-code the
  dev-tooling module or Verifier inline in the planning session.
- **⚑ Dispatch mechanics (proven, fleet-followups Session 15, 2026-07-03):**
  promote `backlog→ready` + `--add-label admission:auto --add-label
  acceptance:ai-only` + a formal `--acceptance` field, then
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh \
    bash /data/projects/livespec-orchestrator-beads-fabro/orchestrator-image/real-work-dispatch.sh \
    --target-repo livespec-dev-tooling --item <ready-id> --run
  ```
  `--target-repo` takes the bare repo NAME. Dispatches are strictly
  SERIAL — a second concurrent dispatch kills the in-flight one (open
  beads-fabro bug `bd-ib-h55`). The pre-dispatch conformance gate
  hard-blocks on ANY tenant item with beads-native `open` status —
  normalize stragglers `open→backlog` first (open beads-fabro bug
  `bd-ib-cur` tracks the systemic fix). The `bd` mutation forms (all under
  the same `with-livespec-env.sh` wrapper): file =
  `bd -C <repo-path> create "<title>" -t task -p 2 -d "<desc>" --acceptance "<criteria>" --labels origin:freeform`;
  normalize = `bd -C <repo-path> update <id> --status backlog`; promote =
  `... update <id> --status ready --add-label admission:auto --add-label acceptance:ai-only`;
  close = `... update <id> --status closed` (+ a completion comment via
  `bd -C <repo-path> comment <id> "<text>"`).
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-merged-branch-cleanup`.

## The next action

Execute the kickoff, in order:

1. **Compose status LIVE.** `bd show livespec-ixap` (command above), and
   re-verify the per-repo settings — the evidence table is a snapshot:
   ```bash
   for repo in livespec livespec-dev-tooling livespec-driver-claude livespec-driver-codex livespec-orchestrator-beads-fabro livespec-orchestrator-git-jsonl livespec-runtime livespec-console-beads-fabro openbrain; do
     echo -n "$repo: "; gh api "repos/thewoolleyman/$repo" --jq .delete_branch_on_merge
   done
   ```
   (`openbrain` is the adopter — it stays in the verification loop only if
   the step-2 decision accepts the opportunistic-PATCH recommendation.)
   To check whether the fleet App could automate the rollout instead of
   the operator, inspect its granted permissions with
   `gh api user/installations --jq '.installations[] | {app_slug, permissions}'`
   and look for `administration: write` — absent means operator-only.
2. **Settle the adopter-scope decision with the maintainer** (structured
   picker, recommendation first): Verifier binds the manifest `fleet`
   array only; PATCH openbrain opportunistically. Rationale in the
   research note §"Decision for the maintainer".
3. **Operator rollout** — for each repo still `false`:
   `gh api -X PATCH repos/thewoolleyman/<repo> -F delete_branch_on_merge=true`,
   then re-run the step-1 loop to confirm all `true`.
4. **File + DoR + dispatch the two dev-tooling work-items** (tenant
   `livespec-dev-tooling`, filed from this session via `bd -C`; normalize
   each new item `open→backlog` immediately):
   - *Sweep module*: enumerate remote branches per fleet repo (repo list
     read from livespec core's `.livespec-fleet-manifest.jsonc`, never
     hardcoded); a branch is sweepable ONLY if it is the head of a MERGED
     PR and has no open PR and is not `master`/`release` (PR-state, not
     ancestry — the fleet rebase-merges); `--dry-run` default with
     per-repo report; unit-tested against a fake API seam; full
     `just check` green.
   - *Fleet-conformance Verifier*: assert `delete_branch_on_merge == true`
     for every `fleet`-array repo; manifest-driven like the existing
     fleet-conformance checks; always wired into `just check`; one
     warn-vs-fail env lever (no-token local → WARN; CI with token → FAIL);
     unit-tested; full `just check` green.
   Dispatch each serially via the mechanics block above.
5. **Run the sweep** (operator): `--dry-run` first, review the per-repo
   report, then the real run; expect the branch counts in the research
   note to collapse to near-zero on the six affected repos.
6. **Provisioning parity + spec proposal.** File the
   `wire_fleet_member`/onboarding parity change as a third dev-tooling
   item (factory), and file the livespec-core spec clause via
   `/livespec:propose-change` (content maintainer-gated at the next
   attended `/livespec:revise` — do NOT auto-revise).
7. **Verify the invariant end-to-end, then close.** All repos `true`, a
   consumer repo's `just check` runs the Verifier green, stale counts
   swept → close `livespec-ixap` (with the PR map in the completion
   comment) and archive this thread
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
