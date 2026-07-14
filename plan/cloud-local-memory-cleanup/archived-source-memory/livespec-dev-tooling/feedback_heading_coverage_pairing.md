---
name: feedback-heading-coverage-pairing
description: Adding a new H2 heading to a SPECIFICATION/*.md in livespec or livespec-dev-tooling REQUIRES a matching entry in tests/heading-coverage.json in the SAME commit.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 48850880-6a8c-4e3b-a8e3-798911468efd
---

`just check-heading-coverage` validates that every `##` heading in
every spec tree has a corresponding entry in
`tests/heading-coverage.json` (with matching `spec_root` and
`spec_file`). Missing entries are a `level: error` finding that
blocks `just check-pre-commit-doc-only` (which is what
`just check-pre-push` runs for spec-only branches).

When a `/livespec:revise` pass introduces a NEW H2 heading (not
just edits to existing sections), the `tests/heading-coverage.json`
update MUST land in the same commit. The wrapper itself does NOT
auto-update this file — the LLM-driven post-step has to remember it.

**Why:** The check exists to enforce that every spec heading is
behaviorally tested (or at least flagged as TODO for forward
deferral). It's a "no orphan headings" gate; the spec tree and the
heading-coverage manifest are paired.

**How to apply:** After any revise pass that adds a new `## ` H2
section, append a new entry to `tests/heading-coverage.json`:

```json
{
  "heading": "## <exact heading text including em-dash and other unicode>",
  "spec_root": "SPECIFICATION",
  "spec_file": "<contracts|spec|constraints>.md",
  "test": "TODO",
  "reason": "<one-paragraph explanation: which work-item or epic added this section, what behavior it codifies, and where the real test will land>"
}
```

For TODOs: the release-gate `check-no-todo-registry` rejects any
`test: "TODO"` value on release-tag CI. So a TODO is acceptable for
mid-cycle work but MUST be replaced with a real test ID before the
next release-please tag cycle. The "real test ID" follow-up usually
lands via a separate work-item once the behavior is exercised.

Where this fired in practice: the v076 revise in livespec added
§"Sibling spec ownership" to contracts.md and required a matching
heading-coverage entry; the omission caught me at `git commit` time
via lefthook.

Em-dashes matter: the heading-coverage JSON entry must use the same
character (— vs --) that appears in the spec file's heading. Copy-
paste from the source rather than retyping.

Related: [[feedback-revise-payload-format]],
[[project-livespec-sibling-family-cross-repo-coordination]]
