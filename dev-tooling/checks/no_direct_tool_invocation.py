"""no_direct_tool_invocation — `lefthook.yml` + CI YAML files only invoke `just <target>`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-direct-tool-invocation` row),
`lefthook.yml` and `.github/workflows/*.yml` may invoke only
`just <target>` commands. Direct calls to `uv run`, `pytest`,
`ruff`, `pyright`, `lint-imports`, etc. are banned — the
justfile is the single source of truth for how dev tools are
invoked.

The check scans each in-scope YAML file's text for any
`run:`-style command lines that invoke a banned dev tool
directly. The banned list covers dev-tooling forms only —
the documented setup form `uv sync` is permitted (each CI
job needs to install Python deps before invoking
`just <target>`). Banned prefixes: `uv run`, `pytest`,
`ruff`, `pyright`, `lint-imports`, `mutmut`, `coverage`,
`python3 dev-tooling/`, `python dev-tooling/`. Lines
starting with `just ` are accepted.

Implementation: a simple line scan that splits each line into
tokens and checks whether the first non-whitespace word in
shell-line position is a banned tool. Lines starting with `#`
(comments) and empty lines are skipped.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_LEFTHOOK_PATH = Path("lefthook.yml")
_WORKFLOWS_DIR = Path(".github") / "workflows"
_BANNED_TOOL_PREFIXES = (
    "uv run",
    "pytest",
    "ruff",
    "pyright",
    "lint-imports",
    "mutmut",
    "coverage",
    "python3 dev-tooling/",
    "python dev-tooling/",
)
_RUN_LINE_PATTERN = re.compile(r"^\s*-?\s*run:\s*(.+)$")


def _line_runs_banned_tool(*, command: str) -> bool:
    stripped = command.strip().lstrip("|").lstrip(">").strip().strip("'\"")
    if stripped.startswith("just "):
        return False
    return any(stripped.startswith(prefix) for prefix in _BANNED_TOOL_PREFIXES)


def _find_offenders(*, source: str) -> list[int]:
    out: list[int] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _RUN_LINE_PATTERN.match(line)
        if match is not None and _line_runs_banned_tool(command=match.group(1)):
            out.append(lineno)
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
    log = structlog.get_logger("no_direct_tool_invocation")
    cwd = Path.cwd()
    in_scope: list[Path] = []
    if (cwd / _LEFTHOOK_PATH).is_file():
        in_scope.append(cwd / _LEFTHOOK_PATH)
    workflows_dir = cwd / _WORKFLOWS_DIR
    if workflows_dir.is_dir():
        in_scope.extend(sorted(workflows_dir.glob("*.yml")))
        in_scope.extend(sorted(workflows_dir.glob("*.yaml")))
    offenders: list[tuple[Path, int]] = []
    for path in in_scope:
        source = path.read_text(encoding="utf-8")
        for lineno in _find_offenders(source=source):
            offenders.append((path.relative_to(cwd), lineno))
    if offenders:
        for path, lineno in offenders:
            log.error(
                "direct tool invocation in lefthook/CI YAML banned (use `just <target>`)",
                file=str(path),
                line=lineno,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
