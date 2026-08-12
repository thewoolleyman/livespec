"""Tests for the spec pull-request merge-policy gate supervisor.

The gate replaces ~250 lines of embedded workflow bash whose defects were only
ever observable on a CI runner. Each case therefore names the production
failure it pins down rather than merely asserting a return value.

`gather` is monkeypatched so the git and hosting-API observations are supplied
directly; everything downstream of it — the derivation, the fold over real
`.livespec.jsonc` and history files, the journal append, and the step-output
write — runs for real against `tmp_path`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.commands import spec_pr_merge_policy
from livespec.commands._spec_pr_merge_gather import Observations
from livespec.errors import LivespecError, PreconditionError
from livespec.spec_governance.pr_merge_derivation import ApiFile
from returns.io import IOResult
from returns.result import Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

_STEM = "some-topic"
_HISTORY_PATH = f"SPECIFICATION/history/v202/proposed_changes/{_STEM}.md"
_REPO = "thewoolleyman/livespec"
_PULL_REQUEST = 2200


def _install_observations(
    *,
    monkeypatch: pytest.MonkeyPatch,
    observations: Observations,
) -> None:
    """Replace the gather seam with one that yields canned observations."""

    def fake_gather(**_kwargs: object) -> IOResult[Observations, LivespecError]:
        return IOResult.from_value(observations)

    monkeypatch.setattr(spec_pr_merge_policy, "gather", fake_gather)


def _install_gather_failure(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the gather seam with one that fails the way a broken runner does."""

    def fake_gather(**_kwargs: object) -> IOResult[Observations, LivespecError]:
        return IOResult.from_failure(PreconditionError("git.merge_base: exited 128"))

    monkeypatch.setattr(spec_pr_merge_policy, "gather", fake_gather)


def _ratifying_observations() -> Observations:
    """The production shape: a move, seen as an add locally and a rename via API."""
    return Observations(
        touched_spec_root=True,
        total_changed_files=9,
        local_paths=(_HISTORY_PATH,),
        api_files=(ApiFile(filename=_HISTORY_PATH, status="renamed"),),
    )


def _write_project(*, root: Path, global_policy: str, front_matter: str = "") -> None:
    """Lay down a governed project: a config block plus one ratified proposal."""
    _ = (root / ".livespec.jsonc").write_text(
        json.dumps({"spec_governance": {"spec_pr_merge": global_policy}}),
        encoding="utf-8",
    )
    proposal_dir = root / "SPECIFICATION" / "history" / "v202" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    _ = (proposal_dir / f"{_STEM}.md").write_text(
        f"---\ntopic: {_STEM}\n{front_matter}---\n\n## Proposal\n\nBody.\n",
        encoding="utf-8",
    )


def _decide(*, project_root: Path) -> spec_pr_merge_policy.Decision:
    """Run the gate and unwrap its decision, failing the test on the error track."""
    unwrapped = unsafe_perform_io(
        spec_pr_merge_policy.decide(
            project_root=project_root,
            repo=_REPO,
            pull_request_number=_PULL_REQUEST,
            base_sha="base",
            head_sha="head",
        ),
    )
    match unwrapped:
        case Success(decision):
            return decision
        case _:
            raise AssertionError(f"expected a decision, got {unwrapped!r}")


def test_ratifying_pull_request_under_auto_on_green_registers(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A move-shaped ratification folds to auto-on-green and journals the event."""
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "auto"
    assert decision.stems == (_STEM,)
    assert decision.effective_policy == "auto-on-green"
    journal = tmp_path / "tmp" / "livespec-spec-governance-journal.jsonl"
    event = json.loads(journal.read_text(encoding="utf-8").splitlines()[0])
    assert event["event_type"] == "spec_pr_merge"
    assert event["pull_request_identity"] == f"{_REPO}#{_PULL_REQUEST}"
    assert event["proposal_stems"] == [_STEM]


def test_manual_floored_proposal_is_left_for_human_merge(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A proposal-level `manual` override blocks even under a global auto-on-green."""
    _write_project(
        root=tmp_path,
        global_policy="auto-on-green",
        front_matter="spec_pr_merge_policy: manual\n",
    )
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert decision.effective_policy == "manual"


def test_blocked_fold_writes_no_journal_event(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The journal records registrations; a blocked gate registered nothing."""
    _write_project(root=tmp_path, global_policy="manual")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert not (tmp_path / "tmp" / "livespec-spec-governance-journal.jsonl").exists()


def test_missing_config_file_falls_back_to_the_safe_default(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """No `.livespec.jsonc` means the safe `manual` default, never a crash."""
    proposal_dir = tmp_path / "SPECIFICATION" / "history" / "v202" / "proposed_changes"
    proposal_dir.mkdir(parents=True)
    _ = (proposal_dir / f"{_STEM}.md").write_text(
        f"---\ntopic: {_STEM}\n---\n\nBody.\n",
        encoding="utf-8",
    )
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert decision.effective_policy == "manual"


def test_untouched_spec_root_falls_through_to_auto(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A non-spec pull request keeps today's behaviour exactly."""
    _install_observations(
        monkeypatch=monkeypatch,
        observations=Observations(
            touched_spec_root=False,
            total_changed_files=0,
            local_paths=(),
            api_files=(),
        ),
    )

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "auto"
    assert decision.stems == ()


def test_entirely_empty_diff_blocks_without_consulting_the_policy(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Zero changed files IN TOTAL is impossible for a real pull request.

    The gate must block on the derivation itself, before any fold — reading a
    policy off a diff computation known to be broken would dress the failure up
    as a governed answer.
    """
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(
        monkeypatch=monkeypatch,
        observations=Observations(
            touched_spec_root=True,
            total_changed_files=0,
            local_paths=(),
            api_files=(),
        ),
    )

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert decision.effective_policy is None


def test_observation_failure_resolves_blocked_rather_than_crashing(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A git or hosting-API error is derivation FAILURE — a decision, not a crash.

    Conflating it with a KNOWN-EMPTY is what would auto-merge on a broken diff.
    """
    _install_gather_failure(monkeypatch=monkeypatch)

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert "derivation FAILURE" in decision.reason


def test_journal_append_failure_prevents_registration(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Journal-as-gate: an append that cannot happen blocks the registration."""
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())
    monkeypatch.setattr(
        spec_pr_merge_policy,
        "append_journal_payload",
        lambda **_kwargs: "journal append failed: read-only file system",
    )

    decision = _decide(project_root=tmp_path)

    assert decision.decision == "blocked"
    assert "PREVENTS registration" in decision.reason


def test_main_writes_the_step_output_and_narrates_on_stdout(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both diagnostic legs exist: the step's own output and the output parameter."""
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())
    github_output = tmp_path / "step-output.txt"

    exit_code = spec_pr_merge_policy.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--repo",
            _REPO,
            "--pull-request",
            str(_PULL_REQUEST),
            "--base-sha",
            "base",
            "--head-sha",
            "head",
            "--github-output",
            str(github_output),
        ],
    )

    assert exit_code == 0
    assert github_output.read_text(encoding="utf-8") == "decision=auto\n"
    narration = json.loads(capsys.readouterr().out.strip())
    assert narration["decision"] == "auto"
    assert narration["proposal_stems"] == [_STEM]


def test_main_appends_rather_than_overwriting_the_step_output(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An earlier step's output parameter survives this step's write."""
    _write_project(root=tmp_path, global_policy="manual")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())
    github_output = tmp_path / "step-output.txt"
    _ = github_output.write_text("earlier=kept\n", encoding="utf-8")

    exit_code = spec_pr_merge_policy.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--repo",
            _REPO,
            "--pull-request",
            str(_PULL_REQUEST),
            "--base-sha",
            "base",
            "--head-sha",
            "head",
            "--github-output",
            str(github_output),
        ],
    )

    assert exit_code == 0
    assert github_output.read_text(encoding="utf-8") == "earlier=kept\ndecision=blocked\n"


def test_main_defaults_the_project_root_to_the_working_directory(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Omitting `--project-root` reads the consumer checkout the runner is in."""
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())
    monkeypatch.chdir(tmp_path)

    exit_code = spec_pr_merge_policy.main(
        argv=[
            "--repo",
            _REPO,
            "--pull-request",
            str(_PULL_REQUEST),
            "--base-sha",
            "base",
            "--head-sha",
            "head",
        ],
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out.strip())["decision"] == "auto"


def test_main_reports_a_usage_error_for_a_missing_required_flag(
    *,
    tmp_path: Path,
) -> None:
    """A malformed invocation fails the STEP, which is the fail-closed direction."""
    exit_code = spec_pr_merge_policy.main(argv=["--project-root", str(tmp_path)])

    assert exit_code != 0


def test_step_output_write_failure_fails_the_step(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A decision that cannot be published must fail the step, loudly.

    Returning 0 here would leave the output parameter unset, and the caller
    reads an unset parameter as `not blocked` — the one shape that turns an
    undeliverable decision into an auto-merge.
    """
    _write_project(root=tmp_path, global_policy="auto-on-green")
    _install_observations(monkeypatch=monkeypatch, observations=_ratifying_observations())
    monkeypatch.setattr(
        spec_pr_merge_policy.fs,
        "append_text",
        lambda **_kwargs: IOResult.from_failure(PreconditionError("fs.append_text: EACCES")),
    )

    exit_code = spec_pr_merge_policy.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--repo",
            _REPO,
            "--pull-request",
            str(_PULL_REQUEST),
            "--base-sha",
            "base",
            "--head-sha",
            "head",
            "--github-output",
            str(tmp_path / "out.txt"),
        ],
    )

    assert exit_code != 0
