"""assert_never_exhaustiveness — every `match` ends in `case _: assert_never(...)`.

Per `python-skill-script-style-requirements.md` lines 1051-1068
every `match` statement in `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
MUST terminate with `case _: assert_never(<subject>)` regardless
of subject type.

Rationale: `assert_never(x)` requires `x` to have type `Never`.
Adding a new variant of a closed-union subject without updating
the dispatch site narrows the residual at the default arm to the
unhandled variant; pyright then flags `assert_never(x)` as a
type error at every unhandled site.

The check walks the three in-scope trees, finds every `Match`
node, and verifies the LAST `case` arm:

1. Has a wildcard pattern (`MatchAs(pattern=None, name=None)`)
   — equivalent to `case _:`.
2. Body is a single `Expr` statement whose value is
   `Call(func=Name("assert_never"), args=[<subject>])`.

A match without this terminator is rejected. One structlog
diagnostic per offender; exit 1 if any matched.

Cycle 42 pins the canonical violation: a match without a
terminator at all. Refinements (e.g., asserting the subject in
the call matches the match's subject) are deferred per v032 D1
one-pattern-per-cycle.
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


_IN_SCOPE_TREES: tuple[Path, ...] = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
)


def _is_wildcard_pattern(*, pattern: ast.pattern) -> bool:
    return isinstance(pattern, ast.MatchAs) and pattern.pattern is None and pattern.name is None


def _is_assert_never_call(*, body: list[ast.stmt]) -> bool:
    if len(body) != 1:
        return False
    stmt = body[0]
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return False
    call = stmt.value
    if not isinstance(call.func, ast.Name) or call.func.id != "assert_never":
        return False
    return len(call.args) == 1


def _has_assert_never_terminator(*, match_node: ast.Match) -> bool:
    if not match_node.cases:
        return False
    last_case = match_node.cases[-1]
    if not _is_wildcard_pattern(pattern=last_case.pattern):
        return False
    return _is_assert_never_call(body=last_case.body)


def _find_violations(*, tree: ast.Module) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Match) and not _has_assert_never_terminator(match_node=node)
    ]


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
    log = structlog.get_logger("assert_never_exhaustiveness")
    cwd = Path.cwd()
    found_any = False
    for tree_path in _IN_SCOPE_TREES:
        tree_root = cwd / tree_path
        if not tree_root.is_dir():
            continue
        for py_file in _iter_python_files(root=tree_root):
            source = py_file.read_text(encoding="utf-8")
            module_ast = ast.parse(source, filename=str(py_file))
            for lineno in _find_violations(tree=module_ast):
                log.error(
                    "match missing `case _: assert_never(<subject>)` terminator",
                    path=str(py_file.relative_to(cwd)),
                    line=lineno,
                )
                found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
