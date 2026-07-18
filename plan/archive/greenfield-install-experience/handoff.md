# Handoff — greenfield-install-experience

This plan thread is complete and archived.

The greenfield install experience work replaced the old install guide
with the paste-able idempotent installer prompt
(`docs/livespec-installation-prompt.md`, pointed at by the minimal
`docs/installation.md`), live-tested the published path through the
resume adopter (`github.com/thewoolleyman/resume`), fixed the live-test
friction that surfaced, and closed the remaining residual
`livespec-p340`.

## Final State

- **Epic:** `livespec-rh0i` in the livespec repository Beads tenant is
  closed. It carries the completion comment naming the doc PR sequence,
  resume verification evidence, and final residual fix.
- **Final child residual:** `livespec-p340` is closed. The factory fix
  landed in livespec repository PR #1334:
  https://github.com/thewoolleyman/livespec/pull/1334
- **Merge evidence:** PR #1334 merged at `2026-07-18T11:19:29Z` as
  `84176a17d5f088d66db0a5a103e34a57142898f0`.
- **Validation evidence:** PR #1334 CI completed with 68 successful
  jobs and the telemetry export job skipped. The dispatcher acceptance
  read observed the merged diff and green PR telemetry, verdict `PASS`,
  then `accept:livespec-p340` moved the item from `acceptance` to
  `done`.
- **Resume live-test evidence:** On 2026-07-04, the resume repository
  verification proved both Claude and Codex harnesses installed and ran
  the expected livespec surfaces through the published path. Seed
  idempotency refusal exited 3 and left the tree untouched in both
  harnesses. The only residual from that verification was the silent
  stderr bug fixed by `livespec-p340`.

## Doc And Fix Sequence

- livespec repository PR #833: created the paste-able idempotent
  installer prompt and minimal `docs/installation.md` pointer.
- livespec repository PR #836: fixed the Phase 2 skip rule so only
  project-level artifacts answer install choices.
- livespec repository PR #847: fixed help prose routing for `next`.
- livespec repository PR #851: fixed per-harness Driver registration
  guidance.
- livespec repository PR #862: fixed the seed idempotency guard.
- livespec repository PR #864: cleared the heading-coverage release
  blocker.
- livespec repository PR #865: cut v0.6.5/release so installed plugins
  picked up the fixes.
- livespec repository PR #1327: refreshed this thread handoff for the
  remaining residual.
- livespec repository PR #1334: fixed the silent exit-3 stderr residual
  by emitting `LivespecError` diagnostics through the shared command
  supervisor path.

## Read-First Chain

The historical product context remains in
`research/01-defects-and-redesign.md`: the six verified defects with
evidence, the maintainer's prompt-based-installer design directive, the
live-test protocol, what survived from the false start, and the
`.ai/adding-an-adopter.md` codification.

No next action remains for this thread.
