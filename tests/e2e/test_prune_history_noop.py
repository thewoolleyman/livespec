"""E2E prune-history no-op test.

Per SPECIFICATION/contracts.md §"E2E harness contract §"Error paths": a
project with only v001 history triggers the prune-history no-op short-circuit
(exit 0, prune-history-no-op skipped Finding).
"""

from __future__ import annotations

import json
import subprocess  # documented integration-test usage
from pathlib import Path

import fake_claude

__all__: list[str] = []


def _git(*, cwd: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
    )


def test_prune_history_noop(*, tmp_path: Path) -> None:
    """v001-only history → prune-history emits skipped Finding and exits 0."""
    _git(cwd=tmp_path, args=["init"])
    _git(cwd=tmp_path, args=["config", "user.email", "e2e-test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "E2E Test"])

    seed_result = fake_claude.seed(project_root=tmp_path, intent="Prune-history no-op test project")
    assert seed_result.returncode == 0, f"seed failed: {seed_result.stderr!r}"
    _git(cwd=tmp_path, args=["add", "-A"])
    _git(cwd=tmp_path, args=["commit", "-m", "seed"])

    prune_result = fake_claude.prune_history(project_root=tmp_path)
    assert prune_result.returncode == 0, (
        f"prune-history exited {prune_result.returncode}; " f"stderr={prune_result.stderr!r}"
    )

    all_findings: list[dict[str, object]] = []
    for raw_line in prune_result.stdout.splitlines():
        stripped = raw_line.strip()
        if stripped:
            doc = json.loads(stripped)
            all_findings.extend(doc.get("findings", []))
    skipped_ids = [str(f["check_id"]) for f in all_findings if f["status"] == "skipped"]
    assert (
        "prune-history-no-op" in skipped_ids
    ), f"expected prune-history-no-op skipped finding; all_findings={all_findings!r}"
