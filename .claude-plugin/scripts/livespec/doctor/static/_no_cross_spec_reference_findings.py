"""Finding constructors for no_cross_spec_reference."""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "_fail_finding", "_pass_finding"]


SLUG: CheckId = CheckId("doctor-no-cross-spec-reference")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=(
            "every section citation resolves same-tree or via the external_references allowlist"
        ),
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
    citation: str,
    suggested_entry: str,
) -> Finding:
    """Construct a fail-status Finding naming the unresolved citation.

    `citation` is the literal offending citation text; `line_number`
    is 1-indexed per editor convention; `suggested_entry` is the
    file-plus-heading string the user would add under an
    `external_references` repo key to allowlist the reference.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} section citation "
            f"'{citation}' does not resolve to a heading in the same "
            f"SPECIFICATION/ tree and is not allowlisted; add "
            f"'{suggested_entry}' under an external_references repo key "
            f"in .livespec.jsonc to allow it"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )
