---
topic: finding-schema-warn-status
author: claude-opus-4-7
created_at: 2026-05-24T03:14:20Z
---

## Proposal: add-warn-to-finding-status-enum

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend the Finding `status` enum from `pass | fail | skipped` to `pass | fail | skipped | warn`, so the four warn-class invariants already specified in `contracts.md` (`no-stale-gap-tied`, `no-stale-merged-branch`, `no-stale-merged-pr-branch`, `no-stale-worktree`, plus the optional pinned-tag drift check) are expressible against the wire schema. The schema and dataclass are co-authoritative per the schema-dataclass-pairing convention; both update in lockstep along with the doctor static-phase exit-code mapping rule.

### Motivation

Memo `mm-twt0yw` and work-item `li-f5wmjr` piece 2 surfaced the gap: `contracts.md` already specifies four invariants that fire `warn` (the three impl-side cleanup invariants under §"Impl-side cleanup invariants (cross-boundary)" plus `no-stale-gap-tied` under §"Doctor cross-boundary invariants", plus the optional pinned-tag drift check under §"contract-version-compatibility"), but `finding.schema.json` enumerates only `pass | fail | skipped` — there is no `warn` slot. The mismatch blocks li-f5wmjr piece 2 (and implicitly the three other warn-class invariants). Closing the gap unblocks all four invariants with a single schema extension. Path A in the memo is the smallest-touch resolution; paths B and C either re-classify cleanup invariants away from doctor or drop them entirely, both of which preserve a structural inconsistency between spec text and schema.

### Proposed Changes

Lockstep edits across schema, dataclass, doctor exit-code derivation, and contract codification.

### `.claude-plugin/scripts/livespec/schemas/finding.schema.json`

Add `warn` to the `status` enum and refresh the schema-level + property-level descriptions to spell out the four-value semantics:

```diff
   "$id": "finding.schema.json",
   "title": "finding",
-  "description": "Schema for a single doctor-static check Finding (v014 N2 standalone). Each check produces one Finding per tree; the orchestrator collects them into a doctor_findings payload. status='pass' is success; status='fail' triggers exit 3; status='skipped' is bootstrap-lenience or content-aware skip.",
+  "description": "Schema for a single doctor-static check Finding (v014 N2 standalone). Each check produces one Finding per tree; the orchestrator collects them into a doctor_findings payload. status='pass' is success; status='fail' triggers exit 3; status='skipped' is bootstrap-lenience or content-aware skip; status='warn' is a productivity-grade nudge that DOES NOT lift the exit code (the SKILL.md narration phase surfaces warn findings to the user).",
```

and:

```diff
     "status": {
       "type": "string",
-      "enum": ["pass", "fail", "skipped"],
-      "description": "Outcome. 'pass' = check ran and asserted invariant holds; 'fail' = check ran and detected a violation (triggers exit 3); 'skipped' = bootstrap-lenience (v014 N3) or content-aware skip per the static-check-semantics deferred entry."
+      "enum": ["pass", "fail", "skipped", "warn"],
+      "description": "Outcome. 'pass' = check ran and asserted invariant holds; 'fail' = check ran and detected a violation (triggers exit 3); 'skipped' = bootstrap-lenience (v014 N3) or content-aware skip per the static-check-semantics deferred entry; 'warn' = check ran and detected a productivity-grade housekeeping nudge that the user should address but that does NOT lift the wrapper exit (reserved for cleanup invariants like `no-stale-gap-tied`, `no-stale-merged-branch`, `no-stale-merged-pr-branch`, `no-stale-worktree`, and the optional pinned-tag drift check)."
     },
```

### `.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json`

Mirror the enum change in the wrapper schema and refresh its description for symmetry:

```diff
     "findings": {
       "type": "array",
-      "description": "All findings from the orchestrator pass. Empty array means doctor ran zero checks (an unusual state worth investigating in itself); a non-empty array with all status='pass' means a clean run. Any status='fail' triggers exit 3.",
+      "description": "All findings from the orchestrator pass. Empty array means doctor ran zero checks (an unusual state worth investigating in itself); a non-empty array with all status in {pass, skipped, warn} means a clean run (exit 0). Any status='fail' triggers exit 3. status='warn' findings are surfaced via SKILL.md narration but do NOT lift the exit code.",
```

and:

```diff
           "status": {
             "type": "string",
-            "enum": ["pass", "fail", "skipped"]
+            "enum": ["pass", "fail", "skipped", "warn"]
           },
```

### `.claude-plugin/scripts/livespec/schemas/dataclasses/finding.py`

Update the dataclass docstring to mention the fourth status value, keeping the schema-dataclass-pairing convention satisfied:

```diff
     Mirrors finding.schema.json: `check_id` is the
     `doctor-<slug>` canonical id; `status` is one of
-    `pass` / `fail` / `skipped`; `message` is human-readable;
+    `pass` / `fail` / `skipped` / `warn`; `message` is
+    human-readable;
     `path` and `line` are optional file-locality fields (None
     when the check is tree-level rather than file-level);
     `spec_root` discriminates per-tree origin per v018 Q1.
```

The dataclass `status` field type stays `str` (no `Literal` introduced); the schema is the wire boundary and the runtime check at JSON validation enforces the enum.

### `.claude-plugin/scripts/livespec/doctor/run_static.py`

Update the `_derive_exit_code` docstring to spell out the four-value mapping. The implementation already returns 0 for any non-fail status, so adding `warn` requires no code change — only the docstring is updated for accuracy:

```diff
 def _derive_exit_code(*, findings: list[Finding]) -> int:
     """Derive the supervisor exit code from aggregated finding statuses.
 
     Per:
     no findings or every finding pass => exit 0; at least one
-    fail => exit 3. The skipped status is treated as pass for
-    exit-code derivation.
+    fail => exit 3. Statuses `skipped` and `warn` are both
+    treated as pass for exit-code derivation: `skipped`
+    indicates bootstrap-lenience or content-aware skip; `warn`
+    indicates a productivity-grade housekeeping nudge that the
+    SKILL.md narration phase surfaces to the user but that does
+    NOT block the wrapper exit.
     """
     if any(finding.status == "fail" for finding in findings):
         return 3
     return 0
```

### `SPECIFICATION/contracts.md` §"Per-sub-spec doctor parameterization"

Update line 95's exit-code derivation sentence to codify the four-value contract that the schema now permits. Reword the existing single sentence into a precise mapping:

```diff
-The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code: any `fail` finding lifts the wrapper to exit non-zero.
+The doctor static phase runs once per spec tree. The wrapper's main loop enumerates the main spec plus every `<spec_root>/templates/<name>/` sub-spec, runs the static checks against each, and emits per-tree findings on stdout. The wrapper's overall exit code is the worst per-tree code derived from the four-value Finding `status` enum (`pass`, `fail`, `skipped`, `warn` per `finding.schema.json`): any `fail` finding lifts the wrapper to exit 3; `pass`, `skipped`, and `warn` findings all yield exit 0. The `warn` status is reserved for productivity-grade housekeeping nudges (`no-stale-gap-tied`, the three `Impl-side cleanup invariants`, and the optional pinned-tag drift check under `contract-version-compatibility`); the SKILL.md narration phase surfaces `warn` findings to the user but the Python layer MUST NOT emit ad-hoc stderr text for them (per the existing rule in `spec.md` §"Sub-command lifecycle" that the Python layer never prints warning text outside the structured-findings contract).
```
