"""E2E harness selector — dispatches mock vs real per `LIVESPEC_E2E_HARNESS`.

Per SPECIFICATION/contracts.md:

- `LIVESPEC_E2E_HARNESS=mock` (default when unset) `tests/e2e/fake_claude.py`.
- `LIVESPEC_E2E_HARNESS=real` `tests/e2e/real_claude.py` (live
  claude-agent-sdk + Claude Code CLI; requires `ANTHROPIC_API_KEY`).

Tests import this module and call `harness.seed(...)`, `harness.revise(...)`
etc.; the module re-exports the matching tier's surface. The selection
happens at module-import time (i.e., once per pytest process), matching the
one-shot-per-sub-command shape of both tiers.

The `HARNESS_MODE` constant is exposed so tests can branch on tier where
needed (e.g., `test_retry_on_exit_4` already carries `pytest.mark.mock_only`).

Import discipline note: the conditional `import-and-rebind` block below
intentionally rebinds module-level names from EITHER `fake_claude` OR
`real_claude` based on `HARNESS_MODE`. The `as <name>` re-export form
keeps pyright happy with the conditional-import idiom; the `# noqa: F401`
disables ruff's `unused-import` complaints on the alternate-branch shadow.
"""

from __future__ import annotations

import os
from typing import Final, Literal

HarnessMode = Literal["mock", "real"]


def _resolve_mode() -> HarnessMode:
    raw = os.environ.get("LIVESPEC_E2E_HARNESS", "mock").strip().lower()
    if raw == "real":
        return "real"
    if raw in ("", "mock"):
        return "mock"
    raise RuntimeError(
        f"LIVESPEC_E2E_HARNESS must be 'mock' or 'real' (or unset for 'mock'); got: {raw!r}"
    )


HARNESS_MODE: Final[HarnessMode] = _resolve_mode()


# Conditional import: only one of `fake_claude` / `real_claude` is loaded.
# Selecting `real` when claude-agent-sdk is missing fails fast at import
# time, which is the intended loud-failure behavior — the operator should
# not silently fall back to the mock tier when they asked for the real one.
if HARNESS_MODE == "real":
    import real_claude as _impl
else:
    import fake_claude as _impl


critique = _impl.critique
doctor_static = _impl.doctor_static
propose_change = _impl.propose_change
propose_change_invalid = _impl.propose_change_invalid
prune_history = _impl.prune_history
revise = _impl.revise
seed = _impl.seed
seed_required_workflow_files = _impl.seed_required_workflow_files


__all__ = [
    "HARNESS_MODE",
    "HarnessMode",
    "critique",
    "doctor_static",
    "propose_change",
    "propose_change_invalid",
    "prune_history",
    "revise",
    "seed",
    "seed_required_workflow_files",
]
