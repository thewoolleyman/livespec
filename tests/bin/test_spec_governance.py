"""Per-wrapper coverage test for bin/spec_governance.py."""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_spec_governance_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/spec_governance.py` calls livespec.commands.spec_governance.main()."""
    wrapper_runner("spec_governance.py", "livespec.commands.spec_governance", 0)
