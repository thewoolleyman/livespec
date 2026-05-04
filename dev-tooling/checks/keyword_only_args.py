"""keyword_only_args — `*`-separator on every `def` in `livespec/**`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-keyword-only-args` row), every `def`
in `.claude-plugin/scripts/livespec/**` MUST use `*` as the
first separator (every parameter keyword-only). Exempts:

- Python-mandated dunder signatures (`__init__`, `__repr__`,
  `__call__`, etc. — the runtime calls them with positional
  args).
- Methods that take a single positional `self` or `cls` first,
  followed by the `*` separator and keyword-only parameters
  thereafter.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`FunctionDef` and `AsyncFunctionDef`'s `args` block:

- If the function name is a dunder (matches `__*__`), exempt.
- If `args.args` is empty, the function is zero-positional
  and trivially compliant (no `*` needed).
- If `args.args` has exactly one entry whose name is `self`
  or `cls`, it's a regular method — the rest of the
  parameters MUST be in `args.kwonlyargs` and `args.args`
  beyond `self`/`cls` must be empty.
- Otherwise, `args.args` must be empty (every parameter is in
  `args.kwonlyargs`).

Cycle 154 implements the def-level check. Subsequent cycles
widen to `@dataclass(frozen=True, kw_only=True, slots=True)`
verification when fixtures demand it.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_LIVESPEC_TREE = Path(".claude-plugin") / "scripts" / "livespec"
_IMPLICIT_FIRST_PARAMS = frozenset({"self", "cls"})


def _is_dunder(*, name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _is_compliant(*, func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if _is_dunder(name=func.name):
        return True
    positional = func.args.args
    if len(positional) == 0:
        return True
    return bool(
        len(positional) == 1 and positional[0].arg in _IMPLICIT_FIRST_PARAMS,
    )


def _find_offenders(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not _is_compliant(
            func=node
        ):
            out.append((node.lineno, node.name))
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
    log = structlog.get_logger("keyword_only_args")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, fn_name in _find_offenders(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, fn_name))
    if offenders:
        for path, lineno, fn_name in offenders:
            log.error(
                "function missing `*` keyword-only separator",
                file=str(path),
                line=lineno,
                function=fn_name,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
