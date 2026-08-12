---
topic: spec-governance-flag-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-12T13:45:59Z
---

## Proposal: Record spec-governance's fourth mode --check-default-block

### Target specification files

- SPECIFICATION/contracts.md

### Summary

`contracts.md` enumerates the spec-governance control CLI's modes as a CLOSED list of three — `--show-effective`, `--action`, `--journal-event-json` — in both the §"Wrapper CLI surface" table row and the §"Spec-governance control CLI" prose. The shipped `.claude-plugin/scripts/bin/spec_governance.py` has a FOURTH mutually-exclusive mode, `--check-default-block <path>`, added 2026-08-04 and absent from the specification entirely: the string appears zero times anywhere under `SPECIFICATION/`. This proposal records the fourth mode so the closed enumeration stops being wrong.

### Motivation

Found by auditing the §"Wrapper CLI surface" table row-by-row against each wrapper's actual `--help` output, after the same audit surfaced the `doctor` `--spec-target` drift filed as `doctor-spec-target-drift`. The two are independent findings in the same table and are filed as separate topics so each can be dispositioned on its own. Drift dated by `git log -S`: the mode entered in `e2f2232d` ("feat: guard spec governance default blocks", 2026-08-04), a commit touching the wrapper, a new `spec_governance/default_block.py`, a dev-tooling check and five test files — and no `SPECIFICATION/` file.

### Proposed Changes

The mode is real and load-bearing, not vestigial. `--check-default-block <path>` reads the named file, calls `verify_default_block(text=..., manifest=manifest_rows())`, and either emits a structured `{"check_id": "spec-governance-default-block-ok", ...}` payload on stdout or fails with `UsageError` naming the drift. It is the guard that keeps a commented default block in step with the `ConfigKey` manifest, and `dev-tooling/checks/spec_governance_template.py` was changed in the same commit to use it.

TWO EDITS TO `SPECIFICATION/contracts.md`, both replacing text that exists verbatim in the live file today.

**Edit 1 — the Wrapper CLI surface table row.** Replace this line exactly:

```
| `spec-governance` (control; not a lifecycle sub-command) | one of `--show-effective`, `--action <action>`, `--journal-event-json <path>` | `--project-root <path>` |
```

with:

```
| `spec-governance` (control; not a lifecycle sub-command) | one of `--show-effective`, `--action <action>`, `--journal-event-json <path>`, `--check-default-block <path>` | `--project-root <path>` |
```

**Edit 2 — the control-CLI paragraph.** Replace this sentence:

```
`--project-root <path> --action <action>` performs exactly one allowlisted policy edit, and `--project-root <path> --journal-event-json <path>` validates and appends one policy event.
```

with:

```
`--project-root <path> --action <action>` performs exactly one allowlisted policy edit, `--project-root <path> --journal-event-json <path>` validates and appends one policy event, and `--check-default-block <path>` verifies that the commented default block in the named file still matches the declarative `ConfigKey` registry, emitting a structured `spec-governance-default-block-ok` payload on agreement and failing via `UsageError` naming the drifted keys otherwise. The four modes are mutually exclusive; exactly one MUST be supplied.
```

**Why this direction.** Unlike the sibling `doctor-spec-target-drift` proposal, this one has no serious alternative. The mode is consumed by an enforcement check that ships in the repository's own `just check` aggregate, so deleting it to match the contract would remove live guard coverage rather than tidy an unused surface. Documenting is the only coherent close.

**One thing a ratifier should confirm rather than take on trust.** The replacement sentence asserts the four modes are mutually exclusive and exactly one is required. That is how `argparse` is configured today — the four sit in a single required mutually-exclusive group — but it is stated here as a CONTRACT, which binds future implementations. A ratifier who wants the contract looser should amend that final sentence rather than reject the whole edit.

**Scope note.** This proposal deliberately does NOT touch the two optional `--show-effective` modifiers, `--proposal-stem` and `--pr-effective-policy`. Both are already documented in the same paragraph and are not in drift.
