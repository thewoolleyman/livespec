"""wrapper_shape — `bin/*.py` 6-statement shebang-wrapper shape (except `_bootstrap.py`).

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-wrapper-shape` row), every
`.claude-plugin/scripts/bin/*.py` file (except
`_bootstrap.py`) MUST conform to the 6-statement shebang-
wrapper shape:

    #!/usr/bin/env python3
    \"\"\"Shebang wrapper for <name>. ...\"\"\"

    from _bootstrap import bootstrap

    bootstrap()

    from livespec.<...> import main

    raise SystemExit(main())

The AST module body has exactly 5 top-level statements (the
docstring counts as an `Expr(Constant(str))`):

1. `Expr(Constant(str))` — the module docstring.
2. `ImportFrom(module="_bootstrap", names=["bootstrap"])`.
3. `Expr(Call(Name("bootstrap")))` — the bootstrap call.
4. `ImportFrom(module="livespec.<...>", names=["main"])`.
5. `Raise(exc=Call(Name("SystemExit"), args=[Call(Name("main"))]))`.

Any deviation (extra statements, missing pieces, wrong
order, wrong identifiers) surfaces as a violation. The
shebang line is a comment and isn't part of the AST body.

Output discipline: per spec lines 1738-1762, `print` (T20) and
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


_BIN_TREE = Path(".claude-plugin") / "scripts" / "bin"
_EXEMPT_NAMES = frozenset({"_bootstrap.py"})

# Per python-skill-script-style-requirements.md lines 1664-1668:
# the canonical shebang wrapper has exactly five top-level
# statements (docstring → bootstrap import → bootstrap() call →
# main import → SystemExit(main())). This constant names the
# load-bearing count.
_CANONICAL_WRAPPER_STMT_COUNT: int = 5


def _is_docstring(*, stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _is_bootstrap_import(*, stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.ImportFrom)
        and stmt.module == "_bootstrap"
        and len(stmt.names) == 1
        and stmt.names[0].name == "bootstrap"
    )


def _is_bootstrap_call(*, stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Expr):
        return False
    call = stmt.value
    return (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "bootstrap"
    )


def _is_livespec_main_import(*, stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.ImportFrom)
        and stmt.module is not None
        and stmt.module.startswith("livespec.")
        and len(stmt.names) == 1
        and stmt.names[0].name == "main"
    )


def _is_raise_systemexit_main(*, stmt: ast.stmt) -> bool:
    if not (isinstance(stmt, ast.Raise) and isinstance(stmt.exc, ast.Call)):
        return False
    outer = stmt.exc
    return (
        isinstance(outer.func, ast.Name)
        and outer.func.id == "SystemExit"
        and len(outer.args) == 1
        and isinstance(outer.args[0], ast.Call)
        and isinstance(outer.args[0].func, ast.Name)
        and outer.args[0].func.id == "main"
    )


def _is_compliant_wrapper(*, source: str) -> bool:
    tree = ast.parse(source)
    body = tree.body
    if len(body) != _CANONICAL_WRAPPER_STMT_COUNT:
        return False
    return (
        _is_docstring(stmt=body[0])
        and _is_bootstrap_import(stmt=body[1])
        and _is_bootstrap_call(stmt=body[2])
        and _is_livespec_main_import(stmt=body[3])
        and _is_raise_systemexit_main(stmt=body[4])
    )


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("wrapper_shape")
    cwd = Path.cwd()
    bin_root = cwd / _BIN_TREE
    offenders: list[Path] = []
    if bin_root.is_dir():
        for py_file in sorted(bin_root.glob("*.py")):
            if py_file.name in _EXEMPT_NAMES:
                continue
            source = py_file.read_text(encoding="utf-8")
            if not _is_compliant_wrapper(source=source):
                offenders.append(py_file.relative_to(cwd))
    if offenders:
        for path in offenders:
            log.error(
                "bin/*.py wrapper shape deviates from canonical 5-statement form",
                file=str(path),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
