"""Tests for livespec.commands.revise.

Per PROPOSAL.md §"`revise`" (line ~2335) and Plan Phase 3
(lines 1533-1553): revise is minimum-viable per v019 Q1 —
validate `--revise-json` payload, process per-proposal
`decisions[]` in payload order, write paired
`<stem>-revision.md`, move processed proposed-change files into
`history/vNNN/proposed_changes/`, cut new `history/vNNN/`.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.commands import revise

__all__: list[str] = []


def test_revise_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/revise.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = revise.main(argv=["--revise-json", "/tmp/x.json"])
    assert isinstance(exit_code, int)


def test_revise_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing required `--revise-json <path>` returns exit code 2.

    Per PROPOSAL.md §"`revise`" lines 2375-2410: the wrapper
    requires `--revise-json <path>` (plus optional `--author
    <id>`, `--spec-target <path>`, `--project-root <path>`).
    Drives the first real railway-composition behavior by
    threading argv through io/cli.parse_argv and pattern-matching
    the IOFailure(UsageError) onto err.exit_code (= 2).
    """
    exit_code = revise.main(argv=[])
    assert exit_code == 2


def test_revise_main_returns_precondition_exit_code_on_missing_revise_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --revise-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to the supervisor's pattern-match, which lifts to
    exit 3 via err.exit_code per style doc §"Exit code contract".
    Mirrors propose_change/critique's same railway stage.
    """
    missing = tmp_path / "no-such-revise.json"
    exit_code = revise.main(argv=["--revise-json", str(missing)])
    assert exit_code == 3


def _write_valid_revise_payload(*, tmp_path: Path) -> Path:
    """Helper: write a schema-valid revise-input payload to tmp_path.

    Mirrors propose_change/critique helpers: the payload conforms
    to revise_input.schema.json with one reject-decision so the
    railway can reach the Success arm without needing the
    accept/modify file-shaping branches yet.
    """
    import json

    payload_dict = {
        "decisions": [
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": "Demo rejection rationale.",
            },
        ],
    }
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    return payload_path


def test_revise_main_returns_zero_when_revise_file_readable(
    *,
    tmp_path: Path,
) -> None:
    """When --revise-json points at a schema-valid payload, main returns 0.

    Drives the Success arm of `_pattern_match_io_result`: the
    parse_argv -> fs.read_text -> jsonc.loads -> validate ->
    process_decisions composition reaches IOSuccess, the
    pattern-match falls into the Success(_) case, and the
    supervisor returns 0. Sets up a minimum spec-target with a
    `history/v001/` directory + a pending `proposed_changes/
    demo.md` so the per-decision processing can move that file
    into the new history version.
    """
    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\nContent.\n", encoding="utf-8",
    )
    revise_path = _write_valid_revise_payload(tmp_path=tmp_path)
    exit_code = revise.main(
        argv=[
            "--revise-json", str(revise_path),
            "--spec-target", str(spec_target),
        ],
    )
    assert exit_code == 0


def test_revise_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) bubbles via
    bind chaining; exit 4 per style doc §"Exit code contract".
    Mirrors critique's cycle-120 stage.
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = revise.main(argv=["--revise-json", str(payload)])
    assert exit_code == 4


def test_revise_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives the railway widening to include schema validation
    against revise_input.schema.json. The payload `{}` is valid
    JSON so jsonc.loads succeeds; it then trips schema validation
    (missing required `decisions` array) which returns
    Failure(ValidationError) and lifts to exit 4. Mirrors
    critique's cycle-121 stage.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = revise.main(argv=["--revise-json", str(payload)])
    assert exit_code == 4


def test_revise_main_uses_cwd_specification_default_when_no_target_flags(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """Without --spec-target / --project-root, falls back to `cwd()/SPECIFICATION`.

    Drives `_resolve_spec_target`'s cwd-fallback branch (the
    `Path.cwd() if namespace.project_root is None` arm). Uses
    monkeypatch.chdir into a tmp_path that has a writable
    `SPECIFICATION/history/v001/` precreated, so the per-decision
    processing can write into the cwd-derived target.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    spec_target = tmp_path / "SPECIFICATION"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\nContent.\n", encoding="utf-8",
    )
    revise_path = _write_valid_revise_payload(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = revise.main(argv=["--revise-json", str(revise_path)])
    assert exit_code == 0
    revision_md = (
        spec_target
        / "history"
        / "v002"
        / "proposed_changes"
        / "demo-revision.md"
    )
    assert revision_md.exists(), f"expected {revision_md} to be written"


def test_revise_format_next_version_name_skips_non_directory_entries(
    *,
    tmp_path: Path,
) -> None:
    """`_format_next_version_name` skips non-directory children defensively.

    Drives the `if not child.is_dir(): continue` guard branch.
    The fixture mixes a regular file (skipped) with a v001 dir
    (counted). The expected next version is `v002`.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    children = sorted(history.iterdir())
    assert revise._format_next_version_name(children=children) == "v002"  # noqa: SLF001


def test_revise_format_next_version_name_skips_non_v_prefix_dirs(
    *,
    tmp_path: Path,
) -> None:
    """`_format_next_version_name` skips dirs whose name doesn't start with `v`.

    Drives the `if not name.startswith("v"): continue` guard.
    Fixture: a `proposed_changes/` dir alongside `v001/`; the
    proposed_changes dir is correctly skipped.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "proposed_changes").mkdir()
    children = sorted(history.iterdir())
    assert revise._format_next_version_name(children=children) == "v002"  # noqa: SLF001


def test_revise_format_next_version_name_skips_v_prefix_with_non_digit_suffix(
    *,
    tmp_path: Path,
) -> None:
    """`_format_next_version_name` skips `v<non-digit>` dirs defensively.

    Drives the `if not suffix.isdigit(): continue` guard. Fixture:
    a `vXXX/` dir alongside `v001/`; the malformed entry is
    correctly skipped.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "vXXX").mkdir()
    children = sorted(history.iterdir())
    assert revise._format_next_version_name(children=children) == "v002"  # noqa: SLF001


def test_revise_bind_resulting_files_skips_non_list_resulting_files(
    *,
    tmp_path: Path,
) -> None:
    """`_bind_resulting_files` skips when resulting_files is not a list.

    Drives the `if not isinstance(resulting_files, list): return accumulator`
    guard. Schema-validation should prevent malformed types from
    reaching this helper, but the runtime isinstance-check keeps
    pyright strict-mode + bug-class drift safe.
    """
    from livespec.schemas.dataclasses.revise_input import RevisionInput
    from returns.io import IOSuccess

    revise_input = RevisionInput(author=None, decisions=[])
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": "Looks good.",
        "resulting_files": "not-a-list",
    }
    initial = IOSuccess(revise_input)
    result = revise._bind_resulting_files(  # noqa: SLF001
        accumulator=initial,
        decision=decision,
        spec_target=tmp_path,
        revise_input=revise_input,
    )
    assert result == initial


def test_revise_bind_resulting_files_skips_non_dict_entry(
    *,
    tmp_path: Path,
) -> None:
    """`_bind_resulting_files` skips per-entry when an entry is not a dict.

    Drives the `if not isinstance(entry, dict): continue` guard.
    Schema-validation should prevent malformed types from
    reaching this helper, but the runtime isinstance-check keeps
    pyright strict-mode + bug-class drift safe.
    """
    from livespec.schemas.dataclasses.revise_input import RevisionInput
    from returns.io import IOSuccess

    revise_input = RevisionInput(author=None, decisions=[])
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": "Looks good.",
        "resulting_files": ["not-a-dict"],
    }
    initial = IOSuccess(revise_input)
    result = revise._bind_resulting_files(  # noqa: SLF001
        accumulator=initial,
        decision=decision,
        spec_target=tmp_path,
        revise_input=revise_input,
    )
    assert result == initial


def test_revise_main_writes_paired_revision_for_reject_decision(
    *,
    tmp_path: Path,
) -> None:
    """For a `reject` decision, revise writes `<stem>-revision.md`.

    Per PROPOSAL.md §"`revise`" lines 2422-2436: each processed
    proposal gets a paired revision at
    `<spec-root>/history/vN/proposed_changes/<stem>-revision.md`.
    Phase-3 minimum-viable for `reject`: the revision file's
    front-matter records `decision: reject` + the rationale; no
    new version cut (no `accept`/`modify` decision present);
    the original proposed-change file moves byte-identically into
    the new history directory.

    This test pins the smallest reject-only behavior: setup a
    spec-target with a v001/ history (the seed baseline) + one
    pending proposed-change, run revise with a reject decision,
    assert that the paired revision file exists in
    `history/v002/proposed_changes/` with the rationale embedded.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    history_v001 = spec_target / "history" / "v001"
    history_v001.mkdir(parents=True)
    proposed_md = proposed_changes / "demo.md"
    _ = proposed_md.write_text("## Proposal: demo\nContent.\n", encoding="utf-8")
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "reject",
                        "rationale": "Not aligned with current direction.",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json", str(payload_path),
            "--spec-target", str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = (
        spec_target
        / "history"
        / "v002"
        / "proposed_changes"
        / "demo-revision.md"
    )
    assert revision_md.exists(), f"expected {revision_md} to be written"
    text = revision_md.read_text(encoding="utf-8")
    assert "decision: reject" in text
    assert "Not aligned with current direction." in text


def test_revise_main_moves_proposed_change_into_history_for_reject_decision(
    *,
    tmp_path: Path,
) -> None:
    """For a `reject` decision, the proposed-change file moves into history.

    Per PROPOSAL.md §"`revise`" lines 2422-2429: each processed
    proposal file is moved byte-identically from
    `<spec-target>/proposed_changes/<stem>.md` into
    `<spec-target>/history/vN/proposed_changes/<stem>.md`. The
    move is byte-identical (same content; same filename stem).

    Asserts both: (a) the original proposed-change file is no
    longer at `proposed_changes/<stem>.md`; (b) the same content
    now lives at `history/vN/proposed_changes/<stem>.md`.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_md = proposed_changes / "demo.md"
    original_content = "## Proposal: demo\nContent.\n"
    _ = proposed_md.write_text(original_content, encoding="utf-8")
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "reject",
                        "rationale": "Demo rationale.",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json", str(payload_path),
            "--spec-target", str(spec_target),
        ],
    )
    assert exit_code == 0
    moved_md = (
        spec_target
        / "history"
        / "v002"
        / "proposed_changes"
        / "demo.md"
    )
    assert moved_md.exists(), f"expected {moved_md} to be written"
    assert moved_md.read_text(encoding="utf-8") == original_content
    assert not proposed_md.exists(), (
        f"expected original {proposed_md} to be removed after move"
    )


def test_revise_main_materializes_resulting_files_for_accept_decision(
    *,
    tmp_path: Path,
) -> None:
    """For an `accept` decision, working-spec files in resulting_files are updated.

    Per PROPOSAL.md §"`revise`" lines 2411-2421: if any decision
    is `accept` or `modify`, working-spec files named in
    `resulting_files` are updated in place with the new content.
    Phase-3 minimum-viable: write each `{path, content}` entry's
    content to its `<spec-target>/<path>` location verbatim.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    (spec_target / "history" / "v001").mkdir(parents=True)
    spec_md = spec_target / "spec.md"
    _ = spec_md.write_text("# Spec v1\nOld content.\n", encoding="utf-8")
    proposed_md = proposed_changes / "demo.md"
    _ = proposed_md.write_text("## Proposal: demo\n", encoding="utf-8")
    payload_path = tmp_path / "revise.json"
    new_spec_content = "# Spec v2\nNew content.\n"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "accept",
                        "rationale": "Looks good.",
                        "resulting_files": [
                            {"path": "spec.md", "content": new_spec_content},
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json", str(payload_path),
            "--spec-target", str(spec_target),
        ],
    )
    assert exit_code == 0
    assert spec_md.read_text(encoding="utf-8") == new_spec_content
