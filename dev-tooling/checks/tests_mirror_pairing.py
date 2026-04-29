"""tests_mirror_pairing — every covered `.py` has a paired test (v033 D1).

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-tests-mirror-pairing` row, added at
v033) and PROPOSAL.md §"Test pyramid" (post-v033), every covered
`.py` file under `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/
checks/**` MUST have a paired test file at the mirror path under
`tests/` containing at least one `def test_*` function (subsequent
cycles tighten the existence-only check to also verify
`def test_*` content). The 1:1 mirror rule was author-discipline-
only pre-v033; this script promotes it to a hard mechanical gate
at the v033-codification commit boundary.

Closed exemption set (per v033 D1): `_vendor/**` (vendored libs),
`bin/_bootstrap.py` (covered by the preserved `tests/bin/
test_bootstrap.py`), and `__init__.py` files containing only
`from __future__ import annotations` plus `__all__: list[str] =
[]` with no executable logic. Subsequent cycles wire up the
exemption matchers; cycle 1 implements the core walk + missing-
pair detection on a non-exempt source path
(`.claude-plugin/scripts/livespec/foo/bar.py`).

Output discipline: per spec lines 1738-1762, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

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


def _expected_paired_test_path(
    *, source_path: Path, source_tree: Path, tests_tree: Path
) -> Path:
    rel = source_path.relative_to(source_tree)
    parent = rel.parent
    name = rel.name
    test_name = f"test_{name[1:]}" if name.startswith("_") else f"test_{name}"
    return tests_tree / parent / test_name


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
            expected_pair = _expected_paired_test_path(
                source_path=py_file, source_tree=source_tree, tests_tree=tests_tree
            )
            if not expected_pair.is_file():
                offenders.append(
                    (py_file.relative_to(cwd), expected_pair.relative_to(cwd))
                )
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
