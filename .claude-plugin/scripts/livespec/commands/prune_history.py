"""prune-history sub-command: irreversibly drops historical version snapshots.

Phase 2 stub. Destructive; the SKILL.md frontmatter sets
`disable-model-invocation: true` so user invocation is required. Real
implementation lands in Phase 7+.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["main", "run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/commands/prune_history: not yet implemented"),
    )


def main() -> int:
    return PreconditionError.exit_code
