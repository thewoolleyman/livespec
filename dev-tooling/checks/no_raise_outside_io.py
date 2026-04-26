"""no_raise_outside_io: restrict LivespecError raise sites to io/** and errors.py.

Per python-skill-script-style-requirements.md line 1804:
"raising of `LivespecError` subclasses (domain errors) at runtime
restricted to `io/**` and `errors.py`. Raising bug-class
exceptions (TypeError, NotImplementedError, AssertionError, etc.)
permitted anywhere."

Per v017 Q3 (style doc line 1801-1802): the import-surface
contract was retracted; the raise-site enforcement here is the
sole enforcement point for the raise-discipline.

Domain errors are defined in
`.claude-plugin/scripts/livespec/errors.py`. The check enumerates
the `LivespecError` family by parsing `errors.py`'s AST: the set
includes `LivespecError` itself plus every direct subclass found
in that file. `HelpRequested` is intentionally NOT in the set —
it does not subclass `LivespecError` and is permitted to be
raised anywhere it's needed.

Permitted raise locations:
- `.claude-plugin/scripts/livespec/io/**`
- `.claude-plugin/scripts/livespec/errors.py`

Forbidden everywhere else inside
`.claude-plugin/scripts/livespec/**`.
"""
from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_file",
    "domain_error_names",
    "main",
]


log = logging.getLogger(__name__)

_LIVESPEC_DIR = Path(".claude-plugin/scripts/livespec")
_IO_DIR = Path(".claude-plugin/scripts/livespec/io")
_ERRORS_FILE = Path(".claude-plugin/scripts/livespec/errors.py")
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"
_BASE_NAME = "LivespecError"


def main() -> int:
    """Walk livespec/**; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    errors_path = repo_root / _ERRORS_FILE
    domain_names = (
        domain_error_names(errors_path=errors_path) if errors_path.is_file() else frozenset()
    )
    livespec_dir = repo_root / _LIVESPEC_DIR
    if livespec_dir.is_dir():
        for path in sorted(livespec_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            relative = path.relative_to(repo_root)
            for v in check_file(path=path, relative=relative, domain_names=domain_names):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("no_raise_outside_io: %d violation(s)", len(failures))
        return 1
    return 0


def domain_error_names(*, errors_path: Path) -> frozenset[str]:
    """Enumerate the LivespecError family by parsing errors.py.

    Returns `LivespecError` itself plus every direct subclass found
    in the module. Names referenced as bases via `ast.Name` only —
    attribute-style bases (`module.LivespecError`) are not expected
    in livespec code.
    """
    text = errors_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(errors_path))
    except SyntaxError:
        return frozenset({_BASE_NAME})
    names: set[str] = {_BASE_NAME}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == _BASE_NAME:
                names.add(node.name)
                break
    return frozenset(names)


def check_file(
    *,
    path: Path,
    relative: Path,
    domain_names: frozenset[str],
) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    if _is_exempt(relative=relative):
        return []
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        raised_name = _raised_name(raise_node=node)
        if raised_name is None:
            continue
        if raised_name in domain_names:
            violations.append(
                f"line {node.lineno}: raise `{raised_name}` outside io/** "
                f"and errors.py forbidden",
            )
    return violations


def _is_exempt(*, relative: Path) -> bool:
    """True if `relative` is inside io/** or is errors.py."""
    if relative == _ERRORS_FILE:
        return True
    return (
        len(relative.parts) >= len(_IO_DIR.parts) + 1
        and Path(*relative.parts[: len(_IO_DIR.parts)]) == _IO_DIR
    )


def _raised_name(*, raise_node: ast.Raise) -> str | None:
    """Return the bare name of the raised class if any, else None."""
    exc = raise_node.exc
    if exc is None:
        return None
    if isinstance(exc, ast.Name):
        return exc.id
    if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
        return exc.func.id
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
