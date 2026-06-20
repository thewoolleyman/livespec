# W7 orchestrator convergence handoff prompt

You are resuming W7 orchestrator-reference convergence in `/data/projects/livespec`.
This handoff owns the active W7 continuation state. Do not put W7 execution
state in `research/codex-support/handoff-prompt.md`; that file is for the
Codex-support track only.

## Current state as of 2026-06-20

W7 is not complete, but step 2's live golden-master acceptance harness is now
DONE and the GitHub permission gate is resolved. The remaining W7 work is steps
3-5 plus the diagram/template remainder.

Credential provisioned (USER-ACTION done):

- A dedicated disposable GitHub org `livespec-e2e` was created with a
  fine-grained token injected by the 1Password wrapper as
  `LIVESPEC_E2E_GITHUB_TOKEN` (Administration / Contents / Pull-requests /
  Workflows read-write, resource-owner-scoped to the org so the create/delete
  blast radius is contained to that throwaway org). Create + delete are proven.

Completed:

- The earlier Beads/Fabro dispatch-plumbing proof completed through
  `livespec-impl-beads-dn9`, `5qv`, and proof sentinels
  `w9d`/`law`/`uw8`/`0b7`/`6vo`/`ef5`. That proof showed the production
  orchestrator container can run Fabro through PR creation, merge, post-merge
  janitor `just check`, cleanup, and a green Dispatcher exit.
- `livespec-ei4i` is closed. The `livespec-impl-git-jsonl` hermetic
  hello-world acceptance harness landed in PR #92 at
  `19c9c09142480f657b633e637b0ebcfedd1a57d5`; it added `just acceptance` and
  the required CI acceptance gate.
- The Beads/Fabro hermetic and live-preflight acceptance tiers landed in
  `livespec-impl-beads` PR #99 at
  `ad6fd1c890f413369a5a422e2babaadd12052353`; it added `just acceptance`, the
  CI acceptance gate, `acceptance-live-preflight`, and
  `acceptance-live <item>`.
- `livespec-b8od` is CLOSED. The live Beads/Fabro golden-master acceptance
  proof was genuinely met end-to-end and independently reproduced
  (livespec-impl-beads PR #101, merge `e2ee88e`, master CI green). It added a
  minimal livespec-impl skeleton (`orchestrator-image/e2e-skeleton/`),
  embedded-mode ephemeral beads ledger, `acceptance-live-golden-master.sh`,
  the `just acceptance-live-golden-master` target, the Red-Green-Replay-bound
  live greeting assertion, and a `workflow_dispatch` CI job. The unmodified
  production Fabro workflow dispatched the greeting work-item into a sandbox,
  Claude implemented `greet()`, a real PR was created and merged, and the
  greeting assertion was green from the merged repo.
- `livespec-zkmn.1.2` (the reaper) is CLOSED. A standalone
  `orchestrator-image/reap-e2e-repos.sh` plus `just reap-e2e-repos` landed in
  livespec-impl-beads PR #100, wired into the live flow on entry-sweep and
  EXIT-teardown. Zero leaks observed across 9+ runs.
- `livespec-1oe9` (runtime-matrix evidence) is satisfied by the
  documentation PR that added the "Acceptance runtime-matrix evidence (W7
  step 2)" section to `research/codex-support/family-audit.md`. (That item is
  closed by the maintainer, not by an agent.)

Remaining W7 work (under `livespec-zkmn.1`):

- Step 3 — memo kill (`livespec-gjn4`, `livespec-kfiz`, `livespec-d4j3`):
  spec-first via propose-change -> revise; it touches the contract.
- Step 4 — shared `Store` extraction (`livespec-4jsi`, `livespec-6a4n`,
  `livespec-5g4i`): a coordinated cross-repo version-bump fan-out.
- Step 5 — promote the container image to the real-work substrate
  (`livespec-pe9u`).
- `livespec-b91b`: diagram/template remainder disposition.

Once steps 3-5 and `livespec-b91b` land, close `livespec-zkmn.1` then
`livespec-zkmn` — which unblocks the orchestrator rename wave `4moata.4`.

## Next action

Step 2 is COMPLETE. Proceed to steps 3-5. Each is substantial:

1. The memo kill (step 3) is spec-first and touches the contract, so drive it
   through `/livespec:propose-change` -> `/livespec:revise` before any impl
   change.
2. The shared `Store` extraction (step 4) is a coordinated cross-repo bump:
   extract once, then fan the version bump out to every consumer repo.
3. Promote the container image to the real-work substrate (step 5).

Do not start the orchestrator rename work or any non-W7 epic from this handoff.
The rename wave `4moata.4` is downstream of W7 and remains out of scope until
`livespec-zkmn` is closed.

## Work discipline

Every tracked repo change still uses worktree -> PR -> merge -> cleanup. Use
`mise exec -- git ...` so hooks run, never pass `--no-verify`, and do not leave
dirty primary checkouts or orphaned worktrees. If a future session must stop,
update this file with the active worktree path, branch, PR, validation state,
and next action.
