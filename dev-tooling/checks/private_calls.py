"""private_calls: ban cross-module imports of _-prefixed names.

Per python-skill-script-style-requirements.md line 1801:
"no cross-module calls to `_`-prefixed functions defined
elsewhere."

A single-leading-underscore prefix on a name signals "private to
this module" — internal helper, not part of the module's public
API. Cross-module imports of such names break the encapsulation:
they expose a private helper as if it were public.

This check walks Python files in livespec/**, bin/**, and
dev-tooling/** and flags any `from <module> import _name` (or
`import <module>._name` etc.) where the imported name starts with
a single underscore (NOT a double underscore — dunders like
`__future__` and `__all__` are not "private" in this sense).

Exemption: `from _bootstrap import bootstrap` in bin/*.py is the
wrapper-shape-mandated cross-module import per style doc lines
1664-1668. The `_bootstrap` module name uses leading-underscore
to signal "pre-livespec-import bootstrap" but is whitelisted here
because the wrapper shape requires it.
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
_BIN_DIR = Path(".claude-plugin/scripts/bin")
_BOOTSTRAP_EXEMPTION = ("_bootstrap", "bootstrap")


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
        log.error("private_calls: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    is_bin_wrapper = (
        len(relative.parts) >= len(_BIN_DIR.parts) + 1
        and Path(*relative.parts[: len(_BIN_DIR.parts)]) == _BIN_DIR
    )
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imported = alias.name
                if _is_private_name(name=imported) and not _is_exempted(
                    module=module,
                    imported=imported,
                    is_bin_wrapper=is_bin_wrapper,
                ):
                    violations.append(
                        f"line {node.lineno}: cross-module import of private name "
                        f"`{imported}` from `{module or '<relative>'}`",
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                segments = alias.name.split(".")
                # Only flag if a non-leading segment is private
                # (e.g., `import livespec.io._helper` flags `_helper`,
                # but `import _bootstrap` is a top-level import handled by exemption).
                for segment in segments[1:]:
                    if _is_private_name(name=segment):
                        violations.append(
                            f"line {node.lineno}: import path traverses private "
                            f"segment `{segment}` in `{alias.name}`",
                        )
                        break
    return violations


def _is_private_name(*, name: str) -> bool:
    """True iff `name` has a single leading underscore (not a dunder)."""
    return name.startswith("_") and not name.startswith("__")


def _is_exempted(*, module: str, imported: str, is_bin_wrapper: bool) -> bool:
    """Check the wrapper-shape `from _bootstrap import bootstrap` exemption."""
    return (
        is_bin_wrapper
        and module == _BOOTSTRAP_EXEMPTION[0]
        and imported == _BOOTSTRAP_EXEMPTION[1]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
