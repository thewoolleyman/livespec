"""match_keyword_only: enforce keyword sub-patterns for livespec-authored class patterns.

Per python-skill-script-style-requirements.md lines 1352-1378 +
1811:

"Every `match` statement's class pattern resolving to a
livespec-authored class MUST bind via keyword sub-patterns
(`Foo(x=x)`), not positional (`Foo(x)`). This eliminates the need
for `__match_args__` on any livespec class — the class pattern
binds attributes by name, reading directly from the instance's
`.x`."

Class patterns resolving to third-party types
(`dry-python/returns`'s `Success`, `Failure`, `IOSuccess`,
`IOFailure`, `Result.Success`, `Result.Failure`) MAY use positional
destructure, because those libraries define `__match_args__`
idiomatically for sum-type wrappers.

Implementation:

1. Walk the file's AST for imports + ClassDefs. A name is
   "livespec-authored" if it's imported from a module starting with
   `livespec.` OR defined locally as an `ast.ClassDef`.
2. Walk for every `ast.Match`. For each `case` whose pattern is
   an `ast.MatchClass` (or contains one nested), check:
   - If the class name resolves to a livespec-authored class AND
     the pattern carries positional sub-patterns
     (`pattern.patterns` non-empty), record a violation.
   - Recurse into nested `MatchClass` patterns within `patterns`
     and `kwd_patterns`.

Empty class patterns (`Foo()`) are permitted: nothing is bound, so
positional-vs-keyword doesn't apply.

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
_LIVESPEC_PREFIX = "livespec"


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
        log.error("match_keyword_only: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    livespec_names = _collect_livespec_authored_names(tree=tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Match):
            continue
        for case in node.cases:
            _walk_pattern(
                pattern=case.pattern,
                livespec_names=livespec_names,
                violations=violations,
            )
    return violations


def _collect_livespec_authored_names(*, tree: ast.Module) -> frozenset[str]:
    """Names imported from `livespec.*` plus locally-defined ClassDefs."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == _LIVESPEC_PREFIX or module.startswith(f"{_LIVESPEC_PREFIX}."):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
    return frozenset(names)


def _walk_pattern(
    *,
    pattern: ast.pattern,
    livespec_names: frozenset[str],
    violations: list[str],
) -> None:
    """Recurse through pattern, flagging livespec-class positional destructures."""
    subpatterns = _subpatterns_of(pattern=pattern)
    if isinstance(pattern, ast.MatchClass):
        _check_match_class(
            pattern=pattern,
            livespec_names=livespec_names,
            violations=violations,
        )
    for sub in subpatterns:
        _walk_pattern(
            pattern=sub,
            livespec_names=livespec_names,
            violations=violations,
        )


def _subpatterns_of(*, pattern: ast.pattern) -> list[ast.pattern]:
    """Return the list of nested sub-patterns to recurse into."""
    if isinstance(pattern, ast.MatchClass):
        return [*pattern.patterns, *pattern.kwd_patterns]
    if isinstance(pattern, ast.MatchSequence | ast.MatchMapping | ast.MatchOr):
        return list(pattern.patterns)
    if isinstance(pattern, ast.MatchAs) and pattern.pattern is not None:
        return [pattern.pattern]
    return []


def _check_match_class(
    *,
    pattern: ast.MatchClass,
    livespec_names: frozenset[str],
    violations: list[str],
) -> None:
    cls_name = _match_class_name(pattern=pattern)
    if cls_name is not None and cls_name in livespec_names and pattern.patterns:
        violations.append(
            f"line {pattern.lineno}: `case {cls_name}(...)` uses positional "
            f"sub-patterns; livespec-authored classes require keyword form "
            f"`{cls_name}(field=field, ...)`",
        )


def _match_class_name(*, pattern: ast.MatchClass) -> str | None:
    """Return the bare-name id of the matched class, else None."""
    cls = pattern.cls
    if isinstance(cls, ast.Name):
        return cls.id
    if isinstance(cls, ast.Attribute):
        return cls.attr
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
