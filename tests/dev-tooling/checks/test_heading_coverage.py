"""Outside-in test for `dev-tooling/checks/heading_coverage.py`.

Per `python-skill-script-style-requirements.md` line 2095:

    Validates that every `##` heading in every spec tree —
    main + each sub-spec under `SPECIFICATION/templates/<name>/`
    — has a corresponding entry in
    `tests/heading-coverage.json` whose `spec_root` field
    matches the heading's tree. Tolerates an empty `[]` array
    pre-Phase-6, before any spec tree exists; from Phase 6
    onward emptiness is a failure if any spec tree exists.

Cycle 54 pins the canonical violation: a `##` heading present
in a spec file with no matching entry in the registry.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_HEADING_COVERAGE = _REPO_ROOT / "dev-tooling" / "checks" / "heading_coverage.py"


def test_heading_coverage_rejects_uncovered_heading(*, tmp_path: Path) -> None:
    """A `##` heading with no matching registry entry is rejected.

    Fixture: `SPECIFICATION/spec.md` carries `## Foo rule`;
    `tests/heading-coverage.json` is `[]`. The check must walk
    the spec tree, observe the uncovered heading, exit non-zero,
    and surface the heading text.
    """
    spec_dir = tmp_path / "SPECIFICATION"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(
        "# Title\n\n## Foo rule\n\nProse here.\n",
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "heading-coverage.json").write_text("[]\n", encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"heading_coverage should reject uncovered `## Foo rule`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "Foo rule" in combined, (
        f"heading_coverage diagnostic does not surface heading 'Foo rule'; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_heading_coverage_accepts_empty_registry_when_no_spec_tree(
    *,
    tmp_path: Path,
) -> None:
    """Empty registry + no spec tree is accepted (pre-Phase-6 baseline).

    Fixture: `tests/heading-coverage.json` is `[]`; no
    `SPECIFICATION/` directory. The check must walk and exit 0.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "heading-coverage.json").write_text("[]\n", encoding="utf-8")
    # Note: no SPECIFICATION/ directory.

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_HEADING_COVERAGE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"heading_coverage should accept empty registry pre-Phase-6 (no spec tree); "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
