"""Tests for livespec.doctor.run_static.

Per PROPOSAL.md §"`doctor`" (line ~2468) and Plan Phase 3
(lines 1554-1616): run_static is the static-phase orchestrator.
It enumerates `(spec_root, template_name)` pairs, builds a
per-tree DoctorContext, and runs the applicable check subset
per the orchestrator-owned applicability table. Phase-3 minimum
subset registers 8 checks; the rest land at Phase 7.
"""

from __future__ import annotations

from livespec.doctor import run_static

__all__: list[str] = []


def test_run_static_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/doctor/run_static.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Subsequent cycles drive the
    enumeration + per-tree dispatch + per-check execution
    behavior under outside-in pressure.
    """
    exit_code = run_static.main(argv=[])
    assert isinstance(exit_code, int)
