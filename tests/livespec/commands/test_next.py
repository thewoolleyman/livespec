"""Tests for livespec.commands.next.

Per `SPECIFICATION/contracts.md` §"`/livespec:next` spec-side
thin-transport skill" → §"Wrapper CLI flags" + §"Output schema":
the `next` sub-command reads spec-side state (Proposed Changes
queue + Specification History) and emits JSON on stdout with two
top-level keys — `candidates` (array of `{action, reason,
urgency, target?}` objects) and `pagination` (`{offset, limit,
total, has_more}`). The wrapper accepts `--limit <count>`
(positive integer, default 5) and `--offset <count>`
(non-negative integer, default 0) in addition to the
§"Wrapper CLI surface" flags; non-positive `--limit` or
negative `--offset` exits 2 (UsageError). Pure function of file
state; no LLM in the ranking path.

Per §"Ranker semantics": the ranker enumerates ALL ripe
candidates, sorts within each action tier by urgency descending
then target lexicographic, and applies offset/limit last. Per
§"`prune-history` ordering invariant": prune-history sorts
strictly below every other action.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import pytest
from livespec.commands import next as next_command
from livespec.commands._next_ranking import _threshold_from_config_text
from livespec.errors import PreconditionError
from returns.result import Failure

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


def _run_and_load(
    *,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> dict[str, Any]:
    """Run the supervisor with `argv`, assert exit 0, and parse stdout JSON."""
    exit_code = next_command.main(argv=argv)
    assert exit_code == 0
    captured = capsys.readouterr()
    payload: dict[str, Any] = json.loads(captured.out)
    return payload


def test_next_main_returns_int(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: pins the canonical
    `main(*, argv) -> int` supervisor signature.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert isinstance(exit_code, int)
    _ = capsys.readouterr()


def test_next_empty_queue_short_history_returns_empty_candidates(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """No pending proposals + short history → `candidates: []`.

    Per §"Output schema": the empty array IS the no-work signal —
    the payload does not degrade to any legacy single-output
    shape. The pagination block echoes the defaults
    (`offset=0`, `limit=5`) with `total=0` and `has_more=false`.
    """
    _ = _make_spec_target(root=tmp_path)
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["candidates"] == []
    assert payload["pagination"] == {
        "offset": 0,
        "limit": 5,
        "total": 0,
        "has_more": False,
    }


def test_next_pending_proposal_returns_revise_candidate(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """One pending proposed change → one `revise` candidate naming it.

    A non-empty Proposed Changes queue is the strongest signal
    for the spec-side ranker: revise drains it. Per §"Output
    schema" the candidate's `target` is the spec-target-relative
    proposed_change path.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    _ = _write_proposed_change(
        target=target,
        topic="topic-x",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    candidate = payload["candidates"][0]
    assert candidate["action"] == "revise"
    assert candidate["target"] == "proposed_changes/topic-x.md"
    assert isinstance(candidate["reason"], str)
    assert len(candidate["reason"]) > 0


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
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    candidate = payload["candidates"][0]
    assert candidate["action"] == "revise"
    assert candidate["urgency"] == "high"


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
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    candidate = payload["candidates"][0]
    assert candidate["action"] == "revise"
    assert candidate["urgency"] == "medium"


def test_next_fresh_pending_proposal_returns_low_urgency(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Single pending proposal aged less than 1 day → urgency=low.

    A just-filed proposal isn't urgent; the ranker emits a revise
    candidate with low urgency so the loop driver knows the queue
    is non-empty but not pressuring drain.
    """
    target = _make_spec_target(root=tmp_path)
    just_now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    _ = _write_proposed_change(
        target=target,
        topic="topic-fresh",
        created_at=just_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    candidate = payload["candidates"][0]
    assert candidate["action"] == "revise"
    assert candidate["urgency"] == "low"


def test_next_enumerates_one_candidate_per_proposal(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Three pending proposals → three revise candidates, all high urgency.

    Per §"Ranker semantics": the ranker enumerates ALL ripe
    candidates, not just the top one. Queue-depth-based urgency:
    even if every proposal is fresh, a deep queue lifts every
    revise candidate to high. Ties sort by `target`
    lexicographic (the deterministic secondary key).
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for index in range(3):
        _ = _write_proposed_change(
            target=target,
            topic=f"topic-{index}",
            created_at=now,
        )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 3
    assert [c["action"] for c in payload["candidates"]] == ["revise"] * 3
    assert [c["urgency"] for c in payload["candidates"]] == ["high"] * 3
    assert [c["target"] for c in payload["candidates"]] == [
        "proposed_changes/topic-0.md",
        "proposed_changes/topic-1.md",
        "proposed_changes/topic-2.md",
    ]


def test_next_sorts_by_urgency_descending_within_tier(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Within the revise tier, higher-urgency candidates sort first.

    Per §"Ranker semantics": sort within each action tier by
    urgency descending, then by `target` lexicographic. An old
    proposal (high urgency via the age axis) outranks a fresh
    one (medium via the depth axis) even though the fresh one's
    target sorts earlier lexicographically.
    """
    target = _make_spec_target(root=tmp_path)
    long_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)
    just_now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    _ = _write_proposed_change(
        target=target,
        topic="a-fresh",
        created_at=just_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    _ = _write_proposed_change(
        target=target,
        topic="z-old",
        created_at=long_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert [c["target"] for c in payload["candidates"]] == [
        "proposed_changes/z-old.md",
        "proposed_changes/a-fresh.md",
    ]
    assert [c["urgency"] for c in payload["candidates"]] == ["high", "medium"]


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
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["candidates"] == []


def test_next_long_history_with_empty_queue_returns_prune_history(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Empty queue + ≥20 history versions → one prune-history candidate.

    The prune-history candidate carries `urgency: low` and omits
    `target` (pruning addresses a version range, not one item;
    per §"Output schema" `target` MAY be omitted).
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=25)
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    candidate = payload["candidates"][0]
    assert candidate["action"] == "prune-history"
    assert candidate["urgency"] == "low"
    assert "target" not in candidate


def test_next_ranks_prune_history_strictly_below_revise(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Pending proposals + long history → revise first, prune-history last.

    Per §"`prune-history` ordering invariant": when ANY ripe
    candidate exists with `action != prune-history`, the ranker
    MUST NOT emit prune-history as the primary recommendation —
    it sorts strictly below every other action tier regardless
    of urgency.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    _ = _write_proposed_change(
        target=target,
        topic="topic-x",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    _make_history_versions(target=target, count=25)
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 2
    assert payload["candidates"][0]["action"] == "revise"
    assert payload["candidates"][-1]["action"] == "prune-history"


def test_next_limit_slices_and_reports_has_more(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--limit 2 over 3 candidates → 2 returned, total=3, has_more=true.

    Per §"Wrapper CLI flags" + §"Output schema": `limit` caps the
    returned slice; `total` counts ripe candidates BEFORE
    offset/limit; `has_more` is true iff
    `offset + len(candidates) < total`.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for index in range(3):
        _ = _write_proposed_change(
            target=target,
            topic=f"topic-{index}",
            created_at=now,
        )
    payload = _run_and_load(
        capsys=capsys,
        argv=["--project-root", str(tmp_path), "--limit", "2"],
    )
    assert len(payload["candidates"]) == 2
    assert payload["pagination"] == {
        "offset": 0,
        "limit": 2,
        "total": 3,
        "has_more": True,
    }


def test_next_offset_skips_ranked_candidates(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--offset 1 skips the front of the ranked list before slicing.

    Per §"Wrapper CLI flags": offset is applied to the ranked
    list before limit. The remaining slice drains the list, so
    `has_more` is false.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for index in range(3):
        _ = _write_proposed_change(
            target=target,
            topic=f"topic-{index}",
            created_at=now,
        )
    payload = _run_and_load(
        capsys=capsys,
        argv=["--project-root", str(tmp_path), "--offset", "1"],
    )
    assert [c["target"] for c in payload["candidates"]] == [
        "proposed_changes/topic-1.md",
        "proposed_changes/topic-2.md",
    ]
    assert payload["pagination"] == {
        "offset": 1,
        "limit": 5,
        "total": 3,
        "has_more": False,
    }


def test_next_offset_at_or_beyond_total_returns_empty_window(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--offset >= total → `candidates: []` and `has_more: false`.

    Pinned verbatim by §"Output schema": "When `offset >= total`,
    the wrapper MUST emit `candidates: []` and `has_more:
    false`."
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    _ = _write_proposed_change(
        target=target,
        topic="topic-x",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    payload = _run_and_load(
        capsys=capsys,
        argv=["--project-root", str(tmp_path), "--offset", "9"],
    )
    assert payload["candidates"] == []
    assert payload["pagination"] == {
        "offset": 9,
        "limit": 5,
        "total": 1,
        "has_more": False,
    }


def test_next_non_positive_limit_returns_2(
    *,
    tmp_path: Path,
) -> None:
    """--limit 0 → exit 2 (UsageError).

    Per §"Wrapper CLI flags": "Non-positive `--limit` or negative
    `--offset` MUST cause the wrapper to exit `2` with a
    `UsageError`."
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(
        argv=["--project-root", str(tmp_path), "--limit", "0"],
    )
    assert exit_code == 2


def test_next_negative_offset_returns_2(
    *,
    tmp_path: Path,
) -> None:
    """--offset -1 → exit 2 (UsageError).

    The negative-offset twin of the non-positive-limit gate per
    §"Wrapper CLI flags".
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(
        argv=["--project-root", str(tmp_path), "--offset", "-1"],
    )
    assert exit_code == 2


def test_next_non_integer_limit_returns_2(
    *,
    tmp_path: Path,
) -> None:
    """--limit not-a-number → exit 2 (UsageError).

    Drives the argparse type-conversion failure path: with
    `exit_on_error=False`, the int conversion failure raises
    `argparse.ArgumentError`, which io/cli's `@impure_safe`
    maps to UsageError; the supervisor lifts exit 2.
    """
    _ = _make_spec_target(root=tmp_path)
    exit_code = next_command.main(
        argv=["--project-root", str(tmp_path), "--limit", "not-a-number"],
    )
    assert exit_code == 2


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
    payload = _run_and_load(capsys=capsys, argv=[])
    assert payload["candidates"] == []


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
    payload = _run_and_load(
        capsys=capsys,
        argv=[
            "--project-root",
            str(tmp_path),
            "--spec-target",
            str(custom_root),
        ],
    )
    assert payload["candidates"] == []


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
    pairing check ever runs. A pending proposal is included so
    the payload exercises the non-empty `candidates` branch.
    """
    target = _make_spec_target(root=tmp_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    _ = _write_proposed_change(
        target=target,
        topic="topic-x",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["candidates"] != []
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


def _write_livespec_config(*, root: Path, body: str) -> None:
    """Write `<root>/.livespec.jsonc` verbatim for the threshold tests.

    The next wrapper reads `next.prune_history_threshold` from the
    project-root-level `.livespec.jsonc` on each invocation per
    `SPECIFICATION/contracts.md` §"`.livespec.jsonc` configuration".
    """
    (root / ".livespec.jsonc").write_text(body, encoding="utf-8")


def test_next_lowered_threshold_config_triggers_prune_history(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """`next.prune_history_threshold: 5` + 5 versions → prune-history.

    Per §"`.livespec.jsonc` configuration": the wrapper MUST read
    the key on each invocation; a project MAY lower the threshold
    to surface pruning sooner. Five history versions would never
    trip the default threshold of 20, so the candidate appearing
    proves the configured value is read and applied.
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=5)
    _write_livespec_config(
        root=tmp_path,
        body='{"next": {"prune_history_threshold": 5}}',
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    assert payload["candidates"][0]["action"] == "prune-history"


def test_next_raised_threshold_config_defers_prune_history(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """`next.prune_history_threshold: 30` + 25 versions → no candidates.

    Per §"`.livespec.jsonc` configuration": a project MAY raise
    the threshold to defer prune-history recommendations on
    long-lived specs. Twenty-five versions trips the default of
    20, so an empty candidates array proves the configured value
    overrides the default.
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=25)
    _write_livespec_config(
        root=tmp_path,
        body='{"next": {"prune_history_threshold": 30}}',
    )
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["candidates"] == []


def test_next_non_positive_threshold_config_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """`next.prune_history_threshold: 0` → exit 3 (PreconditionError).

    Pinned verbatim by §"`.livespec.jsonc` configuration": "a
    non-positive value MUST cause the wrapper to exit `3` with a
    `PreconditionError` naming the offending key and value."
    """
    _ = _make_spec_target(root=tmp_path)
    _write_livespec_config(
        root=tmp_path,
        body='{"next": {"prune_history_threshold": 0}}',
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 3


def test_next_non_integer_threshold_config_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """`next.prune_history_threshold: "20"` (a string) → exit 3.

    Per §"`.livespec.jsonc` configuration": "The key value MUST
    be a positive integer" — a string value is a
    non-positive-integer value and takes the same exit-3
    PreconditionError channel as a non-positive integer.
    """
    _ = _make_spec_target(root=tmp_path)
    _write_livespec_config(
        root=tmp_path,
        body='{"next": {"prune_history_threshold": "20"}}',
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 3


def test_next_boolean_threshold_config_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """`next.prune_history_threshold: true` → exit 3.

    JSON `true` parses to Python `bool`, which is an `int`
    subclass — without an explicit bool gate it would silently
    coerce to threshold 1. The contract requires a positive
    integer, and a boolean is not one.
    """
    _ = _make_spec_target(root=tmp_path)
    _write_livespec_config(
        root=tmp_path,
        body='{"next": {"prune_history_threshold": true}}',
    )
    exit_code = next_command.main(argv=["--project-root", str(tmp_path)])
    assert exit_code == 3


def test_next_threshold_failure_names_key_and_value() -> None:
    """A rejected threshold's PreconditionError names the key and value.

    Pinned verbatim by §"`.livespec.jsonc` configuration": the
    PreconditionError must name "the offending key and value" so
    the user can locate and fix the config entry without
    spelunking the wrapper source.
    """
    result = _threshold_from_config_text(
        text='{"next": {"prune_history_threshold": -3}}',
    )
    match result:
        case Failure(PreconditionError() as err):
            assert "next.prune_history_threshold" in str(err)
            assert "-3" in str(err)
        case _:
            msg = f"expected Failure(PreconditionError), got {result!r}"
            raise AssertionError(msg)


def test_next_threshold_key_absent_in_next_section_defaults_to_20(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A `next` section without the key falls back to the default of 20.

    Per §"`.livespec.jsonc` configuration": "When the key is
    absent, the wrapper MUST fall back to a default value of
    `20`." Exactly 20 versions sits on the trigger boundary, so
    the prune-history candidate appearing proves the default
    applied.
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=20)
    _write_livespec_config(root=tmp_path, body='{"next": {}}')
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    assert payload["candidates"][0]["action"] == "prune-history"


def test_next_threshold_section_not_object_defaults_to_20(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A non-object `next` value means the key is absent → default 20.

    A top-level `next` key holding a scalar carries no
    `prune_history_threshold` member, so the key-absent fallback
    of §"`.livespec.jsonc` configuration" applies rather than the
    exit-3 channel (which is reserved for a present-but-invalid
    threshold value).
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=25)
    _write_livespec_config(root=tmp_path, body='{"next": 7}')
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    assert payload["candidates"][0]["action"] == "prune-history"


def test_next_malformed_livespec_config_defaults_to_20(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Malformed `.livespec.jsonc` is treated as key-absent → default 20.

    Mirrors the prune-history wrapper's
    `_resolve_skip_from_config_text` precedent: the
    `livespec_jsonc_valid` doctor check is the dedicated
    mechanism for surfacing malformed configs; the next wrapper's
    body-level concern is only the threshold resolution, so a
    parse failure collapses to the key-absent default.
    """
    target = _make_spec_target(root=tmp_path)
    _make_history_versions(target=target, count=25)
    _write_livespec_config(root=tmp_path, body='{"next": {"prune_history_')
    payload = _run_and_load(capsys=capsys, argv=["--project-root", str(tmp_path)])
    assert payload["pagination"]["total"] == 1
    assert payload["candidates"][0]["action"] == "prune-history"


def test_next_module_declares_hkt_erosion_pragma() -> None:
    """`commands/next.py` carries the file-level HKT-erosion pyright pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains that
    compose the next supervisor's railway lose flow-narrowing
    through pyright's strict mode, surfacing as
    reportUnknownMemberType / reportUnknownVariableType /
    reportUnknownArgumentType diagnostics on most bind / map
    / unsafe_perform_io call sites. Per-call cast() or refactor
    to named typed functions is the canonical fix but is
    infeasible at scale; the project-local trade-off is a
    file-level pragma that suppresses the three HKT-related
    categories. This contract test pins the pragma so a future
    reformatter / accidental top-comment edit / mass-rewrite
    that drops the pragma surfaces immediately rather than
    silently re-introducing ~27 pyright errors at the next
    `just check-types` run.
    """
    import inspect

    from livespec.commands import next as module_under_test

    source = inspect.getsource(module_under_test)
    assert source.startswith(
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n",
    ), "commands/next.py must declare the HKT-erosion pragma as its first line"
