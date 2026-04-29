"""no_write_direct — bans `sys.stdout.write` / `sys.stderr.write`.

Per `python-skill-script-style-requirements.md` line 2092:

    AST: bans `sys.stdout.write` and `sys.stderr.write` calls
    in `.claude-plugin/scripts/livespec/**`,
    `.claude-plugin/scripts/bin/**`,
    `<repo-root>/dev-tooling/**`. Three exemptions:
    `bin/_bootstrap.py` (pre-import version-check stderr);
    supervisor `main()` functions in
    `livespec/commands/**.py` (any documented stdout contract);
    `livespec/doctor/run_static.py::main()` (findings JSON
    stdout). Pairs with ruff `T20` which bans `print` /
    `pprint`.

Cycle 43 pins the canonical violation: a `sys.stderr.write(...)`
or `sys.stdout.write(...)` call in any non-exempt module is
rejected. The exemptions are recognized at the file level
(`_bootstrap.py`) or function level (calls inside the body of
`main()` of `livespec/commands/<cmd>.py` or
`livespec/doctor/run_static.py`).
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
_BIN_TREE = Path(".claude-plugin") / "scripts" / "bin"
_DEV_TREE = Path("dev-tooling")
_IN_SCOPE_TREES: tuple[Path, ...] = (_LIVESPEC_TREE, _BIN_TREE, _DEV_TREE)
_BOOTSTRAP_FILENAME = "_bootstrap.py"
_STREAM_NAMES = frozenset({"stdout", "stderr"})
_COMMANDS_DEPTH = 2  # `commands/<cmd>.py` is two path components below livespec root.


def _is_sys_stream_write(*, call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "write":
        return False
    receiver = func.value
    return (
        isinstance(receiver, ast.Attribute)
        and isinstance(receiver.value, ast.Name)
        and receiver.value.id == "sys"
        and receiver.attr in _STREAM_NAMES
    )


def _is_supervisor_module(*, py_file: Path, cwd: Path) -> bool:
    livespec_root = cwd / _LIVESPEC_TREE
    if not py_file.is_relative_to(livespec_root):
        return False
    relative = py_file.relative_to(livespec_root)
    parts = relative.parts
    if parts[:1] == ("commands",) and len(parts) == _COMMANDS_DEPTH and parts[1].endswith(".py"):
        return True
    return parts == ("doctor", "run_static.py")


def _calls_inside_main(*, tree: ast.Module) -> set[int]:
    inside: set[int] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "main":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call):
                    inside.add(id(inner))
    return inside


def _find_violations(*, tree: ast.Module, supervisor: bool) -> list[int]:
    permitted = _calls_inside_main(tree=tree) if supervisor else set()
    offenders: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_sys_stream_write(call=node):
            continue
        if id(node) in permitted:
            continue
        offenders.append(node.lineno)
    return offenders


def _iter_python_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("no_write_direct")
    cwd = Path.cwd()
    found_any = False
    for tree_path in _IN_SCOPE_TREES:
        tree_root = cwd / tree_path
        if not tree_root.is_dir():
            continue
        for py_file in _iter_python_files(root=tree_root):
            if py_file.name == _BOOTSTRAP_FILENAME and tree_path == _BIN_TREE:
                continue
            is_supervisor = _is_supervisor_module(py_file=py_file, cwd=cwd)
            source = py_file.read_text(encoding="utf-8")
            module_ast = ast.parse(source, filename=str(py_file))
            for lineno in _find_violations(tree=module_ast, supervisor=is_supervisor):
                log.error(
                    "direct sys.std{out,err}.write call (use structlog)",
                    path=str(py_file.relative_to(cwd)),
                    line=lineno,
                )
                found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
