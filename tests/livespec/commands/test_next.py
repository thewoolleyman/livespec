"""Tests for livespec.commands.next.

Per `SPECIFICATION/contracts.md` §"`/livespec-core:next`
spec-side thin-transport skill" + §"Wrapper CLI surface": the
`next` sub-command reads spec-side state (Proposed Changes
queue + Specification History) and emits JSON on stdout with
fields `action` (one of `revise` / `propose-change` /
`critique` / `prune-history` / `none`), `reason`, `urgency`
(one of `high` / `medium` / `low`). Pure function of file
state; no LLM in the ranking path.

Doctor-cache integration is deferred per the Phase B.1 scope
question (`research/workflow-processes/multi-repo-split-execution-plan.md`
§Phase B sub-tasks). The MVP ranking covers Proposed Changes
queue depth + age + History recency; the cached-doctor-findings
input lands in a follow-on once the cache format is formalized.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest
from livespec.commands import next as next_command

__all__: list[str] = []


def _make_spec_target(*, root: Path) -> Path:
    """Build a minimal SPECIFICATION/ tree under `root` and return its path.

    Creates the canonical `proposed_changes/` and `history/`
    subdirectories. The skill-owned `proposed_changes/README.md`
    is left absent by default; tests that care write it
    explicitly.
    """
    target = root / "SPECIFICATION"
    (target / "proposed_changes").mkdir(parents=True)
    (target / "history").mkdir(parents=True)
    return target


def _write_proposed_change(
    *,
    target: Path,
    topic: str,
    created_at: str,
    author: str = "test-llm",
) -> Path:
    """Write a `<target>/proposed_changes/<topic>.md` with valid front-matter.

    Body is a minimal placeholder; the next ranker reads only
    the YAML front-matter for `created_at`.
    """
    path = target / "proposed_changes" / f"{topic}.md"
    path.write_text(
        f"---\ntopic: {topic}\nauthor: {author}\ncreated_at: {created_at}\n---\n\nBody.\n",
        encoding="utf-8",
    )
    return path


def _make_history_versions(*, target: Path, count: int) -> None:
    """Create `<target>/history/v001/` ... `v<count>/` skeleton directories.

    Each directory is the minimum the ranker needs to count
    versions: an empty directory. The ranker counts directories
    via `iterdir`; full version content is not required for
    ranking.
    """
    for index in range(1, count + 1):
        (target / "history" / f"v{index:03d}").mkdir()


def test_next_main_returns_int(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/next.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert isinstance(exit_code, int)
    _ = capsys.readouterr()


def test_next_empty_queue_short_history_returns_none(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """No pending proposals + short history → action=none, urgency=low.

    The advisory output is the "nothing pressing" signal: the
    project's spec-side queue is drained and the history hasn't
    accreted enough versions to warrant pruning.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "none"
    assert payload["urgency"] == "low"
    assert isinstance(payload["reason"], str)
    assert len(payload["reason"]) > 0


def test_next_pending_proposal_returns_revise_action(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """One pending proposed change → action=revise.

    A non-empty Proposed Changes queue is the strongest signal
    for the spec-side ranker: revise drains it.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    _ = _write_proposed_change(
        target=target,
        topic="topic-x",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "revise"


def test_next_old_pending_proposal_returns_high_urgency(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Pending proposal older than 7 days → urgency=high.

    Age-based urgency is the second axis of the ranking
    (alongside queue depth). An old proposal is signaling
    drift / blocked work.
    """
    target = _make_spec_target(root=tmp_path)
    long_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)
    _ = _write_proposed_change(
        target=target,
        topic="topic-old",
        created_at=long_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "revise"
    assert payload["urgency"] == "high"


def test_next_medium_age_pending_proposal_returns_medium_urgency(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Single pending proposal aged 1-7 days → urgency=medium.

    Exercises the middle bucket of the age-based urgency
    classifier so each branch lights up under coverage.
    """
    target = _make_spec_target(root=tmp_path)
    middling = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
    _ = _write_proposed_change(
        target=target,
        topic="topic-middle",
        created_at=middling.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "revise"
    assert payload["urgency"] == "medium"


def test_next_fresh_pending_proposal_returns_low_urgency(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Single pending proposal aged less than 1 day → urgency=low.

    A just-filed proposal isn't urgent; the ranker emits revise
    with low urgency so the loop driver knows the queue is
    non-empty but not pressuring drain.
    """
    target = _make_spec_target(root=tmp_path)
    just_now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    _ = _write_proposed_change(
        target=target,
        topic="topic-fresh",
        created_at=just_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "revise"
    assert payload["urgency"] == "low"


def test_next_many_pending_proposals_returns_high_urgency(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Three or more pending proposals → urgency=high regardless of age.

    Queue-depth-based urgency: even if every proposal is fresh,
    a deep queue is itself a high-urgency signal — the spec is
    accreting un-decided changes.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for index in range(3):
        _ = _write_proposed_change(
            target=target,
            topic=f"topic-{index}",
            created_at=now,
        )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "revise"
    assert payload["urgency"] == "high"


def test_next_excludes_proposed_changes_readme(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The skill-owned `proposed_changes/README.md` is not a pending proposal.

    Per `SPECIFICATION/spec.md` §"Sub-command lifecycle" revise
    clause (a): the README is excluded from the in-flight
    proposal count. Without this exclusion, every fresh spec
    tree would report a pending proposal.
    """
    target = _make_spec_target(root=tmp_path)
    (target / "proposed_changes" / "README.md").write_text(
        "Skill-owned README.\n",
        encoding="utf-8",
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "none"


def test_next_long_history_with_empty_queue_returns_prune_history(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Empty queue + ≥20 history versions → action=prune-history, urgency=low.

    The prune-history recommendation surfaces only when the
    queue is empty (revise dominates) and the history has
    accreted enough versions to make pruning worth a cycle.
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=25)
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "prune-history"
    assert payload["urgency"] == "low"


def test_next_unknown_flag_returns_2(
    *,
    tmp_path: Path,
) -> None:
    """Unknown CLI flag → exit 2 (UsageError).

    Per `SPECIFICATION/contracts.md` §"Lifecycle exit-code
    table": exit 2 on bad CLI invocation. Drives the parse_argv
    stage on the railway: an unknown flag surfaces as an
    argparse SystemExit, which io/cli's @impure_safe maps to
    UsageError; the supervisor's pattern-match lifts to
    err.exit_code = 2.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(
        argv=["--project-root", str(tmp_path), "--no-such-flag"],
    )
    assert exit_code == 2


def test_next_missing_spec_target_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """--spec-target points to non-existent path → exit 3 (PreconditionError).

    Per `SPECIFICATION/contracts.md` §"Lifecycle exit-code
    table": exit 3 on project-state precondition failure. A
    missing spec target is the canonical precondition failure
    for any sub-command that reads spec content.
    """
    exit_code = next_command.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--spec-target",
            str(tmp_path / "no-such-spec"),
        ],
    )
    assert exit_code == 3


def test_next_default_project_root_is_cwd(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """--project-root defaults to Path.cwd() per the wrapper-CLI contract.

    Drives the cwd-fallback branch of the parser-default
    resolution. `monkeypatch.chdir(tmp_path)` isolates the test
    from the runner's invocation cwd so the fallback resolves
    deterministically to a writable scratch root rather than
    the repo cwd (preventing tmp-artifact leakage into the
    repo tree per the auto-memory `test_cwd_isolation` rule).
    """
    _ = _make_spec_target(root=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = next_command.main(argv=[])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "none"


def test_next_explicit_spec_target(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--spec-target selects a non-default spec tree explicitly.

    Per `SPECIFICATION/contracts.md` §"Wrapper CLI surface":
    --spec-target may name any spec tree (main spec or a
    sub-spec). Drives the explicit-spec-target branch (vs the
    `<project-root>/SPECIFICATION/` default).
    """
    custom_root = tmp_path / "templates" / "custom-spec"
    (custom_root / "proposed_changes").mkdir(parents=True)
    (custom_root / "history").mkdir()
    exit_code = next_command.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--spec-target",
            str(custom_root),
        ],
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "none"


def test_next_malformed_proposal_front_matter_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """Proposal with malformed YAML front-matter → exit 3 (PreconditionError).

    The ranker must read `created_at` from each proposal's
    front-matter to compute age-based urgency. A proposal
    lacking the canonical front-matter block is a project-state
    precondition failure surfaced through the same exit-3
    channel as a missing spec target.
    """
    target = _make_spec_target(root=tmp_path)
    (target / "proposed_changes" / "broken.md").write_text(
        "no front-matter here\n",
        encoding="utf-8",
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 3


def test_next_emits_schema_conformant_json(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """stdout payload conforms to next_output.schema.json.

    The wire contract is the schema; every emitted payload
    MUST validate against it. The test loads the schema and
    invokes fastjsonschema on the captured stdout payload —
    if the dataclass-to-JSON serialization drifts from the
    schema, this test fails before the schema-dataclass-
    pairing check ever runs.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    schema_path = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "schemas"
        / "next_output.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    import fastjsonschema

    validator = fastjsonschema.compile(schema)
    _ = validator(payload)
