# W7 orchestrator convergence handoff prompt

You are resuming W7 orchestrator-reference convergence in `/data/projects/livespec`.
This handoff owns the active W7 continuation state. Do not put W7 execution
state in `research/codex-support/handoff-prompt.md`; that file is for the
Codex-support track only.

## Current state as of 2026-06-20

W7 is not complete. Step 2's golden-master acceptance harness is partially
landed and blocked on a user-action GitHub permission gate.

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

Blocked:

- `livespec-b8od` remains open and blocked with `blocked:github-create-repo`.
  The remaining acceptance proof requires the live throwaway GitHub tier:
  create a `livespec-e2e-*` repository, seed the fixture, run the production
  container/Fabro path, create and merge the generated PR, assert the greeting
  from the merged repo, then delete or reap the throwaway repo.
- The current `LIVESPEC_FAMILY_GITHUB_TOKEN` authenticates but cannot create
  repositories. A smoke create of `livespec-e2e-permission-smoke-*` failed with
  `GraphQL: Resource not accessible by personal access token (createRepository)`.
  Agents must not try to bypass this by weakening the acceptance proof.
- `livespec-1oe9` is blocked behind `livespec-b8od`; it records runtime-matrix
  evidence only after the step-2 acceptance proof is complete.

Queued after step 2:

- `livespec-gjn4`, `livespec-kfiz`, and `livespec-d4j3`: memo kill.
- `livespec-4jsi`, `livespec-6a4n`, and `livespec-5g4i`: shared `Store`
  extraction and consumer fan-out.
- `livespec-pe9u`: promote the container image to the real-work substrate.
- `livespec-b91b`: diagram/template remainder disposition.

## Next action

Wait for, or ask the user to provide, a dedicated GitHub token or GitHub App
credential that can create and delete repositories in the required namespace
for `livespec-e2e-*` throwaway repos.

After that credential exists:

1. Resume `livespec-b8od` in `livespec-impl-beads`.
2. Run the live acceptance proof through the production container/Fabro path
   using `just acceptance-live <item>` or the repository's current equivalent.
3. Verify that the run creates the throwaway repo, opens and merges the PR,
   asserts the generated greeting from the merged repo, and cleans up the repo.
4. Close `livespec-b8od` only after that live proof is green.
5. Continue `livespec-1oe9` for the runtime-matrix evidence.

Do not start the orchestrator rename work or any non-W7 epic from this handoff.
The rename wave is downstream of W7 and remains out of scope until W7 is closed.

## Work discipline

Every tracked repo change still uses worktree -> PR -> merge -> cleanup. Use
`mise exec -- git ...` so hooks run, never pass `--no-verify`, and do not leave
dirty primary checkouts or orphaned worktrees. If a future session must stop,
update this file with the active worktree path, branch, PR, validation state,
and next action.
