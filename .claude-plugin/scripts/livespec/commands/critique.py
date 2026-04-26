"""critique sub-command: runs an LLM-driven critique against a proposed change.

Phase 2 stub. Real implementation lands in Phase 3 (minimum-viable
critique) and Phase 7 (full feature parity).
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(PreconditionError("livespec/commands/critique: not yet implemented"))


def main() -> int:
    return PreconditionError.exit_code
