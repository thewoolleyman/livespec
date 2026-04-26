"""revise sub-command: applies accepted proposed changes to a new version snapshot.

Phase 2 stub. Real implementation lands in Phase 3 (minimum-viable
revise) and Phase 7 (full feature parity).
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(PreconditionError("livespec/commands/revise: not yet implemented"))


def main() -> int:
    return PreconditionError.exit_code
