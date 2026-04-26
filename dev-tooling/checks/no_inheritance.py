"""no_inheritance: enforce v013 M5 direct-parent allowlist.

Per python-skill-script-style-requirements.md lines 943-967
(v013 M5): class inheritance in `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
is RESTRICTED. The AST check rejects any `class X(Y):` definition
where `Y` is not in the direct-parent allowlist:

    {Exception, BaseException, LivespecError, Protocol,
     NamedTuple, TypedDict}

The rule is DIRECT-PARENT only: `LivespecError` subclasses
(e.g., `UsageError`, `ValidationError`) are NOT acceptable bases
for further subclassing.

Permitted forms:
- `class X:`              — no explicit parent (implicit `object`).
- `class X(Exception):`   — Exception in allowlist.
- `class X(LivespecError):` — LivespecError in allowlist.
- `class X(Protocol):`    — Protocol in allowlist.
- `class X(NamedTuple):`  — NamedTuple in allowlist.
- `class X(TypedDict):`   — TypedDict in allowlist.
- `class X(BaseException):` — BaseException in allowlist.

Rejected:
- `class X(UsageError):`         — UsageError not in allowlist.
- `class X(SomeOtherClass):`     — generic inheritance forbidden.
- `class X(SomeABC):` (when SomeABC is `abc.ABC`) — banned via TID.
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

_ALLOWLIST: frozenset[str] = frozenset({
    "BaseException",
    "Exception",
    "LivespecError",
    "NamedTuple",
    "Protocol",
    "TypedDict",
})


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
            violations = check_file(path=path)
            for v in violations:
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("no_inheritance: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return a list of violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name = _base_name(base=base)
            if base_name is None:
                violations.append(
                    f"line {node.lineno}: class {node.name} has non-name base "
                    f"{ast.unparse(base)}; only allowlist names permitted",
                )
                continue
            if base_name not in _ALLOWLIST:
                violations.append(
                    f"line {node.lineno}: class {node.name}({base_name}) — "
                    f"{base_name!r} not in direct-parent allowlist "
                    f"{sorted(_ALLOWLIST)}",
                )
    return violations


def _base_name(*, base: ast.expr) -> str | None:
    """Return the base-class name as a string if it's a simple `Name`
    or a parametric `Name[...]` (`ast.Subscript`), otherwise None.

    For `class X(typing.Protocol):` the base is an `ast.Attribute`;
    we don't unwrap that — the spec uses bare-name imports
    (`from typing import Protocol`), so `class X(Protocol):` is the
    canonical form. Attribute-style bases are flagged for review.

    Parametric Protocols (`class X(Protocol[T]):`) are recognized
    because Python's generic-Protocol surface uses subscript syntax;
    rejecting them would force a `# type: ignore` workaround for
    every generic Protocol the codebase declares.
    """
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
        return base.value.id
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
