# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: version_contiguity.

Per Plan  +: this check asserts that the
`<spec_root>/history/vNNN/` directory numbers form a
contiguous sequence starting from `v001` with no gaps.

Both arms are implemented: the pass arm for a well-formed
contiguous sequence (including an empty history with no `vNNN/`
directories yet — a freshly seeded project), and the fail arm
naming the first missing version when the sequence has a gap or
does not start at `v001`.
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-version-contiguity")

# A `vNNN` history-snapshot directory name: the literal `v` followed by
# one or more digits. The README.md directory-description file and any
# other non-snapshot sibling under `history/` do not match.
_VERSION_DIR_PATTERN = re.compile(r"^v(\d+)$")


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="history/vNNN/ numbers form a contiguous sequence starting at v001",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _gap_finding(*, ctx: DoctorContext, missing: int) -> Finding:
    """Construct a fail-status Finding naming the first missing version.

    The `vNNN` sequence under `<spec_root>/history/` MUST be
    contiguous starting at `v001`. When a number is absent — a
    middle gap (e.g. `v001`, `v003` with no `v002`) or a missing
    `v001` while later snapshots exist — the check fires fail and
    embeds the first missing tag (zero-padded to three digits) in
    the message so the user can locate the gap without re-scanning.
    """
    missing_tag = f"v{missing:03d}"
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"history/vNNN/ numbers are not contiguous: {missing_tag} is "
            f"missing; the sequence MUST start at v001 with no gaps"
        ),
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _select_version_numbers(*, version_paths: list[Path]) -> list[int]:
    """Extract the integer NNN from each `vNNN`-named directory in `version_paths`.

    Mirrors `version_directories_complete._select_version_dirs`: the
    `is_dir()` + `^v(\\d+)$` filter excludes the skill-owned
    `<spec_root>/history/README.md` directory-description file and any
    other non-snapshot sibling, so a valid seeded tree is not
    mis-classified. Returns the parsed numbers sorted ascending.
    """
    numbers: list[int] = []
    for path in version_paths:
        if not path.is_dir():
            continue
        match = _VERSION_DIR_PATTERN.match(path.name)
        if match is None:
            continue
        numbers.append(int(match.group(1)))
    return sorted(numbers)


def _first_missing_version(*, numbers: list[int]) -> int | None:
    """Return the first version absent from a contiguous-from-1 sequence.

    The expected sequence is `1, 2, ... max(numbers)`. Returns the
    first integer in that range not present in `numbers`, or `None`
    when the sequence is contiguous starting at 1. An empty
    `numbers` (a freshly seeded project with no `vNNN/` snapshots
    yet) is contiguous-by-vacuity and yields `None`.
    """
    if not numbers:
        return None
    present = set(numbers)
    for expected in range(1, max(numbers) + 1):
        if expected not in present:
            return expected
    return None


def _evaluate(
    *,
    ctx: DoctorContext,
    version_paths: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Evaluate the directory list for contiguity.

    Filters `version_paths` to `vNNN/` snapshot directories, then
    asserts the numbers form a contiguous sequence starting at
    `v001`. A gap (or a missing `v001` while later snapshots exist)
    yields a fail-Finding naming the first missing version; an
    empty or contiguous sequence yields the pass-Finding.
    """
    numbers = _select_version_numbers(version_paths=version_paths)
    missing = _first_missing_version(numbers=numbers)
    if missing is None:
        return IOSuccess(_pass_finding(ctx=ctx))
    return IOSuccess(_gap_finding(ctx=ctx, missing=missing))


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the version-contiguity check against `ctx`.

    Lists `<ctx.spec_root>/history/` and evaluates the result. On
    a contiguous (or empty) `vNNN/` sequence yields
    IOSuccess(Finding(status='pass')); on a gap or missing-v001
    yields IOSuccess(Finding(status='fail')) naming the first
    missing version.
    """
    history_path = ctx.spec_root / "history"
    return fs.list_dir(path=history_path).bind(
        lambda version_paths: _evaluate(ctx=ctx, version_paths=version_paths),
    )
