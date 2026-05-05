"""Tests for livespec.commands.prune_history.

Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle" prune-history
paragraph: the wrapper resolves the spec root from `--project-root`,
enumerates `<spec-root>/history/`, and short-circuits with a
`prune-history-no-op` skipped JSON finding when the no-op
preconditions are met.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.commands import prune_history

__all__: list[str] = []


def _make_v001_only_spec_root(*, tmp_path: Path) -> Path:
    """Set up `<tmp_path>/SPECIFICATION/history/v001/` and return tmp_path."""
    (tmp_path / "SPECIFICATION" / "history" / "v001").mkdir(parents=True)
    return tmp_path


def test_prune_history_main_exists_and_returns_int(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/prune_history.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Uses `monkeypatch.chdir(tmp_path)` to
    isolate the cwd-fallback `_resolve_spec_root` branch from the
    real repo's `SPECIFICATION/`; without isolation this test would
    leak into the developer's working tree.
    """
    _ = _make_v001_only_spec_root(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = prune_history.main(argv=[])
    assert isinstance(exit_code, int)


def test_prune_history_main_returns_zero_on_valid_argv(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """prune-history with no flags + only v001 in history returns exit code 0.

    Per v012 spec.md no-op short-circuit (i): only-v001 case
    emits the skipped finding and exits 0. Drives the cwd-fallback
    `_resolve_spec_root` branch + the no-op path.
    """
    _ = _make_v001_only_spec_root(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = prune_history.main(argv=[])
    assert exit_code == 0


def test_prune_history_main_returns_usage_exit_code_on_unknown_flag() -> None:
    """Unknown CLI flag returns exit code 2.

    Drives the parse_argv stage on the railway: an unknown flag
    surfaces as an argparse SystemExit, which io/cli's
    @impure_safe maps to UsageError and the supervisor's
    pattern-match lifts to exit 2 via err.exit_code. The
    UsageError fires before the body runs, so no spec-root
    setup is needed.
    """
    exit_code = prune_history.main(argv=["--no-such-flag"])
    assert exit_code == 2


def test_prune_history_main_accepts_skip_pre_check_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--skip-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--skip-pre-check` as one half of the mutually-exclusive
    flag pair codified in v012 spec.md §"Pre-step skip control".
    The body widening at cycle 6.c.3 means the wrapper now requires
    a valid `<spec-root>/history/` to short-circuit on; this test
    sets up a v001-only history and drives the no-op path.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--skip-pre-check", "--project-root", str(project_root)],
    )
    assert exit_code == 0


def test_prune_history_main_accepts_run_pre_check_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--run-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--run-pre-check` as the override-config half of the
    mutually-exclusive flag pair codified in v012 spec.md
    §"Pre-step skip control".
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    assert exit_code == 0


def test_prune_history_main_rejects_both_skip_and_run_pre_check_flags_together() -> None:
    """Passing both `--skip-pre-check` AND `--run-pre-check` exits 2.

    Per v012 spec.md §"Pre-step skip control" rule (4): both flags
    set together MUST result in argparse mutually-exclusive usage
    error, lifting to exit 2 via `IOFailure(UsageError)`. Drives
    the `add_mutually_exclusive_group` enforcement. The
    UsageError fires before the body runs, so no spec-root setup
    is needed.
    """
    exit_code = prune_history.main(argv=["--skip-pre-check", "--run-pre-check"])
    assert exit_code == 2


def test_prune_history_main_emits_no_op_finding_when_only_v001_exists(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md no-op short-circuit (i): only v001 exists.

    When `<spec-root>/history/` contains only `v001`, the wrapper
    emits a single-finding `{"findings": [{"check_id": "prune-
    history-no-op", "status": "skipped", "message": "..."}]}` JSON
    document to stdout and exits 0; the existing tree is NOT
    re-written, no commit-worthy diff is produced. Drives spec-
    root resolution from `--project-root`, history enumeration,
    max-version detection, and the JSON finding emission.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert payload["findings"][0]["status"] == "skipped"


def test_prune_history_main_accepts_project_root_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--project-root <path>` is a recognized optional flag (exit 0).

    Per v012 contracts.md §"Wrapper CLI surface" prune-history row
    + the universal `--project-root <path>` baseline (PROPOSAL.md
    §"Project-root detection contract" explicitly enumerates
    `bin/prune_history.py` as a project-state wrapper that accepts
    the flag).
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    assert exit_code == 0


def test_prune_history_main_does_not_emit_no_op_finding_when_history_has_multiple_versions(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When history has multiple v* dirs, the only-v001 short-circuit does NOT fire.

    Drives the `if max_version == 1:` guard's "guard not taken"
    branch in `_maybe_no_op`. The fixture sets up v001 and v002,
    so max_version = 2; the no-op finding MUST NOT be emitted to
    stdout. Subsequent cycles widen the wrapper to either fire
    the second no-op short-circuit (oldest is already
    PRUNED_HISTORY.json) or perform the actual prune.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v002").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""


def test_prune_history_find_max_version_skips_non_directory_entries(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips non-directory children defensively.

    Drives the `if not child.is_dir(): continue` guard branch.
    The fixture mixes a regular file (skipped) with a v001 dir
    (counted). Mirrors the
    `test_revise_format_next_version_name_skips_non_directory_entries`
    precedent.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001


def test_prune_history_find_max_version_skips_non_v_prefix_dirs(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips directory children whose name doesn't start with `v`.

    Drives the `if not name.startswith("v"): continue` guard
    branch. The fixture mixes a non-v-prefixed dir with a v001
    dir (counted). Mirrors the analogous revise-side test.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "scratch").mkdir()
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001


def test_prune_history_find_max_version_skips_v_prefix_with_non_digit_suffix(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips `v<non-digits>` directory children.

    Drives the `if not suffix.isdigit(): continue` guard branch.
    The fixture mixes a `vextra` dir (skipped) with a v001 dir
    (counted). Mirrors the analogous revise-side test.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "vextra").mkdir()
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001
