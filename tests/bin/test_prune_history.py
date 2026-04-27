"""Per-wrapper coverage test for bin/prune_history.py."""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_wrapper_threads_zero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("prune_history.py", "livespec.commands.prune_history", 0)


def test_wrapper_threads_nonzero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("prune_history.py", "livespec.commands.prune_history", 8)
