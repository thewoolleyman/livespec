"""Tests for livespec.commands.spec_governance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
from livespec.commands import spec_governance
from livespec.errors import UsageError
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_show_effective_emits_manifest_declared_effective_and_diagnostics(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance": {"propose_change_mode": "batch"}}',
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=["--project-root", str(tmp_path), "--show-effective"],
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert len(payload["manifest"]) == 7
    assert payload["declared"] == {"propose_change_mode": "batch"}
    assert payload["effective"]["propose_change_mode"] == "batch"
    assert payload["effective"]["revise_decision_mode"] == "manual"


def test_show_effective_defaults_project_root_to_cwd(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = spec_governance.main(argv=["--show-effective"])

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["effective"]["propose_change_mode"] == "interactive"


def test_action_updates_config_and_emits_changed_path(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:global:delegated",
        ],
    )

    assert exit_code == 0
    payload: dict[str, str] = json.loads(capsys.readouterr().out)
    assert payload["changed_path"] == ".livespec.jsonc"
    assert '"revise_decision_mode": "delegated"' in (tmp_path / ".livespec.jsonc").read_text(
        encoding="utf-8"
    )


def test_invalid_action_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:global:robot",
        ],
    )

    assert exit_code == 2
    assert "revise decision mode" in capsys.readouterr().err


def test_invalid_revise_decision_action_shape_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--action",
            "set-revise-decision-mode:project:manual",
        ],
    )

    assert exit_code == 2
    assert "requires global" in capsys.readouterr().err


def test_journal_event_appends_and_emits_digest(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_type": "authoring_auto_consumption",
                "operation": "critique",
                "governing_key": "critique_mode",
                "effective_source": "global",
                "input_envelope_digest": "d" * 64,
                "outcome": "consumed",
            },
        ),
        encoding="utf-8",
    )

    exit_code = spec_governance.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--journal-event-json",
            str(event_path),
        ],
    )

    assert exit_code == 0
    payload: dict[str, str] = json.loads(capsys.readouterr().out)
    assert payload["journal_path"] == "tmp/livespec-spec-governance-journal.jsonl"
    assert len(payload["event_digest"]) == 64


def test_invalid_journal_event_exits_usage_error(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text("[]", encoding="utf-8")

    exit_code = spec_governance.main(
        argv=["--project-root", str(tmp_path), "--journal-event-json", str(event_path)],
    )

    assert exit_code == 2
    assert "JSON object" in capsys.readouterr().err


def test_dispatch_rejects_namespace_without_operation() -> None:
    result = unsafe_perform_io(
        spec_governance.dispatch(
            namespace=argparse.Namespace(
                project_root=None,
                show_effective=False,
                action=None,
                journal_event_json=None,
            ),
        ),
    )

    assert isinstance(result.failure(), UsageError)
