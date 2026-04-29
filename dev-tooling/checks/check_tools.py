"""check_tools — verify pinned tools are installed at the pinned version.

Per `python-skill-script-style-requirements.md` canonical-target
line 2098 / Plan line 1753 (Phase-4-exit must-pass list):

    Verify every pinned tool is installed at the pinned version
    — both mise-pinned binaries (`uv`, `just`, `lefthook`) and
    uv-managed Python deps from `pyproject.toml`
    `[dependency-groups.dev]` per v024.

Sources of truth:

- `.mise.toml` `[tools]` table — non-Python binaries.
- `pyproject.toml` `[dependency-groups]` `dev` array — Python
  packages installed by `uv sync --all-groups` into the
  project-local `.venv`.

Per-binary verification: `<tool> --version` is invoked via
`subprocess.run`; the output is matched against the pin.
Per-package verification:
`importlib.metadata.version(<pkg>)` reads the installed
distribution metadata; the result is compared against the pin.

Pin equality is exact-string match on the version core (e.g.,
`"1.36.0"` matches `"just 1.36.0 (...)"`). Restore-from-redo
authoring per Phase-4 must-pass list (Plan line 1753); the
script lives outside the 11-cycle Plan-listed redo scope per
Plan lines 1675-1712.
"""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_MISE_PATH = Path(".mise.toml")
_PYPROJECT_PATH = Path("pyproject.toml")
_MISE_PIN_LINE_RE = re.compile(r'^\s*([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"\s*$')
_DEV_DEP_RE = re.compile(r'"\s*([A-Za-z0-9_.-]+)\s*==\s*([^"]+)"')


def _read_mise_pins(*, mise_file: Path) -> list[tuple[str, str]]:
    if not mise_file.is_file():
        return []
    pins: list[tuple[str, str]] = []
    in_tools_table = False
    for raw_line in mise_file.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_tools_table = stripped == "[tools]"
            continue
        if not in_tools_table:
            continue
        match = _MISE_PIN_LINE_RE.match(raw_line)
        if match:
            pins.append((match.group(1), match.group(2)))
    return pins


def _read_dev_deps(*, pyproject_file: Path) -> list[tuple[str, str]]:
    if not pyproject_file.is_file():
        return []
    text = pyproject_file.read_text(encoding="utf-8")
    in_dev_group = False
    deps: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("dev = ["):
            in_dev_group = True
            continue
        if in_dev_group:
            if stripped.startswith("]"):
                in_dev_group = False
                continue
            match = _DEV_DEP_RE.search(raw_line)
            if match:
                deps.append((match.group(1), match.group(2)))
    return deps


_VERSION_FLAG_BY_TOOL: dict[str, list[str]] = {
    "lefthook": ["version"],
}


def _version_argv(*, name: str) -> list[str]:
    flag = _VERSION_FLAG_BY_TOOL.get(name, ["--version"])
    return [name, *flag]


def _binary_version_check(*, name: str, expected: str) -> str | None:
    try:
        # S603: argv is a fixed list (binary name + version-flag literal);
        # name is read from local .mise.toml; no untrusted input.
        result = subprocess.run(  # noqa: S603
            _version_argv(name=name),
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        return f"{name} not on PATH ({exc.__class__.__name__})"
    if result.returncode != 0:
        return f"{name} version-query exited {result.returncode}"
    output = result.stdout + " " + result.stderr
    if expected not in output:
        return f"{name} pinned to {expected}; actual output did not contain pin: {output.strip()!r}"
    return None


def _package_version_check(*, pkg_name: str, expected: str) -> str | None:
    try:
        actual = importlib.metadata.version(pkg_name)
    except importlib.metadata.PackageNotFoundError:
        return f"{pkg_name} not installed (expected {expected})"
    if actual != expected:
        return f"{pkg_name} pinned to {expected}; actual installed: {actual}"
    return None


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
    failures: list[str] = []
    for name, expected in _read_mise_pins(mise_file=cwd / _MISE_PATH):
        problem = _binary_version_check(name=name, expected=expected)
        if problem is not None:
            failures.append(problem)
    for pkg_name, expected in _read_dev_deps(pyproject_file=cwd / _PYPROJECT_PATH):
        problem = _package_version_check(pkg_name=pkg_name, expected=expected)
        if problem is not None:
            failures.append(problem)
    for problem in failures:
        log.error("pinned tool/package mismatch", message=problem)
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
