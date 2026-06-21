# implementation.just — recipes for the repo-local
# livespec-implementation workflow. Imported as a `mod` from the
# main justfile; invoked as `just implementation::<recipe>`.
#
# Authority: SPECIFICATION/non-functional-requirements.md
# §Contracts §"Implementation justfile namespace".
#
# Phase D.10 cutover note (2026-05-19): beads-specific recipes
# (setup-beads, beads-doctor, check-gap-tracking) and their backing
# scripts (setup-beads.sh, bd-doctor.sh, _plan_bd.py,
# check_gap_tracking.py, implement.py, plan.py) were retired when
# livespec-core's tracking moved to livespec-orchestrator-git-jsonl. The
# gap-tracking invariant is now a livespec-orchestrator-git-jsonl concern
# (rewriteable via that plugin's list-work-items query); the
# beads-coupled implementation gap-discovery scripts were superseded
# by livespec-orchestrator-git-jsonl's capture-impl-gaps + implement
# heavyweight skills. refresh-gaps and check-gaps remain because they
# operate on implementation-gaps/current.json which is backend-agnostic.

# Run the gap-discovery skill and regenerate
# `implementation-gaps/current.json`. Read-only with respect to
# `SPECIFICATION/`.
refresh-gaps:
    uv run python3 dev-tooling/implementation/refresh_gaps.py

# Validate `implementation-gaps/current.json` against
# `implementation-gaps/current.schema.json`.
check-gaps:
    uv run python3 dev-tooling/implementation/check_gaps.py
