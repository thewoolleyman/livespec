"""tests_mirror_pairing — every covered `.py` has a paired test (v033 D1).

Per `SPECIFICATION/spec.md` §"Testing approach" (post-v006), every
`.py` file under `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/
checks/**` MUST have a paired test file at the mirror path under
`tests/`, except:

(a) **Private-helper modules** — `.py` files whose filename starts
    with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`).
    Their behavior is exercised through the public function that
    imports them.
(b) **Pure declaration modules** — files whose AST contains no
    `FunctionDef` or `AsyncFunctionDef` anywhere (no module-level
    or class-level functions). This covers boilerplate `__init__.py`,
    pure dataclass declarations under `schemas/dataclasses/`, the
    `DoctorContext` value-object, the `LivespecError` hierarchy,
    and the static-check registry — none of which have testable
    behavior independent of the consumers tested elsewhere.
(c) `bin/_bootstrap.py` — special-cased; covered by
    `tests/bin/test_bootstrap.py`.

Output discipline: per spec lines 1738-1762, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
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


_SOURCE_TREES_TO_TESTS: dict[Path, Path] = {
    Path(".claude-plugin") / "scripts" / "livespec": Path("tests") / "livespec",
    Path(".claude-plugin") / "scripts" / "bin": Path("tests") / "bin",
    Path("dev-tooling") / "checks": Path("tests") / "dev-tooling" / "checks",
}
_BOOTSTRAP_REL = Path(".claude-plugin") / "scripts" / "bin" / "_bootstrap.py"


def _expected_paired_test_path(*, source_path: Path, source_tree: Path, tests_tree: Path) -> Path:
    rel = source_path.relative_to(source_tree)
    parent = rel.parent
    name = rel.name
    test_name = f"test_{name[1:]}" if name.startswith("_") else f"test_{name}"
    return tests_tree / parent / test_name


def _is_private_helper_module(*, name: str) -> bool:
    return name.startswith("_") and name != "__init__.py"


def _is_pure_declaration_module(*, source_path: Path) -> bool:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return False
    return True


def _is_exempt(*, source_path: Path, cwd: Path) -> bool:
    rel_to_cwd = source_path.relative_to(cwd)
    if rel_to_cwd == _BOOTSTRAP_REL:
        return True
    if _is_private_helper_module(name=source_path.name):
        return True
    return _is_pure_declaration_module(source_path=source_path)


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
    log = structlog.get_logger("tests_mirror_pairing")
    cwd = Path.cwd()
    offenders: list[tuple[Path, Path]] = []
    for source_tree_rel, tests_tree_rel in _SOURCE_TREES_TO_TESTS.items():
        source_tree = cwd / source_tree_rel
        if not source_tree.is_dir():
            continue
        tests_tree = cwd / tests_tree_rel
        for py_file in _iter_python_files(root=source_tree):
            if _is_exempt(source_path=py_file, cwd=cwd):
                continue
            expected_pair = _expected_paired_test_path(
                source_path=py_file, source_tree=source_tree, tests_tree=tests_tree
            )
            if not expected_pair.is_file():
                offenders.append((py_file.relative_to(cwd), expected_pair.relative_to(cwd)))
    if offenders:
        for source_rel, pair_rel in offenders:
            log.error(
                "source missing paired test file",
                source=str(source_rel),
                expected_pair=str(pair_rel),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
