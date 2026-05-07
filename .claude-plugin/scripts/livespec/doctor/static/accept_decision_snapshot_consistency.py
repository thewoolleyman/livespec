"""Static-phase doctor check: accept_decision_snapshot_consistency.

Per `SPECIFICATION/spec.md` §"Sub-command lifecycle":

For every `<spec-target>/history/vNNN/<stem>-revision.md` with
YAML front-matter `decision` in `{accept, modify}` and a
non-empty `## Resulting Changes` section, every spec-target-
relative file path listed under that section MUST exist in
both `vNNN/` and `v(NNN-1)/`, AND `vNNN/<file>` MUST NOT be
byte-identical to `v(NNN-1)/<file>`. A byte-identical pair
indicates the `resulting_files[]` write silently failed during
the revise that cut `vNNN`.

The check is exempt for `vNNN` directories that contain a
`PRUNED_HISTORY.json` marker (per the existing pruned-marker
exemption convention).
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult
from returns.result import Failure

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import front_matter
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-accept-decision-snapshot-consistency"

_VERSION_RE = re.compile(r"^v(\d+)$")
_REVISION_SUFFIX = "-revision.md"
_RESULTING_CHANGES_HEADING = "## Resulting Changes"
_NEXT_HEADING_PATTERN = re.compile(r"^## ", re.MULTILINE)
_BULLET_PATTERN = re.compile(r"^- (.+)$", re.MULTILINE)
_NONE_PLACEHOLDER = "(none)"
_VERSION_DIR_PADDING = 3
_MIN_VERSION_NUMBER = 2
_PRUNED_MARKER = "PRUNED_HISTORY.json"
_PROPOSED_CHANGES_DIR = "proposed_changes"
_HISTORY_SUBDIR = "history"


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=(
            "every history/vNNN/ accept|modify revision produces a "
            "non-byte-identical snapshot vs v(NNN-1)/ for each listed file"
        ),
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    version_label: str,
    prior_label: str,
    file_path: str,
    revision_filename: str,
) -> Finding:
    """Construct the fail-status Finding for a byte-identical pair."""
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"history/{version_label}/{file_path} is byte-identical to "
            f"history/{prior_label}/{file_path} but "
            f"history/{version_label}/proposed_changes/{revision_filename} "
            f"claims decision in {{accept, modify}} with that file in "
            f"## Resulting Changes; the resulting_files[] write may have "
            f"silently failed"
        ),
        path=f"{_HISTORY_SUBDIR}/{version_label}/{_PROPOSED_CHANGES_DIR}/{revision_filename}",
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _parse_version_number(*, path: Path) -> int | None:
    """Extract NNN from a `vNNN` directory path, or None on shape mismatch."""
    match = _VERSION_RE.match(path.name)
    if match is None:
        return None
    return int(match.group(1))


def _select_versions(*, children: list[Path]) -> list[tuple[int, Path]]:
    """Filter to vNNN directories with N >= 2 that aren't pruned markers."""
    selected: list[tuple[int, Path]] = []
    for child in children:
        if not child.is_dir():
            continue
        n = _parse_version_number(path=child)
        if n is None or n < _MIN_VERSION_NUMBER:
            continue
        if (child / _PRUNED_MARKER).is_file():
            continue
        selected.append((n, child))
    selected.sort(key=lambda pair: pair[0])
    return selected


def _extract_resulting_files_paths(*, revision_text: str) -> list[str]:
    """Extract bullet-listed paths from the `## Resulting Changes` section.

    Bounded by the next `## ` heading or end-of-text. Skips the
    `(none)` placeholder emitted when the section is empty.
    """
    heading_index = revision_text.find(_RESULTING_CHANGES_HEADING)
    if heading_index == -1:
        return []
    after_heading = revision_text[heading_index + len(_RESULTING_CHANGES_HEADING) :]
    next_heading_match = _NEXT_HEADING_PATTERN.search(after_heading)
    section = (
        after_heading[: next_heading_match.start()]
        if next_heading_match is not None
        else after_heading
    )
    paths: list[str] = []
    for match in _BULLET_PATTERN.finditer(section):
        path_str = match.group(1).strip()
        if path_str and path_str != _NONE_PLACEHOLDER:
            paths.append(path_str)
    return paths


def _list_revision_files(*, version_dir: Path) -> list[Path]:
    """Sort the `*-revision.md` files in `version_dir/proposed_changes/`."""
    proposed_changes = version_dir / _PROPOSED_CHANGES_DIR
    if not proposed_changes.is_dir():
        return []
    return sorted(
        entry
        for entry in proposed_changes.iterdir()
        if entry.is_file() and entry.name.endswith(_REVISION_SUFFIX)
    )


def _check_revision(
    *,
    version_dir: Path,
    prior_dir: Path,
    revision_path: Path,
) -> tuple[str, str] | None:
    """Return `(file_path, revision_filename)` on first byte-identical violation.

    Returns None when the revision is reject, parse fails, no
    listed files match, or every listed file differs from prior.
    """
    text = revision_path.read_text(encoding="utf-8")
    parse_result = front_matter.parse_front_matter(text=text)
    if isinstance(parse_result, Failure):
        return None
    fm = parse_result.unwrap()
    if fm.get("decision") not in ("accept", "modify"):
        return None
    paths = _extract_resulting_files_paths(revision_text=text)
    for path_str in paths:
        current = version_dir / path_str
        prior = prior_dir / path_str
        if not (current.is_file() and prior.is_file()):
            continue
        if current.read_bytes() == prior.read_bytes():
            return (path_str, revision_path.name)
    return None


def _detect_first_violation(
    *,
    ctx: DoctorContext,
    children: list[Path],
) -> Finding:
    """Walk versions and revision files; return first fail Finding, else pass."""
    for n, version_dir in _select_versions(children=children):
        prior_dir = ctx.spec_root / _HISTORY_SUBDIR / f"v{n - 1:0{_VERSION_DIR_PADDING}d}"
        if not prior_dir.is_dir():
            continue
        for revision_path in _list_revision_files(version_dir=version_dir):
            violation = _check_revision(
                version_dir=version_dir,
                prior_dir=prior_dir,
                revision_path=revision_path,
            )
            if violation is not None:
                file_path, revision_filename = violation
                return _fail_finding(
                    ctx=ctx,
                    version_label=version_dir.name,
                    prior_label=prior_dir.name,
                    file_path=file_path,
                    revision_filename=revision_filename,
                )
    return _pass_finding(ctx=ctx)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the accept-decision-snapshot-consistency check against `ctx`.

    Walks `<ctx.spec_root>/history/vNNN/proposed_changes/*-revision.md`
    for every vNNN with N >= 2 (skipping pruned markers); for each
    revision file with decision in {accept, modify}, asserts each
    listed file in `## Resulting Changes` differs byte-for-byte
    between vNNN and v(NNN-1).
    """
    history_path = ctx.spec_root / _HISTORY_SUBDIR
    return fs.list_dir(path=history_path).map(
        lambda children: _detect_first_violation(ctx=ctx, children=children),
    )
