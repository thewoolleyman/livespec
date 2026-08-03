# livespec/spec_governance/

Core spec-governance policy support. This package owns the
declarative config-key registry, safe-default parsing, effective
policy resolvers, control-surface edits, and digest-only journal
validation used by the `spec_governance` control CLI.

Keep modules cohesive and free of lifecycle side effects. Policy
edits may touch only `.livespec.jsonc` or one proposed-change
front-matter block; journal writes may touch only
`tmp/livespec-spec-governance-journal.jsonl`.
