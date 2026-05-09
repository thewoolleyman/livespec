# implementation.just — recipes for the repo-local
# livespec-implementation workflow. Imported as a `mod` from the
# main justfile; invoked as `just implementation::<recipe>`.
#
# Authority: SPECIFICATION/non-functional-requirements.md
# §Contracts §"Implementation justfile namespace".
#
# Architectural rules (NFR §Constraints §"Beads invariants"):
# - bd issue prefix `li-`
# - Dolt is source of truth; .beads/issues.jsonl is the export view
# - noninteractive `bd` only (`bd edit` forbidden)
# - hook chaining: lefthook FIRST, beads SECOND, exit status preserved
#
# Pattern source for setup-beads.sh and bd-doctor.sh: Open Brain's
# scripts/setup-beads.sh and scripts/bd-doctor.sh. The vendored,
# adapted copies live at dev-tooling/implementation/.
#
# Phase ordering note: refresh-gaps, check-gaps, and
# check-gap-tracking invoke Python scripts that may not exist yet at
# the time this file is committed. They are Phase C/E bootstrap work,
# themselves tracked as beads issues once the gap loop is alive.
# Recipes failing with "No such file" before those scripts land is
# the expected, gap-signalling state.

# Install / repair the beads tooling: `bd` binary (via mise),
# embedded Dolt database, hook chaining with lefthook. Idempotent
# and recovers from corrupted / workspace-mismatched embedded state.
setup-beads:
    ./dev-tooling/implementation/setup-beads.sh

# Health-check the beads installation per the embedded-mode invariants
# upstream `bd doctor` does not cover.
beads-doctor:
    ./dev-tooling/implementation/bd-doctor.sh

# Run the gap-discovery skill and regenerate
# `implementation-gaps/current.json`. Read-only with respect to
# `SPECIFICATION/`.
refresh-gaps:
    uv run python3 dev-tooling/implementation/refresh_gaps.py

# Validate `implementation-gaps/current.json` against
# `implementation-gaps/current.schema.json`.
check-gaps:
    uv run python3 dev-tooling/implementation/check_gaps.py

# Enforce the gap-id ↔ beads-label exactly-once invariant
# (NFR §Constraints §"Beads invariants" #2): every current gap id has
# exactly one beads issue across all statuses.
check-gap-tracking:
    uv run python3 dev-tooling/implementation/check_gap_tracking.py
