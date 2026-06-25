"""Tests for livespec.doctor.static.version_contiguity.

This check asserts that the `<spec_root>/history/vNNN/`
directory numbers are contiguous starting from `v001` with no
gaps (e.g., v001, v002, v003 is valid; v001, v003 is a gap).

Both arms are covered: the pass arm for a contiguous (or empty)
v001..vN sequence, and the fail arm naming the first missing
version when the sequence has a gap or does not start at v001.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import version_contiguity
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_history(*, tmp_path: Path, entries: tuple[str, ...]) -> DoctorContext:
    """Seed a project root whose spec_root carries the named history entries.

    Each entry without a dot is created as a directory; an entry
    containing a dot (e.g. ``README.md``) is created as a file.
    Returns the DoctorContext the check runs against.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    history_path = spec_root / "history"
    history_path.mkdir()
    for entry in entries:
        target = history_path / entry
        if "." in entry:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir()
    return DoctorContext(project_root=project_root, spec_root=spec_root)


def test_version_contiguity_run_returns_pass_for_contiguous_versions(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for v001..v003 contiguous.

    Seeds a project root with a populated spec_root containing
    `history/v001/`, `history/v002/`, `history/v003/` (a
    contiguous sequence). Asserts the check yields a
    pass-status Finding.
    """
    ctx = _seed_history(tmp_path=tmp_path, entries=("v001", "v002", "v003"))
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)


def test_version_contiguity_run_returns_pass_for_empty_history(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for a history/ with no vNNN/ dirs.

    A freshly seeded project whose `history/` directory exists but
    holds no `vNNN/` snapshots yet is contiguous-by-vacuity and
    MUST pass (so doctor stays green on a brand-new tree).
    """
    ctx = _seed_history(tmp_path=tmp_path, entries=())
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)


def test_version_contiguity_run_ignores_non_version_entries(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) ignores a README.md file and a non-`vNNN` sibling directory.

    The `is_dir()` + `^v(\\d+)$` filter excludes the skill-owned
    `history/README.md` file (not a directory) and a non-snapshot
    `notes/` directory (a directory whose name does not match), so a
    valid `v001`, `v002` tree alongside them still yields a
    pass-Finding rather than being mis-classified.
    """
    ctx = _seed_history(
        tmp_path=tmp_path,
        entries=("README.md", "notes", "v001", "v002"),
    )
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)


def test_version_contiguity_run_returns_fail_for_middle_gap(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) naming v002 for a v001/v003 gap.

    Seeds `history/v001/` and `history/v003/` with no `v002/`. The
    check fires fail naming the first missing version (`v002`).
    """
    ctx = _seed_history(tmp_path=tmp_path, entries=("v001", "v003"))
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="fail",
        message=(
            "history/vNNN/ numbers are not contiguous: v002 is missing; "
            "the sequence MUST start at v001 with no gaps"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)


def test_version_contiguity_run_returns_fail_for_missing_v001(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) naming v001 when v001 is absent.

    Seeds `history/v002/` and `history/v003/` with no `v001/`. The
    sequence MUST start at v001, so the check fires fail naming the
    first missing version (`v001`).
    """
    ctx = _seed_history(tmp_path=tmp_path, entries=("v002", "v003"))
    expected = Finding(
        check_id="doctor-version-contiguity",
        status="fail",
        message=(
            "history/vNNN/ numbers are not contiguous: v001 is missing; "
            "the sequence MUST start at v001 with no gaps"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )
    assert version_contiguity.run(ctx=ctx) == IOSuccess(expected)
