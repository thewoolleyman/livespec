"""E2E retry-on-exit-4 test: schema-invalid payload triggers exit 4, retry succeeds.

Per SPECIFICATION/contracts.md §"E2E harness contract §"Error paths": the
mock generates a schema-invalid propose-change payload on first call (exit 4),
then a valid payload on second call (exit 0). Mock-only; real tier skips.
"""

from __future__ import annotations

from pathlib import Path

import fake_claude
import pytest

__all__: list[str] = []


@pytest.mark.mock_only
def test_retry_on_exit_4(*, tmp_path: Path) -> None:
    """Schema-invalid payload exits 4; retry with valid payload exits 0."""
    import subprocess

    def _git(args: list[str]) -> None:
        subprocess.run(
            ["git", *args],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )

    _git(["init"])
    _git(["config", "user.email", "e2e-test@example.com"])
    _git(["config", "user.name", "E2E Test"])

    seed_result = fake_claude.seed(project_root=tmp_path, intent="Retry-on-exit-4 test project")
    assert seed_result.returncode == 0, f"seed failed: {seed_result.stderr!r}"
    _git(["add", "-A"])
    _git(["commit", "-m", "seed"])

    invalid_result = fake_claude.propose_change_invalid(
        project_root=tmp_path,
        topic="retry-test-invalid",
    )
    assert invalid_result.returncode == 4, (
        f"expected exit 4 for schema-invalid payload, got {invalid_result.returncode}; "
        f"stderr={invalid_result.stderr!r}"
    )

    valid_result = fake_claude.propose_change(
        project_root=tmp_path,
        intent="Add a constraint that retries MUST succeed on valid payloads",
        topic="retry-test-valid",
    )
    assert valid_result.returncode == 0, f"retry with valid payload failed: {valid_result.stderr!r}"
    assert (tmp_path / "SPECIFICATION" / "proposed_changes" / "retry-test-valid.md").is_file()
