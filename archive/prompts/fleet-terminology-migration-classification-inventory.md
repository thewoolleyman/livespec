# Fleet Terminology Migration Classification Inventory

Work-item: livespec-wnkl72
Source epic: livespec-ztepy5

This note records the residual active-scope `family` occurrences left after the
v133 fleet-terminology migration and their final dispositions. `FIX` means the
wording was migrated to fleet terminology. `KEEP` means the occurrence remains
by design and the rationale is recorded here.

| Path | Occurrence | Disposition | Rationale |
|---|---|---|---|
| `.claude/hooks/livespec_footgun_guard.py` | module docstring: "livespec family" | FIX | Domain-fleet wording; migrated to "livespec fleet". |
| `.claude/hooks/livespec_footgun_guard.py` | `_NO_VERIFY_REASON`: "livespec family" | FIX | User-facing guard message refers to the livespec fleet. |
| `.github/scripts/export-ci-telemetry.sh` | `NAMESPACE="livespec-family"` | KEEP | Telemetry-namespace continuity freeze; renaming would break dashboard and query history. Adjacent comment added. |
| `templates/orchestrator-plugin/.github/scripts/export-ci-telemetry.sh` | `NAMESPACE="livespec-family"` | KEEP | Template copy preserves the same telemetry namespace for continuity. Adjacent comment added. |
| `SPECIFICATION/non-functional-requirements.md` | "self-application family" | KEEP | Generic English that survived the v133 revise deliberately; a spec revise for an annotation-only change is not warranted. |
| `dev-tooling/checks/behavior_scenario_link.py` | docstring: "across the family" | FIX | Domain-fleet wording; migrated to "across the fleet". |
| `dev-tooling/reap_stale_worktrees.py` | docstring: "family repos" | FIX | Domain-fleet wording for repo set; migrated to "fleet repos". |
| `dev-tooling/reap_stale_worktrees.py` | docstring: "ANY family repo path" | FIX | Domain-fleet wording for repo set; migrated to "ANY fleet repo path". |
| `dev-tooling/spec_clauses.py` | docstring: "livespec family's behavior-clause detection" | FIX | Domain-fleet wording; migrated to "livespec fleet's behavior-clause detection". |
| `templates/orchestrator-plugin/.claude/hooks/github_auth_guard.py` | comment: "repo-family convention" | FIX | Template comment refers to the fleet convention; migrated to "repo-fleet convention". |
| `templates/orchestrator-plugin/.github/workflows/ci.yml.jinja` | comment: "livespec-family write-only ingest key" | FIX | Comment wording only; migrated to "livespec fleet write-only ingest key". |
| `templates/orchestrator-plugin/.github/workflows/copier-update-drift.yml.jinja` | comment: "the family's blessed re-sync ref" | FIX | Template comment refers to the fleet; migrated to "the fleet's blessed re-sync ref". |
| `tests/dev-tooling/test_spec_clauses.py` | docstring: "shared across the livespec family" | FIX | Test mirrors `dev-tooling/spec_clauses.py`; migrated to "livespec fleet". |
| `tests/livespec/doctor/static/test_wiring_completeness_cross_repo.py` | module docstring: "family-wide bare-flag invariant" | FIX | Test wording refers to fleet-wide invariant; migrated to "fleet-wide". |
| `tests/livespec/doctor/static/test_wiring_completeness_cross_repo.py` | test docstring: "post-v095 family-wide invariant" | FIX | Test wording refers to fleet-wide invariant; migrated to "fleet-wide". |
| `tests/test_template_beads_access_guard.py` | module docstring: `"Family agent-instruction core"` | FIX | Contract terminology is fleet-scoped; migrated to `"Fleet agent-instruction core"`. |
| `tests/test_template_beads_access_guard.py` | test docstring: "non-family", "family", "non-family" | FIX | Tenant classification wording migrated to "non-fleet" and "fleet". |

Two archived `plan/archive/` transcript exact-string hits were also migrated
from `LiveSpec-family` to `LiveSpec fleet` so the active-tree acceptance grep is
not polluted by obsolete archived planning text outside `archive/`.
