# `<intent-derived-title>` — contracts

This file enumerates the wire-level / CLI-level interfaces the
project exposes. Contracts SHOULD be language-neutral (JSON,
CLI argument shapes, exit codes, etc.) so any tool authored
against them works regardless of which language internalizes
them.

## CLI surface

The user-facing CLI surface, if any. Each invocation MUST
document its required and optional flags, its expected
stdout/stderr shape, and its exit-code semantics.

## Exit-code table

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | internal bug (uncaught exception) |
| `2` | usage error (bad CLI invocation) |
| `3` | precondition error (project state not met) |

The 4-and-up range is reserved for project-specific error
conditions; document each new code in this table.

## Wire-format payloads

Any JSON payloads the project produces or consumes. Each
payload MUST be schema-validated at the boundary; the schema
file lives alongside the contract.
