"""cli_explicit_project_root — every spec-side CLI accepts an explicit project-root.

Enforces the load-bearing, mechanically-checkable rule of
`SPECIFICATION/contracts.md`: *"Explicit
project-root addressing — every CLI accepts an explicit project-root,
so a consumer can address any repository's state through the named CLI
rather than by reading anything directly."*

The other shape conventions in that section are prose/contract
conventions, NOT mechanical per-CLI asserts, and are deliberately out
of this check's scope (recorded as the regroom residual on work-item
livespec-besm.2):

- "One binary per side with subcommands" — an architectural framing
  the reference impl realizes as one thin wrapper per operation under
  `.claude-plugin/scripts/bin/`; not a per-CLI add_argument assertion.
- "`--json` everywhere" — realized as the JSON wire format on
  stdin/stdout (input via `--*-json` flags, output as schema-conforming
  JSON on stdout), not a literal `--json` toggle flag.
- "Stable exit codes" — governed by the shared, not a per-CLI flag.
- "stdin/stdout plus files for payloads" — a wire convention.

The check scans, at the consuming repo `cwd`, every Python module
under `.claude-plugin/scripts/livespec/` that defines a module-level
`build_parser()` factory (the canonical spec-side CLI argument-parser
seam per `livespec/io/cli.py`). Each such module is a spec-side CLI and
MUST register an `add_argument("--project-root", ...)` inside its
`build_parser`. A `build_parser` without it is surfaced; exit 1.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_PACKAGE_REL = Path(".claude-plugin") / "scripts" / "livespec"
_BUILD_PARSER = "build_parser"
_PROJECT_ROOT_FLAG = "--project-root"


def _build_parser_funcs(*, tree: ast.Module) -> list[ast.FunctionDef]:
    """Module-level `def build_parser(...)` functions in the parsed module."""
    return [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == _BUILD_PARSER
    ]


def _registers_project_root(*, func: ast.FunctionDef) -> bool:
    """True iff `func` calls `<x>.add_argument("--project-root", ...)`."""
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == _PROJECT_ROOT_FLAG
        ):
            return True
    return False


def _offenders(*, repo_root: Path) -> list[str]:
    """Repo-relative paths of spec-side CLI modules missing --project-root."""
    package = repo_root / _PACKAGE_REL
    if not package.is_dir():
        return []
    offenders: list[str] = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        funcs = _build_parser_funcs(tree=tree)
        if not funcs:
            continue
        if not any(_registers_project_root(func=func) for func in funcs):
            offenders.append(str(path.relative_to(repo_root)))
    return offenders


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("cli_explicit_project_root")
    offenders = _offenders(repo_root=Path.cwd())
    if not offenders:
        return 0
    for path in offenders:
        log.error(
            "spec-side CLI build_parser does not register --project-root",
            check_id="cli-explicit-project-root",
            module=path,
            flag=_PROJECT_ROOT_FLAG,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
