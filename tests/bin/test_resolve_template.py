"""Per-wrapper coverage test for bin/resolve_template.py."""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_wrapper_threads_zero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("resolve_template.py", "livespec.commands.resolve_template", 0)


def test_wrapper_threads_nonzero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("resolve_template.py", "livespec.commands.resolve_template", 6)
