"""Private pure helpers for `out_of_band_edits`."""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = [
    "_is_empty_dir",
    "_make_finding",
    "_parse_version_number",
    "_strip_release_please_anchor_lines",
]


_SLUG: CheckId = CheckId("doctor-out-of-band-edits")
_VERSION_DIR_PREFIX: str = "v"
# release-please tags every mechanically-bumped version line in a spec file
# with a trailing `# x-release-please-version` (TOML) or
# `// x-release-please-version` (JSONC) sentinel. Matching the bare marker
# substring (no comment prefix) covers both comment dialects in one rule.
_RELEASE_PLEASE_ANCHOR_MARKER: bytes = b"x-release-please-version"


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
        spec_root=SpecRoot(str(ctx.spec_root)),
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


def _strip_release_please_anchor_lines(*, content: bytes) -> bytes:
    """Drop every line carrying the `x-release-please-version` marker.

    release-please mechanically rewrites the version token on any
    spec-file line tagged with a trailing `# x-release-please-version`
    (TOML) or `// x-release-please-version` (JSONC) sentinel on each
    release. Those bumps land on HEAD-active `contracts.md` without a
    paired revise snapshot, so the active tree diverges from the
    latest `history/vNNN/` snapshot in those marker lines ALONE.
    Stripping every marker-bearing line from BOTH sides before the
    byte comparison makes a version-anchor-only bump compare equal
    (no drift), while every other spec edit still diverges and is
    still flagged.

    Operates on raw bytes (no UTF-8 round-trip) so no content is lost
    for surviving lines; `splitlines(keepends=True)` preserves the
    exact line terminators of the lines that remain.
    """
    kept = [
        line
        for line in content.splitlines(keepends=True)
        if _RELEASE_PLEASE_ANCHOR_MARKER not in line
    ]
    return b"".join(kept)
