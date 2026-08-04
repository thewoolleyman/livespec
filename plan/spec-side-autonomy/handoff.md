# spec-side-autonomy — handoff

Resume at the Increment 2 Slice B boundary. This is the authoritative state as
of 2026-08-04T06:36Z. Increment 2 is ratified, and its control-surface Slice A
is implemented and landed. Do not resume stale candidate/review/revise briefs,
recreate their worktrees, or redo Slice A.

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

## Increment 2 implementation state

- Core control-surface Slice A `livespec-jvdvx4.3` is closed completed. PR
  #1980 rebase-merged as
  `2ffebf1b0744e07a5c385c5be25b475bb1dfbd75` after all 75 local and forge
  gates passed with 100% coverage.
- Slice A added the seventh co-authoritative registry key,
  `revise_decision_mode`, with enum values `manual|delegated|consensus`, safe
  default `manual`, and per-proposal `decision_policy` override support.
- Its global and proposal control actions set or clear only the selected value,
  reject invalid modes and proposal stems, preserve JSONC comments/unrelated
  bytes and Markdown body bytes, and perform no lifecycle, review, git/PR,
  history, or ledger mutation.
- Slice A deliberately did not add the effective resolver, human floors, shared
  attention predicate, `revise_decision` journal validation, or any consensus
  panel. Those belong to the already-filed dependent Slice B
  `livespec-jvdvx4.4`; consensus remains only a valid configured enum value.
- The Slice A feature worktree and local/remote branches are removed. Primary
  and `origin/master` are clean and equal at the merge SHA above.

## Next action — Slice B boundary

Slice B `livespec-jvdvx4.4` is separate work. Do not infer authorization from
Slice A, redispatch Slice A, or begin Increment 3. On restart, inspect the
current ledger state for `livespec-jvdvx4.4` under the configured credential
wrapper and follow the next explicit supervisor brief. Preserve Slice A's
landed control surface and its safe-default behavior while implementing the
resolver/floors/predicate/journal scope only when directed.

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
