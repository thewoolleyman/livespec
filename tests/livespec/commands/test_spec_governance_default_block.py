"""Additional command-supervisor tests for spec-governance default-block checks."""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.commands import spec_governance

__all__: list[str] = []


def test_check_default_block_rejects_missing_source(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=["--check-default-block", str(tmp_path / "missing.jsonc")],
    )

    assert exit_code == 2
    assert "spec-governance-default-block-missing-source" in capsys.readouterr().err
