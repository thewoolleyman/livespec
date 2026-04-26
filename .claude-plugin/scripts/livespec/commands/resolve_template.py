"""resolve-template helper: echoes the active template's resolved path to stdout.

Phase 2 stub. Real implementation lands when SKILL.md two-step prompt
dispatch wiring is needed (Phase 3+).
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/commands/resolve_template: not yet implemented"),
    )


def main() -> int:
    return PreconditionError.exit_code
