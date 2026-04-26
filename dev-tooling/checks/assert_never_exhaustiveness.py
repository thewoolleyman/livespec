"""assert_never_exhaustiveness: enforce final `case _: assert_never(<subject>)`.

Per python-skill-script-style-requirements.md lines 983-1008 +
1851:

"Every `match` statement in `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
MUST terminate with `case _: assert_never(<subject>)` regardless
of subject type."

Rationale: `assert_never(x)` requires `x` to have type `Never`.
When all variants of a closed-union subject are handled by
preceding `case` arms, the residual type at the default arm is
`Never` and pyright accepts the call. When a new variant is added
without updating the dispatch site, the residual narrows to the
unhandled variant and `assert_never(x)` becomes a type error.
This converts "I added a new variant and forgot to handle it
somewhere" from a silent runtime bug into a compile-time error.

The conservative scope (every `match`, regardless of subject
type) is preferred over a precise scope (only closed-union
subjects) because false positives are cheap (just add the line)
and the simpler check is more maintainable.

Implementation:

1. Walk every `ast.Match` in scope.
2. Verify `match.subject` is an `ast.Name` (the canonical form;
   complex subjects are not enforced by this check at v1).
3. Verify the LAST case in `match.cases` is `case _:` — i.e.,
   `pattern` is `ast.MatchAs(pattern=None, name=None)`.
4. Verify the case body is exactly one statement: an
   `ast.Expr` wrapping an `ast.Call` whose function is
   `ast.Name(id="assert_never")` and whose single positional
   argument is `ast.Name(id=<subject_name>)`.

Scope: `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`.
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
            for v in check_file(path=path):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("assert_never_exhaustiveness: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Match):
            continue
        problem = _violation_for_match(match=node)
        if problem is not None:
            violations.append(f"line {node.lineno}: {problem}")
    return violations


def _violation_for_match(*, match: ast.Match) -> str | None:
    """Return a one-line violation description, or None on pass."""
    subject_name = _subject_name(match=match)
    if subject_name is None:
        return None
    if not match.cases:
        return "match has no case arms"
    last = match.cases[-1]
    if not _is_wildcard_case(case=last):
        return (
            f"match on `{subject_name}` does not terminate with `case _:` "
            f"(final case pattern is not the bare wildcard)"
        )
    if not _body_is_assert_never_of(body=last.body, subject_name=subject_name):
        return (
            f"match on `{subject_name}` final `case _:` body is not "
            f"`assert_never({subject_name})`"
        )
    return None


def _subject_name(*, match: ast.Match) -> str | None:
    """Return the subject's bare-Name id, or None for non-Name subjects."""
    if isinstance(match.subject, ast.Name):
        return match.subject.id
    return None


def _is_wildcard_case(*, case: ast.match_case) -> bool:
    """True iff `case` is a bare `case _:` (no `as`-binding, no guard)."""
    if case.guard is not None:
        return False
    pattern = case.pattern
    if not isinstance(pattern, ast.MatchAs):
        return False
    return pattern.pattern is None and pattern.name is None


def _body_is_assert_never_of(*, body: list[ast.stmt], subject_name: str) -> bool:
    """True iff body is exactly `assert_never(<subject_name>)`."""
    if len(body) != 1:
        return False
    stmt = body[0]
    if not isinstance(stmt, ast.Expr):
        return False
    call = stmt.value
    if not isinstance(call, ast.Call):
        return False
    if not isinstance(call.func, ast.Name) or call.func.id != "assert_never":
        return False
    if len(call.args) != 1 or call.keywords:
        return False
    arg = call.args[0]
    return isinstance(arg, ast.Name) and arg.id == subject_name


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
