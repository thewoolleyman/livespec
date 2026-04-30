"""Critique sub-command supervisor.

Per PROPOSAL.md §"`critique`" (line ~2280) and Plan Phase 3
(lines 1524-1532): critique is minimum-viable per v019 Q1 —
invokes propose_change internally with the `-critique`
reserve-suffix appended (the simplest delegation shape; full
reserve-suffix algorithm lives at Phase 7). Accepts
`--findings-json <path>` plus the same flags propose_change
takes; routes the delegation with the same target.

Cycle 96 lands the supervisor stub returning 1; subsequent
cycles widen under outside-in pressure.
"""

from __future__ import annotations

import sys

__all__: list[str] = ["main"]


def main(*, argv: list[str] | None = None) -> int:
    """Critique supervisor entry point. Returns the process exit code.

    Cycle 96 stub: returns 1 (generic error sentinel) until
    subsequent cycles drive the propose_change-delegation
    railway. The wrapper invokes `main()` per the canonical
    6-statement shape; argv defaults to sys.argv[1:] when
    called without args.
    """
    _ = sys.argv[1:] if argv is None else argv
    return 1
