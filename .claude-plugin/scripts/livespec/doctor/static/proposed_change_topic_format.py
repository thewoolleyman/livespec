"""proposed-change-topic-format static check: the topic slug follows the
canonical lowercase-kebab format (style doc §"Proposed-change topic format").

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError(
            "livespec/doctor/static/proposed_change_topic_format: not yet implemented",
        ),
    )
