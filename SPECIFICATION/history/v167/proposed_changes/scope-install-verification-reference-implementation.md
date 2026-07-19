---
topic: scope-install-verification-reference-implementation
author: claude-opus-4-8
created_at: 2026-07-19T06:42:28Z
spec_commitments:
  impl_followups:
    - id_hint: ensure-plugins-projectpath-verification
      description: |
        Add `projectPath` record verification plus its covering unit test to `livespec_dev_tooling/fleet/ensure_plugins.py`, so the tool conforms to the install-verification invariant it is cited against. Filed as livespec-zxf6, owned by the livespec-dev-tooling sibling per §"Sibling spec ownership".
---

## Proposal: Scope the install-verification reference implementation to the flow it actually implements

### Target specification files

- SPECIFICATION/contracts.md

### Summary

history/v166 cites `livespec_dev_tooling/fleet/ensure_plugins.py` as the unqualified reference implementation of the install-verification invariant, but that tool performs no record verification and infers success from exit status — the exact inference the invariant forbids. Scope the citation to the derive-and-install flow, state the nonconformance explicitly, and bind remediation to the sibling-owned follow-up.

### Motivation

Correcting a defect introduced by this contract's own previous revision
(history/v166, proposal `adopter-install-requires-explicit-plugin-install`).

The independent Fable review of that proposal returned one blocker, which was
fixed before ratification. A second, more serious blocker was reported after
the pass had already been driven, and is therefore corrected here rather than
in v166.

v166's install-verification paragraph states that enabled-without-installed and
installed-against-a-different-`projectPath` are defective states which
provisioning tooling MUST detect and report loudly, and that "neither may be
inferred from a command's exit status". It then cites
`livespec_dev_tooling/fleet/ensure_plugins.py` as the "Reference
implementation" — without qualification.

That tool does not implement the invariant. Verified against the installed copy
at `.venv/lib/python3.10/site-packages/livespec_dev_tooling/fleet/ensure_plugins.py`:
zero occurrences of `projectPath`, zero occurrences of `installed_plugins`, and
`run_from_settings` returns based solely on each subprocess's `returncode`.

So v166 as ratified tells a reader that a nonconforming tool is the reference
for conformance. The defect is compounded by v166's own finding that a
`-s project` update can act on another project's record and exit 0: under that
behavior `ensure_plugins.py` reports success having provisioned nothing for the
invoking project — the precise failure the invariant exists to prevent.

### Proposed Changes

One replacement in `SPECIFICATION/contracts.md` §"Plugin distribution", in the
install-verification paragraph added at history/v166. The REPLACE-TARGET exists
verbatim and uniquely in the live file.

REPLACE-TARGET:

    Reference implementation: `livespec_dev_tooling/fleet/ensure_plugins.py`, which derives the marketplace and plugin set from the committed `.claude/settings.json` and issues `claude plugin install ... -s project` followed by `claude plugin update ... -s project` for each.

REPLACEMENT:

    Reference implementation of the derive-and-install flow ONLY: `livespec_dev_tooling/fleet/ensure_plugins.py`, which derives the marketplace and plugin set from the committed `.claude/settings.json` and issues `claude plugin install ... -s project` followed by `claude plugin update ... -s project` for each. That tool does NOT yet satisfy this invariant: it determines success from each command's exit status and reads no install record, which is exactly the inference this paragraph forbids — so a scoped update that acted on another project's record would be reported as success. Adding the `projectPath` verification and its covering test is a committed follow-up owned by the `livespec-dev-tooling` sibling per `non-functional-requirements.md` §"Sibling spec ownership", on the same pattern this contract already applies to the copier-scaffold enforcement check.

The follow-up work is filed as `livespec-zxf6` (add `projectPath` verification
plus its covering unit test to `ensure_plugins.py`, owned by the
`livespec-dev-tooling` sibling). The ownership split follows the precedent
already in this file, where the copier-scaffold contract defers its paired
enforcement check to "a parallel propose-change against that sibling's spec".
