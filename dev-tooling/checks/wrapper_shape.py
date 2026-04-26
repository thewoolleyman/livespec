"""wrapper_shape: enforce the 6-statement shebang-wrapper shape.

Per python-skill-script-style-requirements.md §"Shebang-wrapper
contract" (lines 1664-1668), every `.claude-plugin/scripts/bin/*.py`
file (excluding `_bootstrap.py`) MUST be exactly the following
6-statement structure:

    1. shebang: `#!/usr/bin/env python3`
    2. module docstring
    3. `from _bootstrap import bootstrap`
    4. `bootstrap()`
    5. `from livespec.<...> import main`
    6. `raise SystemExit(main())`

Per v016 P5, an OPTIONAL blank line between statement 4 and
statement 5 is permitted (and only there).

Exemption: `bin/_bootstrap.py` carries the pre-livespec sys.path
setup + Python version check; it does NOT match the 6-statement
shape. Skipped by this check.
"""
from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_file",
    "main",
]


log = logging.getLogger(__name__)

_SHEBANG = "#!/usr/bin/env python3"
_BIN_DIR = Path(".claude-plugin/scripts/bin")
_EXEMPT_FILES = frozenset({"_bootstrap.py"})
_REQUIRED_POST_DOCSTRING_STATEMENTS = 4


def main() -> int:
    """Walk `bin/*.py`, verify each matches the 6-statement shape.

    Returns 0 on pass; 1 on any violation.
    """
    repo_root = Path.cwd()
    bin_dir = repo_root / _BIN_DIR
    if not bin_dir.is_dir():
        log.error("%s does not exist; cannot check wrapper shape", bin_dir)
        return 1

    failures: list[str] = []
    for wrapper in sorted(bin_dir.glob("*.py")):
        if wrapper.name in _EXEMPT_FILES:
            continue
        violations = check_file(path=wrapper)
        for v in violations:
            failures.append(f"{wrapper}: {v}")

    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("wrapper-shape: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return a list of violation messages for `path`. Empty list = pass."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    violations: list[str] = []

    if not lines or lines[0] != _SHEBANG:
        violations.append(f"line 1 must be {_SHEBANG!r}")
        return violations

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]

    body = tree.body
    docstring_node = (
        body[0]
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
        else None
    )
    if docstring_node is None:
        violations.append("statement 2 must be a module docstring")
        return violations

    statements = body[1:]
    if len(statements) != _REQUIRED_POST_DOCSTRING_STATEMENTS:
        violations.append(
            f"expected {_REQUIRED_POST_DOCSTRING_STATEMENTS} post-docstring "
            f"statements (import bootstrap; bootstrap(); import main; "
            f"raise SystemExit(main())); got {len(statements)}",
        )
        return violations

    if not _is_from_import(statements[0], module="_bootstrap", name="bootstrap"):
        violations.append("statement 3 must be `from _bootstrap import bootstrap`")
    if not _is_call_expr(statements[1], func_name="bootstrap"):
        violations.append("statement 4 must be `bootstrap()`")
    if not _is_from_import_livespec_main(statements[2]):
        violations.append("statement 5 must be `from livespec.<...> import main`")
    if not _is_raise_systemexit_main_call(statements[3]):
        violations.append("statement 6 must be `raise SystemExit(main())`")

    return violations


def _is_from_import(node: ast.stmt, *, module: str, name: str) -> bool:
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.module != module:
        return False
    if len(node.names) != 1 or node.names[0].name != name:
        return False
    return node.names[0].asname is None


def _is_call_expr(node: ast.stmt, *, func_name: str) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    if not isinstance(node.value, ast.Call):
        return False
    if not isinstance(node.value.func, ast.Name):
        return False
    if node.value.func.id != func_name:
        return False
    return not (node.value.args or node.value.keywords)


def _is_from_import_livespec_main(node: ast.stmt) -> bool:
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.module is None or not node.module.startswith("livespec."):
        return False
    if len(node.names) != 1 or node.names[0].name != "main":
        return False
    return node.names[0].asname is None


def _is_raise_systemexit_main_call(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == "SystemExit"
        and len(node.exc.args) == 1
        and isinstance(node.exc.args[0], ast.Call)
        and isinstance(node.exc.args[0].func, ast.Name)
        and node.exc.args[0].func.id == "main"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
