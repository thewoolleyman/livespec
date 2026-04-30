"""Propose-change sub-command supervisor.

Per PROPOSAL.md §"`propose-change`" (line ~2134) and Plan Phase 3
(lines 1505-1523): the wrapper validates the inbound
`--findings-json <path>` payload, composes a proposed-change
file from the findings, and writes it to
`<spec-target>/proposed_changes/<topic>.md`. Phase-3 scope is
minimum-viable per v019 Q1 — topic canonicalization, reserve-
suffix handling, collision disambiguation, and unified author
precedence are deferred to Phase 7.

Cycle 89 lands the supervisor stub; subsequent cycles drive
the railway stages in order: parse_argv -> read --findings-json
-> jsonc.loads -> validate against proposal_findings.schema.json
-> compose proposed-change file -> write to disk.
"""

from __future__ import annotations

import sys

__all__: list[str] = ["main"]


def main(*, argv: list[str] | None = None) -> int:
    """Propose-change supervisor entry point. Returns the process exit code.

    Cycle 89 stub: returns 1 (generic error sentinel) until the
    next cycle drives parse_argv onto the railway. The wrapper
    invokes `main()` per the canonical 6-statement shape; argv
    defaults to sys.argv[1:] when called without args.
    """
    _ = sys.argv[1:] if argv is None else argv
    return 1
