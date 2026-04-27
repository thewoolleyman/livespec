"""check_tools: verify every pinned tool is installed at the pinned version.

Per python-skill-script-style-requirements.md canonical target list
line 1900:

    Verify every pinned tool is installed at the pinned version —
    both mise-pinned binaries (`uv`, `just`, `lefthook`) and
    uv-managed Python deps from `pyproject.toml`
    `[dependency-groups.dev]` per v024.

Sources of truth:

- `.mise.toml` `[tools]` table — non-Python binaries.
- `pyproject.toml` `[dependency-groups]` `dev` array — Python
  packages installed by `uv sync --all-groups` into the
  project-local `.venv`.

Per-binary verification: `<tool> --version` is invoked via
`subprocess.run`; the first version-like substring in the output
is matched against the pin. Per-package verification:
`importlib.metadata.version(<pkg>)` reads the installed
distribution metadata; the result is compared against the pin.

Pin equality is exact-string match on the version core (e.g.,
`"1.36.0"` matches `"just 1.36.0 (...)"`). Loose semver matches
(e.g., pin `"1.36"` matches `"1.36.0"`) are NOT supported —
pins are exact.
"""

from __future__ import annotations

import importlib.metadata
import logging
import re
import subprocess
import sys
from pathlib import Path

__all__: list[str] = [
    "check_repo",
    "main",
]


log = logging.getLogger(__name__)

_MISE_PATH = Path(".mise.toml")
_PYPROJECT_PATH = Path("pyproject.toml")
_PIN_LINE_RE = re.compile(r'^\s*([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"\s*$')
_DEP_RE = re.compile(r'"\s*([A-Za-z0-9_.-]+)\s*==\s*([^"]+)"')


def main() -> int:
    repo_root = Path.cwd()
    failures = check_repo(repo_root=repo_root)
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("check_tools: %d violation(s)", len(failures))
        return 1
    return 0


def check_repo(*, repo_root: Path) -> list[str]:
    """Verify mise-pinned binaries + uv-managed Python deps are at pinned versions."""
    violations: list[str] = []
    mise_pins = _parse_mise_tools(path=repo_root / _MISE_PATH)
    if mise_pins is None:
        return [f"{_MISE_PATH}: missing or unreadable [tools] section"]
    py_pins = _parse_pyproject_dev_deps(path=repo_root / _PYPROJECT_PATH)
    if py_pins is None:
        return [f"{_PYPROJECT_PATH}: missing or unreadable [dependency-groups] dev"]
    for tool, pinned_version in sorted(mise_pins.items()):
        message = _check_binary(tool=tool, pinned_version=pinned_version)
        if message is not None:
            violations.append(message)
    for pkg, pinned_version in sorted(py_pins.items()):
        message = _check_python_package(pkg=pkg, pinned_version=pinned_version)
        if message is not None:
            violations.append(message)
    return violations


def _check_binary(*, tool: str, pinned_version: str) -> str | None:
    try:
        completed = subprocess.run(  # noqa: S603 — tool name from trusted .mise.toml
            [tool, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return f"binary `{tool}` not on PATH (pinned to {pinned_version})"
    output = (completed.stdout or "") + (completed.stderr or "")
    if pinned_version not in output:
        return (
            f"binary `{tool}` version mismatch — pinned to {pinned_version}, "
            f"`{tool} --version` produced: {output.strip()[:200]!r}"
        )
    return None


def _check_python_package(*, pkg: str, pinned_version: str) -> str | None:
    try:
        installed = importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return f"python package `{pkg}` not installed (pinned to {pinned_version})"
    if installed != pinned_version:
        return (
            f"python package `{pkg}` version mismatch — pinned to "
            f"{pinned_version}, installed {installed}"
        )
    return None


def _parse_mise_tools(*, path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    in_tools = False
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip().startswith("[") and line.strip().endswith("]"):
            in_tools = line.strip() == "[tools]"
            continue
        if not in_tools:
            continue
        match = _PIN_LINE_RE.match(line)
        if match:
            pins[match.group(1)] = match.group(2)
    return pins if pins else None


def _parse_pyproject_dev_deps(*, path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    section = _extract_dev_array(text=text)
    if section is None:
        return None
    pins: dict[str, str] = {}
    for match in _DEP_RE.finditer(section):
        pins[match.group(1)] = match.group(2)
    return pins if pins else None


def _extract_dev_array(*, text: str) -> str | None:
    """Find `[dependency-groups]` block and the `dev = [...]` array within it."""
    in_group = False
    capturing = False
    bracket_depth = 0
    captured: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_group = stripped == "[dependency-groups]"
            continue
        if not in_group:
            continue
        if not capturing and re.match(r"\s*dev\s*=\s*\[", line):
            capturing = True
            bracket_depth = line.count("[") - line.count("]")
            captured.append(line)
            if bracket_depth == 0:
                break
            continue
        if capturing:
            captured.append(line)
            bracket_depth += line.count("[") - line.count("]")
            if bracket_depth <= 0:
                break
    return "\n".join(captured) if captured else None


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
