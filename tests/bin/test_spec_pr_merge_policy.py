"""Per-wrapper coverage test for bin/spec_pr_merge_policy.py."""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = []


def test_spec_pr_merge_policy_wrapper_threads_main_exit_code(
    *,
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    """`bin/spec_pr_merge_policy.py` calls the command supervisor's main()."""
    wrapper_runner("spec_pr_merge_policy.py", "livespec.commands.spec_pr_merge_policy", 0)
