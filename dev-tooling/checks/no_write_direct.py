"""no_write_direct: ban sys.stdout/stderr.write outside 3 designated surfaces.

Per python-skill-script-style-requirements.md line 1816: bans
`sys.stdout.write` and `sys.stderr.write` calls in
`.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`,
and `<repo-root>/dev-tooling/**`. Three exemptions:

1. `bin/_bootstrap.py` — pre-import version-check stderr.
2. Supervisor `main()` functions in
   `livespec/commands/**.py` — any documented stdout contract
   (HelpRequested per K7, resolve_template path per K2, etc.).
3. `livespec/doctor/run_static.py::main()` — findings JSON
   stdout per the static-phase output contract.

Pairs with ruff `T20` which bans `print` and `pprint`.

Implementation: AST walk. For every `Call` node where the
function is `sys.stdout.write` or `sys.stderr.write`, check
whether the call site is inside one of the three exempted
scopes. The exemption is per-supervisor `main()` at module
top-level — NOT per-helper inside commands/** (style doc lines
1478-1481).
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

_SCOPE_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin/scripts/livespec"),
    Path(".claude-plugin/scripts/bin"),
    Path("dev-tooling"),
)
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_BOOTSTRAP_PATH = Path(".claude-plugin/scripts/bin/_bootstrap.py")
_COMMANDS_DIR = Path(".claude-plugin/scripts/livespec/commands")
_DOCTOR_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")


def main() -> int:
    """Walk scoped trees; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            relative = path.relative_to(repo_root)
            violations = check_file(path=path, relative=relative)
            for v in violations:
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("no_write_direct: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass.

    `relative` is the repo-root-relative path used for exemption
    matching against `_BOOTSTRAP_PATH`, `_COMMANDS_DIR`, and
    `_DOCTOR_RUN_STATIC`.
    """
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    if relative == _BOOTSTRAP_PATH:
        return []
    is_command_file = (
        len(relative.parts) >= len(_COMMANDS_DIR.parts) + 1
        and Path(*relative.parts[: len(_COMMANDS_DIR.parts)]) == _COMMANDS_DIR
    )
    is_run_static = relative == _DOCTOR_RUN_STATIC
    is_exempted_file = is_command_file or is_run_static
    violations: list[str] = []
    for child in tree.body:
        _walk(
            node=child,
            inside_main=False,
            is_exempted_file=is_exempted_file,
            violations=violations,
        )
    return violations


def _walk(
    *,
    node: ast.AST,
    inside_main: bool,
    is_exempted_file: bool,
    violations: list[str],
) -> None:
    """Recursive AST walker that tracks main() lexical scope.

    Recognizes `main()` only when it's encountered as a module-top
    statement (`inside_main=False` initially per the call from
    `check_file`'s loop over `tree.body`). Nested `def`s declared
    INSIDE the recognized `main()` inherit the exemption — they're
    part of main's lexical scope and a normal Python idiom. A
    module-top-level helper `def` (sibling of main) does NOT inherit
    the exemption.
    """
    if isinstance(node, ast.Call) and not inside_main and _is_sys_write_call(node=node):
        attr_chain = _attr_chain(func=node.func)
        violations.append(
            f"line {node.lineno}: {attr_chain}() forbidden outside designated surfaces",
        )
    enters_main = (
        is_exempted_file
        and not inside_main
        and isinstance(node, ast.FunctionDef)
        and node.name == "main"
    )
    child_inside_main = inside_main or enters_main
    for child in ast.iter_child_nodes(node):
        _walk(
            node=child,
            inside_main=child_inside_main,
            is_exempted_file=is_exempted_file,
            violations=violations,
        )


def _is_sys_write_call(*, node: ast.Call) -> bool:
    """True iff `node` is `sys.stdout.write(...)` or `sys.stderr.write(...)`."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "write":
        return False
    parent = func.value
    if not isinstance(parent, ast.Attribute) or parent.attr not in {"stdout", "stderr"}:
        return False
    grandparent = parent.value
    return isinstance(grandparent, ast.Name) and grandparent.id == "sys"


def _attr_chain(*, func: ast.expr) -> str:
    """Render `sys.stdout.write` etc. as a string for diagnostic messages."""
    parts: list[str] = []
    cur: ast.expr = func
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
