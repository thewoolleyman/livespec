"""proposed-change-topic-format static check.

For each proposed-change file under `<spec_root>/proposed_changes/`
and `<spec_root>/history/v<N>/proposed_changes/`, verifies the
front-matter `topic` field matches the canonical kebab-case format
(`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, length ≤ 64).

Phase 3 minimum-viable: tiny inline front-matter scanner that
extracts the `topic:` line from the YAML block bracketed by
`---` markers. Phase 7 widens to the full
`livespec/parse/front_matter.py` restricted-YAML parser (deferred
per PROPOSAL §"Proposed-change file format" lines 2990-2995).

Skips paired `<stem>-revision.md` files (those have `proposal:` /
`decision:` front-matter, not `topic:`).
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = [
    "SLUG",
    "run",
]


SLUG: CheckId = CheckId("doctor-proposed-change-topic-format")
_VNNN_RE = re.compile(r"^v\d+$")
_TOPIC_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
_TOPIC_MAX_LEN = 64
_TOPIC_LINE_RE = re.compile(r"^topic:\s*(.+)$")


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    spec_root_str = str(ctx.spec_root)
    violations: list[str] = []
    _scan_dir(
        directory=ctx.spec_root / "proposed_changes",
        violations=violations,
        rel_prefix="proposed_changes",
    )
    history_dir = ctx.spec_root / "history"
    if history_dir.is_dir():
        for vdir in sorted(history_dir.iterdir()):
            if _VNNN_RE.match(vdir.name) and vdir.is_dir():
                _scan_dir(
                    directory=vdir / "proposed_changes",
                    violations=violations,
                    rel_prefix=f"history/{vdir.name}/proposed_changes",
                )
    if violations:
        return IOSuccess(
            Finding(
                check_id=SLUG,
                status="fail",
                message=f"non-canonical topics: {'; '.join(violations)}",
                path=None,
                line=None,
                spec_root=spec_root_str,
            ),
        )
    return IOSuccess(
        Finding(
            check_id=SLUG,
            status="pass",
            message="every proposed-change topic field is canonical kebab-case",
            path=None,
            line=None,
            spec_root=spec_root_str,
        ),
    )


def _scan_dir(
    *,
    directory: Path,
    violations: list[str],
    rel_prefix: str,
) -> None:
    """Walk `directory` for proposed-change files; append violations to the list."""
    if not directory.is_dir():
        return
    for entry in sorted(directory.iterdir()):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        if entry.name.endswith("-revision.md"):
            continue
        if entry.name == "README.md":
            continue
        topic = _extract_topic(path=entry)
        if topic is None:
            violations.append(f"{rel_prefix}/{entry.name} (missing topic: line)")
        elif len(topic) > _TOPIC_MAX_LEN:
            violations.append(
                f"{rel_prefix}/{entry.name} (topic exceeds {_TOPIC_MAX_LEN} chars)",
            )
        elif not _TOPIC_RE.match(topic):
            violations.append(
                f"{rel_prefix}/{entry.name} (topic={topic!r} not canonical)",
            )


def _extract_topic(*, path: Path) -> str | None:
    """Tiny front-matter scanner: returns the `topic:` value or None.

    `_scan_dir` filters to `entry.is_file()` before calling here, so any
    OSError reading the file is a bug and propagates to the supervisor's
    bug-catcher (per `check-no-except-outside-io`: no explicit `except`
    outside io/** except the supervisor catch-all).
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        m = _TOPIC_LINE_RE.match(line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None
