"""red_output_in_commit — every redo feature/bugfix commit has `## Red output` (v033 D4 hard gate).

Per the v033 D4 revision file at `brainstorming/approach-2-
nlspec-based/history/v033/proposed_changes/critique-fix-v032-
revision.md`, this check is **promoted from Phase-4-informational
to hard gate at the v033-codification commit**. The original v032
D4 framing positioned the promotion at Phase-5-exit; v033 D5a
moved the lefthook activation forward to v033-codification, which
forced the hard-gate promotion to the same boundary so the
second retroactive redo's first cycle is mechanically gated.

Behavior: walks `git log` for redo-format commits (subjects
matching `phase-5: cycle <N> — ...`) and emits one structlog
ERROR per commit whose body lacks the `## Red output` heading.
Returns 1 when any offender is found, 0 otherwise. Pre-v033-
codification commits are grandfathered (they precede the hard
gate); the lefthook wires this check into pre-commit so the
gate fires only on commits being authored from the v033-
codification boundary forward.

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
    # S603/S607: argv is a fixed list of literal git args; bare `git` is
    # the canonical invocation per system PATH; no untrusted input.
    result = subprocess.run(  # noqa: S603
        ["git", "log", f"--format={_GIT_LOG_FORMAT}"],  # noqa: S607
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
    offenders: list[tuple[str, str]] = []
    for sha, message in _collect_redo_commits(cwd=cwd):
        if _RED_OUTPUT_HEADING in message:
            continue
        subject = message.splitlines()[0]
        log.error(
            "redo commit missing `## Red output` block (v033 hard gate)",
            sha=sha,
            subject=subject,
        )
        offenders.append((sha, subject))
    return 1 if offenders else 0


if __name__ == "__main__":
    raise SystemExit(main())
