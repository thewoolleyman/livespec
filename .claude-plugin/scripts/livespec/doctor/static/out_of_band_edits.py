"""out-of-band-edits static check: working-tree spec edits not landed via
the revise sub-command. Includes a narrow auto-backfill path that may
write to `<spec-root>/proposed_changes/` and `<spec-root>/history/`
per PROPOSAL.md §"Static-phase checks".

Phase 2 stub.
"""
from typing import Any

from returns.io import IOFailure, IOResult

from livespec.errors import PreconditionError

__all__: list[str] = ["run"]


def run() -> IOResult[Any, PreconditionError]:
    return IOFailure(
        PreconditionError("livespec/doctor/static/out_of_band_edits: not yet implemented"),
    )
