"""Tests for livespec.commands._doctor_lifecycle.

The shared pre-step / post-step doctor-static lifecycle used by the
propose-change, critique, and revise wrappers, per
`SPECIFICATION/contracts.md` (pre-step skip control) and `SPECIFICATION/spec.md` (sub-command lifecycle).
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest
from livespec.commands import _doctor_lifecycle
from livespec.errors import LivespecError, PreconditionError
from livespec.io import proc
from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _namespace(*, skip: bool = False, run: bool = False) -> argparse.Namespace:
    return argparse.Namespace(skip_pre_check=skip, run_pre_check=run)


def _resolve(*, tmp_path: Path, namespace: argparse.Namespace) -> bool:
    result = unsafe_perform_io(
        _doctor_lifecycle.resolve_pre_step_skip(namespace=namespace, project_root=tmp_path),
    )
    assert isinstance(result, Success)
    return bool(result.unwrap())


def test_add_pre_check_flags_rejects_both_flags_together() -> None:
    """The registered pair is mutually exclusive at the argparse layer."""
    parser = argparse.ArgumentParser(prog="demo", exit_on_error=False)
    _doctor_lifecycle.add_pre_check_flags(parser=parser)
    with pytest.raises(argparse.ArgumentError):
        _ = parser.parse_args(["--skip-pre-check", "--run-pre-check"])
    namespace = parser.parse_args([])
    assert (namespace.skip_pre_check, namespace.run_pre_check) == (False, False)


@pytest.mark.parametrize(
    ("config_text", "expected"),
    [
        (None, False),
        ('{"pre_step_skip_static_checks": true}', True),
        ('{"pre_step_skip_static_checks": false}', False),
        ("{}", False),
        ('{"pre_step_skip_static_checks": "yes"}', False),
        ("[true]", False),
        ("{not json", False),
    ],
)
def test_resolve_pre_step_skip_reads_config_when_neither_flag(
    *,
    tmp_path: Path,
    config_text: str | None,
    expected: bool,
) -> None:
    """Neither flag: the config key decides; absent, malformed or non-bool means run."""
    if config_text is not None:
        _ = (tmp_path / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    assert _resolve(tmp_path=tmp_path, namespace=_namespace()) is expected


def test_resolve_pre_step_skip_flags_override_config(*, tmp_path: Path) -> None:
    """The skip flag forces skip; the run flag forces run over a config of true."""
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": true}',
        encoding="utf-8",
    )
    assert _resolve(tmp_path=tmp_path, namespace=_namespace(skip=True)) is True
    assert _resolve(tmp_path=tmp_path, namespace=_namespace(run=True)) is False


def _stub_doctor(
    *,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
) -> list[list[str]]:
    calls: list[list[str]] = []

    def _run(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], LivespecError]:
        del cwd
        calls.append(argv)
        return IOResult.from_value(
            subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr=""),
        )

    monkeypatch.setattr(proc, "run_subprocess", _run)
    return calls


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        ("not json", "post-step doctor stdout malformed JSON"),
        ('{"other": []}', "post-step doctor stdout missing 'findings' key"),
        ("[]", "post-step doctor stdout missing 'findings' key"),
        ('{"findings": {}}', "post-step doctor 'findings' is not a list"),
        (
            '{"findings": [{"status": "fail"}, {"status": "pass"}, "x"]}',
            "post-step doctor reported 1 fail-status finding(s)",
        ),
    ],
)
def test_run_post_step_doctor_folds_bad_documents_to_precondition_error(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    message: str,
) -> None:
    """Malformed doctor output and fail findings fold to PreconditionError (exit 3)."""
    _ = _stub_doctor(monkeypatch=monkeypatch, stdout=stdout)
    result = unsafe_perform_io(
        _doctor_lifecycle.run_post_step_doctor(project_root=tmp_path, value="v"),
    )
    assert isinstance(result, Failure)
    error = result.failure()
    assert isinstance(error, PreconditionError)
    assert str(error).startswith(message)


def test_run_post_step_doctor_threads_value_and_targets_project_root(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A passing doctor threads the value through; the run targets the project root."""
    calls = _stub_doctor(monkeypatch=monkeypatch, stdout='{"findings": []}')
    result = unsafe_perform_io(
        _doctor_lifecycle.run_post_step_doctor(project_root=tmp_path, value="v"),
    )
    assert result == Success("v")
    assert calls[0][1].endswith("doctor_static.py")
    assert calls[0][-2:] == ["--project-root", str(tmp_path)]


def test_run_pre_step_skips_doctor_and_emits_finding_when_skip(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Resolved skip: the canonical finding is emitted and no doctor runs."""
    calls = _stub_doctor(monkeypatch=monkeypatch, stdout='{"findings": []}')
    result = unsafe_perform_io(
        _doctor_lifecycle.run_pre_step(namespace=_namespace(skip=True), project_root=tmp_path),
    )
    assert isinstance(result, Success)
    assert calls == []
    assert capsys.readouterr().out == (
        '{"findings": [{"check_id": "pre-step-skipped", "status": "skipped", '
        '"message": "pre-step checks skipped by user config or --skip-pre-check"}]}\n'
    )


def test_run_pre_step_runs_doctor_when_not_skipped(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolved run: the pre-step doctor runs and a fail finding folds to failure."""
    calls = _stub_doctor(
        monkeypatch=monkeypatch,
        stdout='{"findings": [{"status": "fail"}]}',
    )
    result = unsafe_perform_io(
        _doctor_lifecycle.run_pre_step(namespace=_namespace(run=True), project_root=tmp_path),
    )
    assert isinstance(result, Failure)
    assert str(result.failure()).startswith("pre-step doctor reported 1")
    assert len(calls) == 1
