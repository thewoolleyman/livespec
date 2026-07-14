---
name: feedback-revise-payload-format
description: "How to compose a valid revise-input JSON payload for the `/livespec:revise` wrapper. Non-obvious from the SKILL.md prose alone."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 48850880-6a8c-4e3b-a8e3-798911468efd
---

The `bin/revise.py` wrapper's `--revise-json` payload format has two
non-obvious requirements that aren't fully captured in the SKILL.md
prose:

1. **One decision per FILE, not per `## Proposal:` sub-section.**
   The SKILL.md says "the prompt emits an `accept`, `modify`, or
   `reject` decision per `## Proposal` section," but the
   wrapper's `proposal_topic` field maps to the FILENAME (without
   `.md`) at `<spec-target>/proposed_changes/<topic>.md`. So if
   a single propose-change file carries multiple `## Proposal:`
   sub-sections, they ALL collapse into ONE decision entry whose
   `resulting_files[]` carries the cumulative effect.

   The schema permits multiple `decisions[]` entries, but each must
   correspond to a separate FILE. With multiple sub-sections in one
   file, you cannot independently accept/reject them via the
   wrapper — you get one decision verb for the whole file.

2. **`resulting_files[].path` is RELATIVE to spec-target**, with NO
   spec-target-basename prefix. Use `"spec.md"`, NEVER
   `"SPECIFICATION/spec.md"`. The wrapper explicitly rejects the
   latter with `UsageError` (exit 2) at the `_validate_resulting_files`
   step.

**Why:** Both rules were discovered the hard way when the wrapper
silently exited with code 2 / 3 and no stderr output. The errors are
caught in the IOResult railway and surfaced via structlog at WARNING
level, but the default structlog config doesn't emit them. To debug,
import the railway helpers directly:

```python
PYTHONPATH=<scripts>:<vendor> uv run python -c "
from livespec.commands._revise_validation import _validate_resulting_files
from returns.unsafe import unsafe_perform_io
result = unsafe_perform_io(_validate_resulting_files(...))
# match Success/Failure and print the err
"
```

**How to apply:** When composing a revise payload, structure as:

```json
{
  "author": "claude-opus-4-7",
  "decisions": [{
    "proposal_topic": "<frontmatter topic from propose-change file>",
    "decision": "accept",
    "rationale": "Cumulative rationale across all sub-sections",
    "resulting_files": [
      {"path": "spec.md", "content": "<full new content>"},
      {"path": "contracts.md", "content": "<full new content>"}
    ]
  }]
}
```

If a propose-change file has 3 sub-sections targeting 3 different
files, the single decision's `resulting_files[]` has 3 entries. If
sub-sections need different verdicts (some accept, some reject),
that's not expressible in the current schema — file separate
propose-change files instead.

Related: [[feedback-heading-coverage-pairing]],
[[feedback-livespec-commit-prefixes]]
