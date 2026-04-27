"""Per-wrapper coverage test for bin/doctor_static.py.

The doctor static-phase wrapper imports
`livespec.doctor.run_static.main` (not
`livespec.commands.<cmd>.main`) — the only wrapper that does so.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_wrapper_threads_zero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("doctor_static.py", "livespec.doctor.run_static", 0)


def test_wrapper_threads_nonzero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("doctor_static.py", "livespec.doctor.run_static", 9)
