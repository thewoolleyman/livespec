"""check_tools — pinned tools installed at pinned versions.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-tools` row), every pinned tool is
installed at the pinned version. The check covers:

- mise-pinned binaries from `.mise.toml`'s `[tools]` table
  (per v024: `uv`, `just`, `lefthook`).
- uv-managed Python deps from `pyproject.toml`
  `[dependency-groups.dev]`. Cycle 167 (minimum-viable)
  implements only the mise-pinned binary subset; subsequent
  cycles widen to the Python-dep subset when fixtures
  surface.

For each binary, the check shells out to `<binary> --version`
and verifies the output contains the pinned version string.
A pin of `*` (any version) is accepted as long as the binary
exists. Missing `.mise.toml` is a failure (the manifest
cannot be empty per v024).

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_MISE_PATH = Path(".mise.toml")
_TOOLS_TABLE_HEADER = re.compile(r"^\[tools\]\s*$")
_TOOL_LINE = re.compile(r'^\s*([\w-]+)\s*=\s*"([^"]+)"\s*$')


def _parse_mise_tools(*, source: str) -> dict[str, str]:
    """Parse `.mise.toml`'s `[tools]` table into a name->version dict."""
    tools: dict[str, str] = {}
    in_tools_section = False
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if line.startswith("["):
            in_tools_section = bool(_TOOLS_TABLE_HEADER.match(line))
            continue
        if not in_tools_section:
            continue
        match = _TOOL_LINE.match(raw)
        if match is not None:
            tools[match.group(1)] = match.group(2)
    return tools


def _verify_tool(*, name: str, expected_version: str) -> str | None:
    """Return None on pass, an error message on fail.

    Tries `<bin> --version` first; if that exits non-zero (e.g.,
    lefthook, which uses subcommand-style `lefthook version`),
    falls back to `<bin> version`. The fallback is required to
    cover all three v024 mise-pinned binaries — `uv`, `just`
    accept `--version`; `lefthook` does not.
    """
    binary_path = shutil.which(name)
    if binary_path is None:
        return f"{name}: not on PATH"
    # S603: argv is fixed (binary path resolved via shutil.which + literal flag).
    completed = subprocess.run(
        [binary_path, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        # Fallback for binaries with subcommand-style version surfaces.
        completed = subprocess.run(
            [binary_path, "version"],
            capture_output=True,
            text=True,
            check=False,
        )
    output = (completed.stdout + completed.stderr).strip()
    if expected_version == "*":
        return None
    if expected_version in output:
        return None
    return f"{name}: pinned {expected_version!r} not found in `--version` output ({output!r})"


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_tools")
    cwd = Path.cwd()
    mise_path = cwd / _MISE_PATH
    if not mise_path.is_file():
        log.error(".mise.toml missing — pinned-tool manifest required")
        return 1
    tools = _parse_mise_tools(source=mise_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for name, expected in tools.items():
        problem = _verify_tool(name=name, expected_version=expected)
        if problem is not None:
            issues.append(problem)
    if issues:
        for issue in issues:
            log.error("pinned tool verification failed", issue=issue)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
