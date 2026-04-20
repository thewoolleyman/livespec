# history

Versioned snapshots of the (pre-seed) `PROPOSAL.md` plus every proposed
change and acknowledgement that produced each version. This directory
is backfilled by hand to mirror what `livespec`'s own `history/`
mechanism would have produced if it had existed at the time these
revisions were made.

## Filename convention

- `vNNN/vNNN-PROPOSAL.md` — frozen copy of the working proposal at
  version `NNN`.
- `vNNN/vNNN-proposed-change-<topic>.md` — a proposed change
  processed by the revise that cut version `NNN`.
- `vNNN/vNNN-proposed-change-<topic>-acknowledgement.md` — the
  paired acknowledgement (decision, rationale, modifications).

## Versions

- **v001** — initial proposal (commit `abba068`), seeded by hand
  before `livespec` existed. No proposed-change files; the `seed`
  step itself is not represented as a proposal under the model.
- **v002** — revise driven by `v002-proposed-change-proposal-
  critique-v01.md` and its acknowledgement, plus several follow-on
  in-conversation corrections that were absorbed into v002 rather
  than filed as separate proposals (gherkin-format change, holdout
  removal, doctor-warning removal, progressive-disclosure removal,
  filename rename `livespec-nlspec-guidelines.md` →
  `livespec-nlspec-spec.md`, etc.). Future revisions, once the
  livespec skill exists, SHOULD file these as discrete proposals
  rather than batching them informally.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is byte-
identical to `history/v002/v002-PROPOSAL.md` until the next revise.
