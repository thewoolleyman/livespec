"""Per-wrapper coverage test for bin/seed.py.

Verifies the wrapper threads `livespec.commands.seed.main()`'s
return code into `SystemExit`, with `bootstrap()` stubbed to a
no-op so the test does NOT mutate the real `sys.path`.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_wrapper_threads_zero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("seed.py", "livespec.commands.seed", 0)


def test_wrapper_threads_nonzero_exit(
    *, wrapper_runner: Callable[[str, str, int], None]
) -> None:
    wrapper_runner("seed.py", "livespec.commands.seed", 7)
