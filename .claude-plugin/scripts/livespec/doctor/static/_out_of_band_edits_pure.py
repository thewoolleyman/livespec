"""Private pure helpers for `out_of_band_edits`."""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = [
    "_is_empty_dir",
    "_make_finding",
    "_parse_version_number",
]


_SLUG: str = "doctor-out-of-band-edits"
_VERSION_DIR_PREFIX: str = "v"


def _make_finding(
    *,
    ctx: DoctorContext,
    status: str,
    message: str,
) -> Finding:
    """Construct a Finding shaped for this check.

    Centralizes the per-check Finding-construction so every
    status branch (skipped, pass, fail) shares the same
    check_id + spec_root field formula and only varies on
    status + message.
    """
    return Finding(
        check_id=_SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _parse_version_number(*, version_path: Path) -> int | None:
    """Parse the integer suffix from a `vNNN` directory name; None on non-match."""
    name = version_path.name
    if not name.startswith(_VERSION_DIR_PREFIX):
        return None
    suffix = name[len(_VERSION_DIR_PREFIX) :]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _is_empty_dir(*, dir_path: Path) -> bool:
    """Return True iff `dir_path` is a directory with zero entries."""
    return not any(dir_path.iterdir())
