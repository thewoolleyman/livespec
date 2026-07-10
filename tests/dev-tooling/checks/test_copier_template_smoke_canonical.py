"""Tests for `dev-tooling/checks/copier_template_smoke_canonical.py`."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECKS_DIR = _REPO_ROOT / "dev-tooling" / "checks"
if str(_CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(_CHECKS_DIR))

import copier_template_smoke_canonical as canonical  # noqa: E402
from copier_template_smoke_canonical import (  # noqa: E402
    _extract_stamped_targets,
    _verify_canonical_slug_stamping,
)


class _RecordingLog:
    def __init__(self) -> None:
        self.errors: list[dict[str, Any]] = []

    def error(self, event: str, **kwargs: Any) -> None:
        self.errors.append({"event": event, **kwargs})


def test_extract_stamped_targets_preserves_check_slug_order() -> None:
    justfile_text = """
check:
    targets=(
        check-alpha
        not-a-check
        check-beta
    )
"""

    assert _extract_stamped_targets(justfile_text=justfile_text) == (
        "check-alpha",
        "check-beta",
    )


def _expected_slugs(*, repo_root: Path) -> tuple[str, str]:
    _ = repo_root
    return ("check-alpha", "check-beta")


def test_verify_canonical_slug_stamping_reports_drift(
    *, tmp_path: Path, monkeypatch: object
) -> None:
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setattr(
        canonical,
        "_expected_canonical_slugs",
        _expected_slugs,
    )
    (tmp_path / "justfile").write_text(
        """
check:
    targets=(
        check-alpha
    )
""",
        encoding="utf-8",
    )
    log = _RecordingLog()

    assert (
        _verify_canonical_slug_stamping(
            log=log,
            target=tmp_path,
            repo_root=_REPO_ROOT,
        )
        is None
    )
    assert log.errors[0]["check_id"] == "copier-template-smoke-canonical-slug-drift"
    assert log.errors[0]["missing"] == ["check-beta"]
