"""wrapper_shape — `bin/*.py` conforms to the canonical shebang-wrapper shape.

Per `python-skill-script-style-requirements.md` lines 1937-1968
(and PROPOSAL.md lines 397-412) each file under
`.claude-plugin/scripts/bin/*.py` (except `_bootstrap.py`) MUST
consist of exactly five top-level Python statements in this
order. Note: the spec text says "6 statements" because it counts
the `#!/usr/bin/env python3` shebang LINE alongside the 5
Python-AST statements. The shebang is a comment line and does
NOT appear in `ast.parse(...).body`; a conformant wrapper has
exactly 5 entries in `tree.body`. The expected shape:

    1. Module docstring (Expr(Constant(str))).
    2. `from _bootstrap import bootstrap` (ImportFrom).
    3. `bootstrap()` (Expr(Call(Name("bootstrap")))).
    4. `from livespec.<...> import main` (ImportFrom).
    5. `raise SystemExit(main())` (Raise(Call(Name("SystemExit"),
       Call(Name("main"))))).

The shebang `#!/usr/bin/env python3` is a comment line, not a
Python statement. The optional single blank line between the
import block and the final `raise` is permitted (v016 P5) and
does NOT count as a statement.

The check walks `.claude-plugin/scripts/bin/*.py`, parses each
file's AST, skips `_bootstrap.py`, and verifies the body matches
the 5-statement template. Any deviation (extra statements,
missing statements, wrong statement type, wrong import target)
is a violation. One structlog diagnostic per offender; exit 1
if any wrapper deviates.
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
_BOOTSTRAP_FILENAME = "_bootstrap.py"
_EXPECTED_BODY_LEN = 5


def _is_docstring(*, node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_bootstrap_import(*, node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == "_bootstrap"
        and len(node.names) == 1
        and node.names[0].name == "bootstrap"
    )


def _is_bootstrap_call(*, node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "bootstrap"
        and not node.value.args
        and not node.value.keywords
    )


def _is_main_import(*, node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("livespec.")
        and len(node.names) == 1
        and node.names[0].name == "main"
    )


def _is_raise_systemexit_main(*, node: ast.stmt) -> bool:
    if not isinstance(node, ast.Raise) or node.exc is None:
        return False
    outer = node.exc
    if not isinstance(outer, ast.Call) or not isinstance(outer.func, ast.Name):
        return False
    if outer.func.id != "SystemExit" or len(outer.args) != 1:
        return False
    inner = outer.args[0]
    return (
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Name)
        and inner.func.id == "main"
        and not inner.args
        and not inner.keywords
    )


def _conforms(*, body: list[ast.stmt]) -> bool:
    if len(body) != _EXPECTED_BODY_LEN:
        return False
    return (
        _is_docstring(node=body[0])
        and _is_bootstrap_import(node=body[1])
        and _is_bootstrap_call(node=body[2])
        and _is_main_import(node=body[3])
        and _is_raise_systemexit_main(node=body[4])
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
    if not bin_root.is_dir():
        return 0
    found_any = False
    for py_file in sorted(bin_root.glob("*.py")):
        if py_file.name == _BOOTSTRAP_FILENAME:
            continue
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        if not _conforms(body=module_ast.body):
            log.error(
                "wrapper does not match canonical shape",
                path=str(py_file.relative_to(cwd)),
                statement_count=len(module_ast.body),
                expected=_EXPECTED_BODY_LEN,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
