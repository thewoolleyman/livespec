# spec-side-autonomy — handoff

Resume at the post-ratification implementation-follow-up filing boundary. This
is the authoritative state as of 2026-08-04T04:58Z. Increment 2 is ratified and
landed; do not resume its stale candidate/review/revise briefs or recreate its
ratification worktree.

Before any ledger operation, read `AGENTS.md`, `.ai/agent-disciplines.md`, and
`.ai/beads-gaps-workarounds.md`, then use the installed orchestrator skill for
the target tenant. Batch ledger reads under the credential wrapper and never
print secret values.

**Ledger anchor:** livespec epic `livespec-jvdvx4`.

## Landed state

- Increment 1 is complete. Core slices A/B/C/D merged as PRs #1939, #1942,
  #1949, and #1944. Do not redispatch them.
- Increment 2's proposal-only PR #1948 and its hard digest predecessor
  `livespec-jvdvx4.1` are complete. The predecessor repair rebase-merged as PR
  #1974 at `066a29fbb204b4be2e2e3ab56e73053ec52bb646`.
- Increment 2 was ratified with decision `modify` as **v193**. PR #1978
  rebase-merged onto livespec master at
  `98300b9f3bbe6a60650a74a602b6ece137d68279` after the full local 75-target
  gate and every forge check passed.
- The fresh separate read-only Fable review returned literal `NO BLOCKERS` and
  independently reproduced content digest
  `337e49b012f08bb7300e47d2b762ce5ecb8d4273040ae0b9cf6c82757e9e2c17`.
  It verified all four unconditional human floors, the unchanged Increment-3
  drift doctrine, the citation-only repair, and that `external_references` was
  not widened.
- The live proposal queue currently contains only its README. The ratified
  proposal and revision record are under
  `SPECIFICATION/history/v193/proposed_changes/`.
- Primary `/data/projects/livespec` is clean on `master` at the merged SHA.
  The owned Increment-2 ratification worktree/branch and the old owned
  Increment-1 stale worktree/branch are removed; their remote branches are
  absent. Touch no other session's worktrees.

## Next action 1 — file the orchestrator awareness child

Brief 09 explicitly requires a child work-item in repo
`thewoolleyman/livespec-orchestrator-beads-fabro`, parented to cross-repo epic
`livespec-jvdvx4`, now that core Increment 2 is ratified. File it, but **do not
implement or dispatch it**.

Use these prepared inputs:

- description:
  `tmp/overseer/spec-side-autonomy/increment-2-orchestrator-slice-description.md`
- provenance notes:
  `tmp/overseer/spec-side-autonomy/increment-2-orchestrator-slice-notes.md`

Replace the notes' ratification placeholder with core v193, PR #1978, and merge
SHA `98300b9f3bbe6a60650a74a602b6ece137d68279` before filing. Preserve the
description's bounded size and `ai-only` tier. Its required outcome is to retire
the spec-revise human handoff from `needs-attention` exactly when core's exported
`requires_revise_decision_input` is false, consume that predicate rather than
re-derive it, preserve missing/malformed fail-safe advertisement, and preserve
`drive`'s refusal of spec-side action IDs.

Verify no equivalent open item already exists before writing. The brief itself
is explicit filing authority; the factory/build remains unauthorized here.
Record the created item ID in this handoff.

## Next action 2 — resolve the core implementation follow-up capture

The archived v193 proposal carries this explicit implementation follow-up:

- id hint: `spec-governance-revise-decision-mode-core`
- outcome: extend core's spec-governance registry, config/front-matter schemas,
  effective resolver and shared attention predicate, control actions,
  digest-only journal validation, revise prose, and focused tests for the
  Increment-2 modes and hard floors.

The mandatory post-revise `capture-impl-gaps --since-version v192` detector was
invoked, but its touched-file granularity surfaced 203 historical candidates.
The eight newly introduced decision-mode rules were isolated as:

- `gap-e7fkwrtn` — automated revise safety rails
- `gap-vwljaiy6` — durable revision-record audit
- `gap-vahxbmgt` — shared decision-input predicate
- `gap-o6ellwum` — `revise_decision` journal
- `gap-f4w4anj5` — `decision_policy` front matter
- `gap-ij6nkyby` — design-record decision ownership
- `gap-xf5qdoqk` — policy journal/shared-predicate contract
- `gap-ga3g5fah` — effective resolver

No core implementation item was filed and no ledger state was mutated. First
check for an equivalent existing item. Then complete the installed
`capture-impl-gaps` consent/classification flow without treating the other 195
file-scoped candidates as new Increment-2 work. Recommend one coherent core
child matching the proposal's `impl_followups` entry rather than eight
duplicative slices, but obey the skill's explicit ledger-write consent rule.
Do not implement or dispatch during that capture step.

## Increment 3 boundary

Do not start Increment 3 or edit the byte-preserved drift-doctrine sentence.
Increment 3 changes drift acceptance and remains gated on the separately
ratified consensus panel plus a fresh maintainer brief. After the two filings
above, report their IDs and await the next instruction.

## Standing constraints

- All tracked edits use dedicated worktrees; never edit or commit tracked files
  directly in `/data/projects/livespec`.
- Never pass `--no-verify`; use worktree → PR → rebase-merge → primary refresh
  → cleanup and halt on a hook failure.
- Never touch another session's worktree, branch, sandbox, ledger item, or
  admission label. Never kill the acting overseer daemon.
- The detailed historical milestone trail is
  `tmp/overseer/spec-side-autonomy/worker-status.log`.
