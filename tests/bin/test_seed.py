"""Per-wrapper coverage test for bin/seed.py.

Asserts the shebang wrapper threads its stubbed main()'s return
value into `raise SystemExit(<code>)`, per the canonical
6-statement wrapper shape (style doc §"Wrapper shape" /
PROPOSAL.md §"`seed`").

`wrapper_runner` (in conftest.py) stubs `_bootstrap.bootstrap`
and `livespec.commands.seed.main` so we exercise only the
wrapper plumbing — the real seed command lives one layer
deeper and is driven by its own tests.
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_seed_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/seed.py` calls livespec.commands.seed.main() and forwards its exit code."""
    wrapper_runner("seed.py", "livespec.commands.seed", 0)
