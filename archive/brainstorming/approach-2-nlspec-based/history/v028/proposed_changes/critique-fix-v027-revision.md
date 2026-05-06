# critique-fix v027 → v028 revision

## Origin

Phase 3 sub-step 12 implementation work surfaced a literal-text
error in PROPOSAL.md §"Template resolution contract". Line 1466
specifies that the resolve_template wrapper computes its
`<bundle-root>` via:

```
Path(__file__).resolve().parent.parent
```

and then emits `<bundle-root>/specification-templates/<name>/` as
stdout for built-in template resolution.

The repo's actual layout (per PROPOSAL.md's own directory tree at
lines 88 + 172, and confirmed against the on-disk state via
`ls .claude-plugin/`) places `specification-templates/` as a
SIBLING of `scripts/`:

```
.claude-plugin/
├── plugin.json
├── marketplace.json
├── scripts/
│   ├── bin/
│   ├── _vendor/
│   └── livespec/
├── skills/
└── specification-templates/
    ├── livespec/
    └── minimal/
```

Tracing `Path(__file__).resolve().parent.parent` from where the
shebang wrapper at `bin/resolve_template.py` would compute it:

- `__file__` = `.claude-plugin/scripts/bin/resolve_template.py`
- `.parent` = `.claude-plugin/scripts/bin/`
- `.parent.parent` = `.claude-plugin/scripts/`

Following the formula yields
`.claude-plugin/scripts/specification-templates/<name>/`, which
does not exist. The actual `<bundle-root>` (the `.claude-plugin/`
directory) requires one more `.parent` level: from `bin/X.py`,
`.parent.parent.parent`; from
`livespec/commands/resolve_template.py` (where the `main()`
implementation actually lives — the shebang wrapper is the
spec-mandated 6-statement shape with no logic), `.parents[3]`.

This blocks Phase 3 sub-step 12. Every consumer of
resolve_template's stdout — `seed/SKILL.md` prose for
`prompts/seed.md` lookup; `doctor` for the `template-exists`
check's directory-existence verification; per-sub-command SKILL.md
prose for the `Read(<resolved-path>/prompts/<cmd>.md)` step —
would receive a non-existent path and fail.

This is Case A (PROPOSAL.md drift) auto-blocking per the bootstrap
skill rule, requiring a v028 PROPOSAL.md snapshot.

## Decisions captured in v028

### D1 — Correct the bundle-root derivation formula at PROPOSAL.md line 1466

**Decision.** Replace the off-by-one formula with a verbal
description anchored to the actual `.claude-plugin/` directory,
plus a concrete `pathlib` formula that matches the file location
where the path computation actually happens (the `main()`
implementation at
`.claude-plugin/scripts/livespec/commands/resolve_template.py`,
NOT the 6-statement shebang wrapper at
`.claude-plugin/scripts/bin/resolve_template.py`, which has no
room for path-derivation logic per the wrapper-shape contract).

**Old text (PROPOSAL.md line 1466):**

> where `<bundle-root>` is derived via
> `Path(__file__).resolve().parent.parent` on the wrapper itself.

**New text:**

> where `<bundle-root>` is the `.claude-plugin/` directory of the
> installed plugin (the parent of the `scripts/` subtree that
> houses both `bin/` shebang wrappers and the `livespec/` Python
> package). The path is derived inside
> `livespec/commands/resolve_template.py` (where the `main()`
> implementation lives — the 6-statement shebang wrapper at
> `bin/resolve_template.py` has no room for path-computation
> logic per the wrapper-shape contract) via
> `Path(__file__).resolve().parents[3]`: from
> `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
> `parents[0]` is `commands/`, `parents[1]` is `livespec/`,
> `parents[2]` is `scripts/`, `parents[3]` is `.claude-plugin/`.

**Rationale.** The original formula `Path(__file__).resolve().
parent.parent` is correct for `.claude-plugin/scripts/` — the
`bundle_scripts` value computed inside `bin/_bootstrap.py` for
sys.path setup, where `__file__` is the bin/ wrapper itself and
two `.parent` levels reach `scripts/`. The drift originates from
the v1 specification reusing the same formula shape for a
different target (`<bundle-root>` = `.claude-plugin/`, NOT
`<bundle-root>` = `.claude-plugin/scripts/`) and a different
file-location anchor (the `commands/` implementation, NOT the
`bin/` wrapper). The corrected formula uses `.parents[3]` from
the `commands/` implementation file — anchored to where the path
computation actually happens, with each parent level explicitly
named in the prose so future readers can verify the
correspondence to the directory tree at PROPOSAL lines 88 + 172
without needing to count parents themselves.

**Source-doc impact list.**

- PROPOSAL.md line 1466 — single Edit replacing the old formula
  text with the new prose + formula.
- PROPOSAL.md directory tree at lines 88-172 — verified consistent
  with the new formula (no edits needed; the tree was always
  correct, only the formula derived from it was wrong).
- No companion-doc impact: the style doc, NOTICES.md,
  `.vendor.jsonc`, and pyproject.toml carry no reference to the
  bundle-root-derivation formula.
- No deferred-items impact:
  `user-hosted-custom-templates`'s v2+ extensibility-shield clause
  (PROPOSAL lines 1485-1493) freezes the stdout contract and the
  CLI flag shape but explicitly does NOT freeze the
  bundle-root-derivation mechanism — implementations are free to
  use whatever Python expression yields the correct
  `.claude-plugin/` directory. The corrected formula remains
  internal-implementation guidance; the user-facing contract
  (stdout shape + flags) is unchanged.

## Plan-level decisions paired with v028

The plan is unversioned per the v022 rule-refactor decision; plan
edits do not enter v028's overlay record but ride in the same
commit as the v028 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v028; add decision summary for v028
  (D1: bundle-root formula correction at PROPOSAL.md line 1466).
- **Phase 0 step 1 byte-identity check** — bump from v027 to v028.
- **Phase 0 step 2 frozen-status header literal** — bump from
  "Frozen at v027" to "Frozen at v028".
- **Execution prompt block** — bump the "Treat PROPOSAL.md vNNN as
  authoritative" line from v027 to v028.

No other plan-text edits required: Phase 3 sub-step 12 (the
sub-step that surfaced this drift) is described in the plan via
free prose ("`livespec/commands/resolve_template.py` — full
implementation per PROPOSAL.md §'Template resolution contract'")
that defers to PROPOSAL for the concrete formula; the corrected
PROPOSAL text flows directly into the implementation without any
plan-level guidance change.

## Companion-doc + repo-state changes paired with v028

None. The v028 fix is an internal-implementation correction to
PROPOSAL.md only. No companion docs reference the bundle-root
formula; no repo-state files (already-authored Phase 1 / Phase 2
artifacts) carry the formula either.

## Why no formal critique-and-revise

This is a single substantive architectural fix (D1 — the
bundle-root formula correction). One literal-text error, one
correction, one impact-list entry. No option-picker discussion
remains for the revision file to walk through; the user reviewed
the diagnosis and selected the halt-and-revise path explicitly.
Direct overlay matches the v022/v023/v024/v025/v026/v027
precedent for narrow single-architectural-decision fixes.
