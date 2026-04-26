"""seed sub-command: bootstraps a fresh livespec specification tree.

Phase 2 stub. The real implementation arrives in Phase 3 (minimum
viable seed against the `livespec` template) and Phase 7 (full feature
parity); see the bootstrap plan for sub-step boundaries.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(PreconditionError("livespec/commands/seed: not yet implemented"))


def main() -> int:
    return PreconditionError.exit_code
