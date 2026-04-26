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

## 2026-04-26T01:52:47Z — phase 1 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Developer-time dependencies (livespec repo only)" (lines 534-545) and §3437's directory-shape diagram say developer tooling is "managed via `mise`" with `.mise.toml` pinning the 12 dev tools, but neither PROPOSAL nor the plan specifies the underlying Python toolchain manager. User-established convention 2026-04-26: UV (astral-sh/uv) is the Python toolchain manager; mise's role narrows to pinning non-Python binaries only (`uv` itself, `just`, `lefthook`); UV manages Python via `uv python pin` and all Python packages via `pyproject.toml` `[dependency-groups.dev]` + `uv sync`. PROPOSAL.md and plan must be revised to codify UV explicitly so the executor doesn't reflex-default to pipx or pip. Picking UV-managed-Python with mise-pins-binaries-only architecture (gated via AskUserQuestion 2026-04-26).

**Resolved:** 2026-04-26T04:34:25Z — codified in v024; see `history/v024/proposed_changes/critique-fix-v023-revision.md` (decisions D1-D4) and the paired plan-text edits at Phase 1 first bullet, new `.python-version` bullet, `pyproject.toml` `[project]` + `[dependency-groups.dev]` sub-bullets, Phase 1 exit criterion, Phase 0 byte-identity references, and Preconditions file list.
