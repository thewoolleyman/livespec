"""propose-change sub-command: stages an LLM-authored change proposal.

Phase 2 stub. Real implementation lands in Phase 3 (minimum-viable
propose-change) and Phase 7 (full feature parity).
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/commands/propose_change: not yet implemented"),
    )


def main() -> int:
    return PreconditionError.exit_code
