# Open issues

Append-only-with-status-mutation log of plan / PROPOSAL drift
discovered during bootstrap execution. The bootstrap skill is the
only writer.

Each entry's heading carries the timestamp, phase, severity, and
disposition. Severity is one of: `blocking`,
`non-blocking-pre-phase-6`, `non-blocking-post-phase-6`. Disposition
(intent) is one of: `halt-and-revise-brainstorming`,
`defer-to-spec-propose-change`, `resolved-in-session`. Status
(lifecycle) is one of: `open`, `resolved`, `superseded`.

Existing entries' bodies are written once; the `Status:` field MAY
be mutated in place, and a `**Resolved:** ...` line MAY be appended
on resolution. Never rewrite or delete entries without explicit
user direction.

Entry format:

```markdown
## <UTC ISO 8601> — phase N — <severity> — <disposition>

**Status:** open

**Description:** <description, 1-3 sentences>
```

On resolution, the skill mutates `Status:` to `resolved` and
appends:

```markdown
**Resolved:** <UTC ISO 8601> — <one-line resolution summary>
```

## 2026-04-25T23:33:20Z — phase 0 — non-blocking-pre-phase-6 — resolved-in-session

**Status:** resolved

**Description:** Plan Phase 0 step 3 directs deleting `tmp/` on the premise that it is empty stale scaffolding from earlier brainstorming passes. User reports `tmp/` is in active use as personal scratch space and must not be deleted. Convention adopted: any future bootstrap-owned scratch goes under `tmp/bootstrap/` (creatable on demand, freely deletable by the bootstrap); `tmp/` root is user-owned and off-limits. `tmp/` is git-untracked, so the Phase 0 exit-criterion commit (only header-note addition + `tmp/` removal) is naturally satisfied since the deletion would be git-invisible.

**Resolved:** 2026-04-25T23:33:20Z — convention established (`tmp/bootstrap/` for bootstrap scratch, `tmp/` root user-owned); sub-step 3 no-op since no bootstrap scratch exists to delete.

**Resolved:** 2026-04-25T23:52:51Z — codified in v023; see `history/v023/proposed_changes/critique-fix-v022-revision.md` (decision D1) and the paired plan-text edits at Phase 0 step 3 + exit criterion.
