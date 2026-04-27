"""Per-wrapper coverage test for bin/propose_change.py."""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_wrapper_threads_zero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("propose_change.py", "livespec.commands.propose_change", 0)


def test_wrapper_threads_nonzero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("propose_change.py", "livespec.commands.propose_change", 4)
