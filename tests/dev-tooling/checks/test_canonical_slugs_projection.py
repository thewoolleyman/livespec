"""Outside-in test for `dev-tooling/checks/canonical_slugs_projection.py`.

The canonical-slugs projection check is the anti-drift gate for the
release-time projection of `livespec_dev_tooling.canonical_checks`
into the committed copier-template data file
`templates/impl-plugin/canonical-slugs.yml`, per
livespec/SPECIFICATION/contracts.md §"Shared code sync —
livespec-dev-tooling" → Template gate.

Two modes are exercised:

- **Verify mode (default).** Exit 0 when the committed
  `canonical-slugs.yml` matches `canonical_check_slugs()` in set and
  order; exit non-zero with the drift diagnostic otherwise (missing
  file, missing slugs, extra slugs, or out-of-order).
- **Write mode (`--write`).** Regenerate the committed file from the
  source of truth; exit 0. After a write, verify mode passes.

Pass case: invoke the script with cwd=<livespec-core repo root>;
expect exit 0 and the structured success diagnostic, because the
committed projection is kept in lockstep with the source of truth.

Fail cases use a synthetic repo-shape fixture under tmp_path with a
hand-rolled `canonical-slugs.yml` so the drift branches fire
hermetically.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROJECTION = _REPO_ROOT / "dev-tooling" / "checks" / "canonical_slugs_projection.py"
_YAML_REL = Path("templates") / "impl-plugin" / "canonical-slugs.yml"


def _load_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "canonical_slugs_projection_under_test", str(_PROJECTION)
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_slugs() -> tuple[str, ...]:
    from livespec_dev_tooling.canonical_checks import canonical_check_slugs

    return canonical_check_slugs()


def test_verify_passes_against_real_committed_projection() -> None:
    """Pass case: the committed canonical-slugs.yml matches the source of truth."""
    result = subprocess.run(
        [sys.executable, str(_PROJECTION)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"verify should exit 0 against the real committed projection; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "canonical-slugs-projection-ok" in result.stderr, (
        f"expected success diagnostic 'canonical-slugs-projection-ok' in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_verify_fails_when_committed_file_missing(*, tmp_path: Path) -> None:
    """Fail case: no committed canonical-slugs.yml under cwd; emit missing-file diagnostic."""
    result = subprocess.run(
        [sys.executable, str(_PROJECTION)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"verify should reject when canonical-slugs.yml is absent; "
        f"got returncode={result.returncode}"
    )
    assert "canonical-slugs-projection-missing-file" in result.stderr, (
        f"expected 'canonical-slugs-projection-missing-file' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_verify_fails_on_drift(*, tmp_path: Path) -> None:
    """Fail case: committed file carries a stale slug set; emit drift diagnostic."""
    _ = pytest.importorskip("livespec_dev_tooling.canonical_checks")
    yaml_path = tmp_path / _YAML_REL
    yaml_path.parent.mkdir(parents=True)
    yaml_path.write_text("- check-stale-slug\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_PROJECTION)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"verify should reject a stale committed projection; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "canonical-slugs-projection-drift" in result.stderr, (
        f"expected 'canonical-slugs-projection-drift' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_write_mode_then_verify_passes(*, tmp_path: Path) -> None:
    """Write mode regenerates the committed file from source of truth; verify then passes."""
    _ = pytest.importorskip("livespec_dev_tooling.canonical_checks")
    yaml_path = tmp_path / _YAML_REL
    yaml_path.parent.mkdir(parents=True)
    # Start with a stale file so we prove --write overwrites it.
    yaml_path.write_text("- check-stale-slug\n", encoding="utf-8")

    write_result = subprocess.run(
        [sys.executable, str(_PROJECTION), "--write"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert write_result.returncode == 0, (
        f"--write should exit 0; got returncode={write_result.returncode} "
        f"stderr={write_result.stderr!r}"
    )
    assert "canonical-slugs-projection-written" in write_result.stderr, (
        f"expected 'canonical-slugs-projection-written' check_id in stderr; "
        f"got stderr={write_result.stderr!r}"
    )

    verify_result = subprocess.run(
        [sys.executable, str(_PROJECTION)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify_result.returncode == 0, (
        f"verify after --write should exit 0; got returncode={verify_result.returncode} "
        f"stderr={verify_result.stderr!r}"
    )


def test_written_file_parses_back_to_canonical_set(*, tmp_path: Path) -> None:
    """The file `--write` emits round-trips through the module's own parser to the source of truth."""
    _ = pytest.importorskip("livespec_dev_tooling.canonical_checks")
    module = _load_module()
    expected = _canonical_slugs()
    rendered = module._render_yaml(slugs=expected)  # noqa: SLF001
    yaml_path = tmp_path / "canonical-slugs.yml"
    yaml_path.write_text(rendered, encoding="utf-8")
    parsed = module._parse_committed_slugs(yaml_path=yaml_path)  # noqa: SLF001
    assert parsed == expected, (
        f"rendered projection must round-trip back to the canonical set; "
        f"got {parsed!r} != expected {expected!r}"
    )


def test_committed_yaml_matches_source_of_truth() -> None:
    """The real committed canonical-slugs.yml equals canonical_check_slugs() (defense-in-depth)."""
    _ = pytest.importorskip("livespec_dev_tooling.canonical_checks")
    module = _load_module()
    committed = module._parse_committed_slugs(yaml_path=_REPO_ROOT / _YAML_REL)  # noqa: SLF001
    assert committed == _canonical_slugs(), (
        "the committed templates/impl-plugin/canonical-slugs.yml has drifted from "
        "livespec_dev_tooling.canonical_checks; run `just stamp-canonical-slugs`"
    )
