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


def test_check_default_block_rejects_unterminated_block(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """An unterminated commented block is a typed usage failure, never a traceback.

    livespec-runtime v0.22.0 raises `UnterminatedGovernanceBlockError`
    where it previously returned a silent `None`. The source path is
    operator-supplied, so the supervisor must route that onto the
    failure track and emit the usual exit-2 usage error.
    """
    source_path = tmp_path / "unterminated.jsonc"
    _ = source_path.write_text(
        (
            "// Optional — spec_governance: policy\n"
            "not a comment\n"
            "// Optional — credential_wrapper: next\n"
        ),
        encoding="utf-8",
    )

    exit_code = spec_governance.main(argv=["--check-default-block", str(source_path)])

    assert exit_code == 2
    assert "spec-governance-default-block-unterminated" in capsys.readouterr().err
