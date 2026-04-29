"""red_output_in_commit — every redo feature/bugfix commit has `## Red output`.

Per Plan lines 1708-1712 (v032 D4):

    walks `git log --grep` against the v032-redo commit range
    and rejects any feature/bugfix commit lacking a `## Red
    output` fenced block in its body; activates as a hard
    `just check` gate at Phase 5 exit, **informational
    pre-Phase-5-exit**.

Phase 4 = pre-Phase-5-exit, so the check operates in
**informational mode**: it logs warnings for non-conforming
commits but always exits 0. The Phase-5-exit transition (one-
line edit to flip the exit code) lands when the per-commit
gate is wired into lefthook + CI.

The redo commit range is identified by subject prefix:
`phase-5: cycle <N> — ...`. STATUS / scaffolding commits
(`phase-5: STATUS — ...`, `phase-5: tests/livespec — ...`,
etc.) do not match and are out of scope.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_REDO_SUBJECT_PATTERN = re.compile(r"^phase-5: cycle \d+ ")
_RED_OUTPUT_HEADING = "## Red output"
_GIT_LOG_FORMAT = "%H%x00%B%x00END_OF_COMMIT%x00"


def _collect_redo_commits(*, cwd: Path) -> list[tuple[str, str]]:
    # S603/S607: argv is a fixed list of literal git args; no untrusted input.
    result = subprocess.run(  # noqa: S603, S607
        ["git", "log", f"--format={_GIT_LOG_FORMAT}"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    out: list[tuple[str, str]] = []
    raw = result.stdout
    chunks = raw.split("\x00END_OF_COMMIT\x00")
    for chunk in chunks:
        body = chunk.strip("\x00\n")
        if not body:
            continue
        sha, _, message = body.partition("\x00")
        sha = sha.strip()
        message = message.strip()
        if not sha or not message:
            continue
        first_line = message.splitlines()[0] if message else ""
        if not _REDO_SUBJECT_PATTERN.match(first_line):
            continue
        out.append((sha, message))
    return out


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("red_output_in_commit")
    cwd = Path.cwd()
    for sha, message in _collect_redo_commits(cwd=cwd):
        if _RED_OUTPUT_HEADING in message:
            continue
        log.warning(
            "redo commit missing `## Red output` block (Phase 4 informational)",
            sha=sha,
            subject=message.splitlines()[0],
        )
    # Phase 4 is informational mode: always rc=0 regardless of warnings.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
