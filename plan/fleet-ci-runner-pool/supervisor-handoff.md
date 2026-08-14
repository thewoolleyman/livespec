# Supervisor handoff — fleet-ci-runner-pool

**Ledger epic:** `livespec-s43svm`.

This file is the sole resume state for the next supervisor session. Read it
fully, then inspect the named ledger records before acting. The previous
round-six narrative is historical; it does not describe the current active
work or containment state.

## Current state

The fleet routing plan is active, but the PowerEdge JIT runner supervisor is
**intentionally stopped**. Do not restart it casually. A live rollout found
that the supervisor startup configuration omitted
`thewoolleyman/livespec-dev-tooling:63`; that omission was corrected on
`poweredge-xubuntu` in
`/etc/systemd/system/ci-runner-supervisor.service.d/poweredge.conf`, with a
backup named `poweredge.conf.bak-dev-tooling-20260813T164104Z`.

After the correction, startup fan-out minted hundreds of GitHub App
installation-token/JIT-config requests concurrently. GitHub returned
secondary and installation API throttles. Three controlled ten-minute
cooldown/restart cycles reproduced the throttle. Each time the supervisor was
stopped immediately to prevent a retry storm. The corrected drop-in is
retained; the service is currently inactive. Detailed request IDs, timestamps,
and runner/proof observations are recorded on `livespec-s43svm.1` and in
`tmp/overseer/fleet-ci-runner-pool/worker-status.log` (runtime-only).

The affected proof is GitHub Actions run `31753189341` in
`thewoolleyman/livespec-dev-tooling`: it remains queued with 61 matrix jobs
queued and two completed. The worker had a `gh run watch` process attached at
wind-down. Do not create another mint burst merely to make this proof move.

## Active ledger work

- `livespec-s43svm.1` — fleet-wide self-hosted rollout. It is active and
  contains the throttling/containment evidence. External GitHub throttling is
  the current operational block.
- `livespec-s43svm.2` — cache relocation: completed through
  `livespec-dev-tooling` PR #1397, merged and cleaned up. Do not revisit the
  unrelated dirty worktree `~/.worktrees/livespec-dev-tooling/relocate-warm-cache-tier`.
- `livespec-s43svm.3` / `.4` — later cache/Nix plan items; not current.
- `livespec-s43svm.5` — **active, newly captured**:
  `Rate-limit-aware JIT runner supervisor admission controller`. It is a
  direct child of this epic, targets `livespec-dev-tooling`, and implements
  the specification commitment below. Its acceptance requires bounded paced
  admission, shared cooldown/backoff, restart no-reburst, terminal retry
  exhaustion, and a controlled fleet proof with no throttle.

## Specification-first implementation path

The required spec amendment was proposed and revised before `.5` was filed.

- Proposal: `SPECIFICATION/proposed_changes/runner-supervisor-rate-limit-control.md`
  (now ratified into history).
- Revisions: `v044` (rate-control commitment) and `v045` (static EOF
  correction).
- Contract: `SPECIFICATION/non-functional-requirements.md` §"JIT runner
  supervisor GitHub request discipline".
- Spec PR: `thewoolleyman/livespec-dev-tooling#1398`, branch
  `spec/runner-supervisor-rate-limit-control`, commit `c5b57602`.
- PR #1398 has no failed checks and auto-merge is enabled, but its CI is
  queued because runner capacity is intentionally contained by the GitHub
  throttle. Its owned worktree is
  `~/.worktrees/livespec-dev-tooling/spec/runner-supervisor-rate-limit-control`.
  Do not edit or remove it while that PR remains unmerged.

Once PR #1398 merges, direct the worker assigned to `.5` to implement the
commitment in a new, owned `livespec-dev-tooling` worktree using the normal
test-first, PR, merge, and cleanup workflow. It may do read-only mapping
before the merge, but must not implement a competing contract before the spec
is durable.

## Safe next actions after restart

1. Read `livespec-s43svm`, `.1`, and `.5` comments; they are the detailed
   audit timeline.
2. Verify `systemctl is-active ci-runner-supervisor.service` on
   `poweredge-xubuntu` is still inactive and that the corrected drop-in exists.
3. Do not restart the runner supervisor without a new, rate-safe recovery
   decision. The present external block is GitHub throttling, not a missing
   label, credential, or runner directory.
4. Monitor PR #1398 and drive `.5` once the spec PR lands. Keep `.1`'s proof
   run as evidence; do not fabricate a no-op code change just to trigger CI.
5. The prior supervisor/worker session must be wound down before a new one
   starts. Do not trust runtime files as durable handoff; this file and the
   ledger are authoritative.

## Guardrails

- All tracked changes: dedicated worktree → PR → required checks → rebase
  merge → primary refresh → worktree/branch cleanup. Never commit on a
  primary checkout and never use `--no-verify`.
- Do not touch any worktree you do not own, especially the dirty
  `relocate-warm-cache-tier` worktree named above.
- The exact primary-checkout runtime exception is only
  `tmp/overseer/<topic>/`; it does not authorize tracked edits there.
- Do not route global `next` candidates into this epic. Work only the epic’s
  own children.
