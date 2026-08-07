# pyright: reportUnknownMemberType=none
"""Per-field ratification-evidence error builders, extracted from `_revise_ratification`.

Each `_*_error` here answers one question about a single ratification
evidence block and returns either an operator-facing message or `None`.
They share a uniform keyword signature so `_validate_evidence` can run
them as a sequence rather than as a chain of bespoke branches.

`_proposal_bytes_result` and its `_read_proposal_bytes` reader live here
too, because the proposal bytes exist only to be validated against — the
digest comparison that consumes them is the one error builder that stays
behind, since it needs the canonical-digest helper that is
`_revise_ratification`'s own public surface. Keeping it there is what
keeps this module a leaf: it imports nothing from its parent, so there is
no import cycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from returns.io import impure_safe
from returns.result import Failure, Result, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = [
    "_declaration_error",
    "_proposal_bytes_result",
    "_proposal_stem_error",
    "_reviewer_error",
    "_verdict_error",
]


@impure_safe(exceptions=(OSError,))
def _read_proposal_bytes(*, path: Path) -> bytes:
    """Read proposal bytes without text decoding or newline normalization."""
    return path.read_bytes()


def _reviewer_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = decision
    if evidence.get("reviewer_model") != reviewer_model and reviewer_model is not None:
        return "revise: ratification reviewer_model does not match configured reviewer"
    if evidence.get("reviewer_identity") != evidence.get("reviewer_model"):
        return "revise: ratification reviewer identity/model mismatch"
    return None


def _declaration_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = (decision, reviewer_model)
    if evidence.get("separate_reviewer") is not True:
        return "revise: ratification evidence must declare a separate reviewer"
    if evidence.get("read_only") is not True:
        return "revise: ratification evidence must declare read-only review"
    return None


def _verdict_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = (decision, reviewer_model)
    if evidence.get("verdict") != "NO BLOCKERS":
        return "revise: ratification verdict must be literal NO BLOCKERS"
    return None


def _proposal_stem_error(
    *,
    decision: dict[str, object],
    evidence: dict[Any, Any],
    reviewer_model: str | None,
) -> str | None:
    _ = reviewer_model
    if evidence.get("proposal_stem") != decision.get("proposal_topic"):
        return "revise: ratification proposal stem does not match decision topic"
    return None


def _proposal_bytes_result(
    *,
    evidence: dict[Any, Any],
    spec_target: Path,
) -> Result[bytes, tuple[Path, OSError]]:
    proposal_stem = cast(str, evidence["proposal_stem"])
    proposal_path = spec_target / "proposed_changes" / f"{proposal_stem}.md"
    proposal_result = cast(
        Result[bytes, OSError],
        unsafe_perform_io(
            _read_proposal_bytes(path=proposal_path),  # pyright: ignore[reportArgumentType]
        ),
    )
    if isinstance(proposal_result, Failure):
        return Failure((proposal_path, proposal_result.failure()))
    return Success(proposal_result.unwrap())
