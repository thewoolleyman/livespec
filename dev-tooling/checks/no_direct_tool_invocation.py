"""no_direct_tool_invocation — `run:` lines only invoke `just <target>`.

Per `python-skill-script-style-requirements.md` line 2097 and
PROPOSAL.md §"Dev tooling and task runner":

    grep: `lefthook.yml` and `.github/workflows/*.yml` only
    invoke `just <target>` (no direct `ruff` / `pyright` /
    `pytest` / `python3` / `mutmut` / `lint-imports`
    invocations).

The check walks `lefthook.yml` (if present at repo root) and
every `*.yml` under `.github/workflows/`. For each `run:` field
it scans the inlined value (single-line form) for any banned
tool word. Multi-line `run: |` blocks are scanned line-by-line
for the same banlist, since they execute as shell where each
line could fire a check tool. Banlist:

- `ruff` / `pyright` / `pytest` / `mutmut` / `lint-imports` /
  `python` / `python3`

Allowlist (intentionally NOT banned): `just`, `uv` (env
manager — `uv sync` is environment setup, not a check
invocation), shell builtins (`if`, `echo`, `exit`, etc.).
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


_LEFTHOOK = Path("lefthook.yml")
_WORKFLOWS_DIR = Path(".github") / "workflows"
_BANNED_TOOLS = (
    "ruff",
    "pyright",
    "pytest",
    "mutmut",
    "lint-imports",
    "python3",
    "python",
)
_BANNED_PATTERN = re.compile(
    r"(?<![\w\-])(" + "|".join(re.escape(t) for t in _BANNED_TOOLS) + r")(?![\w\-])",
)
_RUN_INLINE_PATTERN = re.compile(r"^\s*-?\s*run:\s*(?P<value>.+?)\s*$")
_RUN_BLOCK_HEADER_PATTERN = re.compile(r"^(?P<indent>\s*)-?\s*run:\s*[|>][+-]?\s*$")


def _scan_run_value(*, value: str) -> str | None:
    match = _BANNED_PATTERN.search(value)
    if match:
        return match.group(1)
    return None


def _scan_yaml(*, lines: list[str]) -> list[tuple[int, str, str]]:
    offenders: list[tuple[int, str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        block_match = _RUN_BLOCK_HEADER_PATTERN.match(line)
        if block_match:
            block_indent = len(block_match.group("indent"))
            j = i + 1
            while j < len(lines):
                inner = lines[j]
                if inner.strip() == "":
                    j += 1
                    continue
                inner_indent = len(inner) - len(inner.lstrip())
                if inner_indent <= block_indent:
                    break
                hit = _scan_run_value(value=inner)
                if hit is not None:
                    offenders.append((j + 1, inner.strip(), hit))
                j += 1
            i = j
            continue
        inline_match = _RUN_INLINE_PATTERN.match(line)
        if inline_match:
            value = inline_match.group("value")
            hit = _scan_run_value(value=value)
            if hit is not None:
                offenders.append((i + 1, value, hit))
        i += 1
    return offenders


def _iter_yaml_files(*, cwd: Path) -> list[Path]:
    out: list[Path] = []
    lefthook = cwd / _LEFTHOOK
    if lefthook.is_file():
        out.append(lefthook)
    workflows = cwd / _WORKFLOWS_DIR
    if workflows.is_dir():
        out.extend(sorted(p for p in workflows.glob("*.yml") if p.is_file()))
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
    found_any = False
    for yaml_file in _iter_yaml_files(cwd=cwd):
        lines = yaml_file.read_text(encoding="utf-8").splitlines()
        for lineno, run_value, banned in _scan_yaml(lines=lines):
            log.error(
                "direct tool invocation in run: line",
                path=str(yaml_file.relative_to(cwd)),
                line=lineno,
                tool=banned,
                run_value=run_value,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
