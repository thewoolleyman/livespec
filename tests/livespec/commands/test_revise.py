"""Tests for livespec.commands.revise.

Per and Plan Phase 3
: revise is minimum-viable per v019 Q1 —
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

    Per: the wrapper
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
        "## Proposal: demo\nContent.\n",
        encoding="utf-8",
    )
    revise_path = _write_valid_revise_payload(tmp_path=tmp_path)
    exit_code = revise.main(
        argv=[
            "--revise-json",
            str(revise_path),
            "--spec-target",
            str(spec_target),
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
        "## Proposal: demo\nContent.\n",
        encoding="utf-8",
    )
    revise_path = _write_valid_revise_payload(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = revise.main(argv=["--revise-json", str(revise_path)])
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
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

    Per: each processed
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    assert revision_md.exists(), f"expected {revision_md} to be written"
    text = revision_md.read_text(encoding="utf-8")
    assert "decision: reject" in text
    assert "Not aligned with current direction." in text


def test_revise_main_moves_proposed_change_into_history_for_reject_decision(
    *,
    tmp_path: Path,
) -> None:
    """For a `reject` decision, the proposed-change file moves into history.

    Per: each processed
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    moved_md = spec_target / "history" / "v002" / "proposed_changes" / "demo.md"
    assert moved_md.exists(), f"expected {moved_md} to be written"
    assert moved_md.read_text(encoding="utf-8") == original_content
    assert not proposed_md.exists(), f"expected original {proposed_md} to be removed after move"


def test_revise_main_materializes_resulting_files_for_accept_decision(
    *,
    tmp_path: Path,
) -> None:
    """For an `accept` decision, working-spec files in resulting_files are updated.

    Per: if any decision
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    assert spec_md.read_text(encoding="utf-8") == new_spec_content


def _git_init_with_user(*, cwd: Path, name: str, email: str) -> None:
    """Initialize a git repo at `cwd` and set local user.name + user.email.

    Mirrors the helper in `tests/livespec/io/test_git.py`. Used by
    the v038-widened revise tests that exercise the
    `io.git.get_git_user` integration in the revision-md
    front-matter `author_human` field.
    """
    import subprocess

    _ = subprocess.run(
        ["git", "init", "--quiet"],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.name", name],
        cwd=cwd,
        check=True,
    )
    _ = subprocess.run(
        ["git", "config", "--local", "user.email", email],
        cwd=cwd,
        check=True,
    )


def test_revise_main_writes_full_5key_front_matter_for_reject_decision(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """The revision-md front-matter has all 5 required keys per v038/v011 spec.

    Per `SPECIFICATION/spec.md` §"Proposed-change and revision file
    formats" §"Revision file format" + `revision_front_matter.schema.json`:
    `proposal`, `decision`, `revised_at`, `author_human`, `author_llm`.
    Drives the widening of `_compose_revision_body` from the
    Phase-3-minimum 2-key shape (proposal + decision) to the full
    5-key shape. The `author_human` value is composed via
    `io.git.get_git_user` (cycle 5.c.1 landed at `9547caa`); the
    `author_llm` is resolved per the unified 4-step precedence
    via a new `_resolve_author` helper analogous to
    propose_change/critique. The `revised_at` is computed via
    `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`
    matching propose_change's `created_at` shape.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "reject",
                        "rationale": "Not aligned.",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "proposal: demo.md" in text
    assert "decision: reject" in text
    assert "revised_at:" in text
    assert "author_human: Test User <test@example.com>" in text
    assert "author_llm: unknown-llm" in text


def test_revise_main_emits_modifications_section_for_modify_decision(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """For a `modify` decision, the revision-md emits a `## Modifications` section.

    Per `SPECIFICATION/spec.md` §"Revision file format" item (3):
    `## Modifications` is REQUIRED when `decision: modify`; the
    section carries prose-form description of how the proposal
    was changed before incorporation. Asserts both the heading
    appears and the modifications text from the decision dict
    is embedded.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "modify",
                        "rationale": "Mostly OK.",
                        "modifications": "Tightened the wording on paragraph 2.",
                        "resulting_files": [
                            {"path": "spec.md", "content": "modified content"},
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "## Modifications" in text
    assert "Tightened the wording on paragraph 2." in text


def test_revise_main_emits_resulting_changes_section_for_accept_decision(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """For an `accept` decision, the revision-md emits a `## Resulting Changes` section.

    Per `SPECIFICATION/spec.md` §"Revision file format" item (4):
    `## Resulting Changes` is REQUIRED when `decision: accept`
    or `modify`; the section names the specification files
    modified and lists the sections changed. Asserts both the
    heading appears and the file path from `resulting_files[0]`
    is embedded.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "proposal_topic": "demo",
                        "decision": "accept",
                        "rationale": "Looks good.",
                        "resulting_files": [
                            {"path": "spec.md", "content": "new content"},
                        ],
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "## Resulting Changes" in text
    assert "spec.md" in text


def test_revise_main_resolves_cli_author_flag_into_author_llm(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """`--author <id>` CLI wins step 1 of the 4-step author precedence.

    Drives `_resolve_author`'s `if namespace.author:` branch.
    Asserts the revision-md `author_llm:` line carries the
    CLI-supplied identifier verbatim, with no env / payload /
    fallback interference.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setenv("LIVESPEC_AUTHOR_LLM", "env-loses-to-cli")
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "author": "payload-also-loses-to-cli",
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "--author",
            "cli-wins",
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "author_llm: cli-wins" in text


def test_revise_main_resolves_env_var_into_author_llm_when_no_cli_flag(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """`LIVESPEC_AUTHOR_LLM` env wins step 2 of the 4-step author precedence.

    Drives `_resolve_author`'s `env_value` branch (no `--author`
    CLI, env var set). Asserts the revision-md `author_llm:` line
    carries the env value, beating the payload-self-declaration
    fallback and the `unknown-llm` fallback.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setenv("LIVESPEC_AUTHOR_LLM", "env-wins-no-cli")
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "author": "payload-loses-to-env",
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "author_llm: env-wins-no-cli" in text


def test_revise_main_resolves_payload_author_into_author_llm_when_no_cli_no_env(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """Payload `author` field wins step 3 of the 4-step author precedence.

    Drives `_resolve_author`'s `payload.author` branch (no `--author`
    CLI, no env var, payload has self-declared `author` field).
    Asserts the revision-md `author_llm:` line carries the payload
    value, beating the `unknown-llm` fallback.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(
        json.dumps(
            {
                "author": "payload-self-declared",
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "author_llm: payload-self-declared" in text


def test_revise_compose_resulting_changes_emits_none_marker_when_resulting_files_absent() -> None:
    """Direct test of `_compose_resulting_changes_section` defensive paths.

    Drives the two defensive branches in
    `_compose_resulting_changes_section`: (a) the `isinstance(
    resulting_files, list)` False arm when the decision dict
    has no `resulting_files` key (the `.get(..., [])` default
    DOES return a list, so this also exercises the empty-list
    case where the for-loop body doesn't run); (b) the
    `isinstance(entry, dict)` False arm when an entry is a
    non-dict value (defensive against a runtime type-violating
    payload).

    These branches are unreachable through `revise.main` because
    `revise_input.schema.json` enforces `resulting_files` is an
    array of `{path, content}` objects at the wrapper boundary.
    The defensive checks remain in the impl because the
    post-validation railway flows the decision dict typed as
    `dict[str, object]` (the schema-narrowed type isn't preserved
    through the dataclass), so pyright strict requires the
    isinstance narrowings.
    """
    body_no_files = revise._compose_resulting_changes_section(  # noqa: SLF001
        decision={"decision": "accept"},
    )
    assert "## Resulting Changes" in body_no_files
    assert "(none)" in body_no_files
    body_non_dict_entry = revise._compose_resulting_changes_section(  # noqa: SLF001
        decision={"decision": "accept", "resulting_files": ["not-a-dict-entry"]},
    )
    assert "## Resulting Changes" in body_non_dict_entry
    assert "(none)" in body_non_dict_entry
    body_non_list = revise._compose_resulting_changes_section(  # noqa: SLF001
        decision={"decision": "accept", "resulting_files": "not-a-list"},
    )
    assert "## Resulting Changes" in body_non_list
    assert "(none)" in body_non_list


def test_revise_main_emits_rejection_notes_section_for_reject_decision(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """For a `reject` decision, the revision-md emits a `## Rejection Notes` section.

    Per `SPECIFICATION/spec.md` §"Revision file format" item (5):
    `## Rejection Notes` is REQUIRED when `decision: reject`;
    explains what would need to change about the proposal for it
    to be acceptable in a future revision. This is the
    rejection-flow audit-trail richness Plan Phase 7
    mandates ("rejection flow preserving audit trail").
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    _git_init_with_user(cwd=tmp_path, name="Test User", email="test@example.com")
    monkeypatch.chdir(tmp_path)

    spec_target = tmp_path / "spec-root"
    (spec_target / "history" / "v001").mkdir(parents=True)
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "demo.md").write_text(
        "## Proposal: demo\n",
        encoding="utf-8",
    )
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    revision_md = spec_target / "history" / "v002" / "proposed_changes" / "demo-revision.md"
    text = revision_md.read_text(encoding="utf-8")
    assert "## Rejection Notes" in text


def test_revise_main_snapshots_working_spec_files_into_history_vnnn(
    *,
    tmp_path: Path,
) -> None:
    """Per v011 Proposal 3 item d, every successful revise snapshots
    every spec-root file byte-identically into `<spec-target>/history/vNNN/`.

    Subdirectories at the spec-root (`history/`, `proposed_changes/`,
    `templates/`) are NOT snapshotted — only the template-declared spec
    files (immediate file children of `<spec-target>/`). Implements
    v038 D1 Statement B's "version cut on every successful revise"
    contract: the new `history/vNNN/` carries byte-identical copies of
    the working-spec files as they stand post-revise.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    (spec_target / "history" / "v001").mkdir(parents=True)
    (spec_target / "templates" / "livespec").mkdir(parents=True)
    spec_md = spec_target / "spec.md"
    contracts_md = spec_target / "contracts.md"
    readme_md = spec_target / "README.md"
    _ = spec_md.write_text("# Spec\nSpec body.\n", encoding="utf-8")
    _ = contracts_md.write_text("# Contracts\nContracts body.\n", encoding="utf-8")
    _ = readme_md.write_text("# README\nReadme body.\n", encoding="utf-8")
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
                        "rationale": "Demo rationale.",
                    },
                ],
            },
        ),
        encoding="utf-8",
    )
    exit_code = revise.main(
        argv=[
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    history_v002 = spec_target / "history" / "v002"
    assert (history_v002 / "spec.md").read_text(encoding="utf-8") == "# Spec\nSpec body.\n"
    assert (history_v002 / "contracts.md").read_text(
        encoding="utf-8"
    ) == "# Contracts\nContracts body.\n"
    assert (history_v002 / "README.md").read_text(encoding="utf-8") == "# README\nReadme body.\n"
    assert not (history_v002 / "templates").exists()
    assert not (history_v002 / "history").exists()


def test_revise_main_snapshot_captures_post_resulting_files_content_for_accept_decision(
    *,
    tmp_path: Path,
) -> None:
    """Per v011 Proposal 3 item d, snapshot reflects post-update content.

    For an `accept` decision, `resulting_files` materialize into the
    working spec BEFORE the snapshot is taken; the snapshot's `spec.md`
    in `history/vNNN/` carries the new content, not the pre-update
    content. Pins the ordering of resulting-files-write -> snapshot.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    (spec_target / "history" / "v001").mkdir(parents=True)
    spec_md = spec_target / "spec.md"
    _ = spec_md.write_text("# Spec v1\nOld content.\n", encoding="utf-8")
    proposed_md = proposed_changes / "demo.md"
    _ = proposed_md.write_text("## Proposal: demo\n", encoding="utf-8")
    new_spec_content = "# Spec v2\nNew content.\n"
    payload_path = tmp_path / "revise.json"
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    snapshot_md = spec_target / "history" / "v002" / "spec.md"
    assert snapshot_md.read_text(encoding="utf-8") == new_spec_content


def test_revise_main_returns_precondition_exit_code_when_proposed_changes_only_has_readme(
    *,
    tmp_path: Path,
) -> None:
    """Per v011 Proposal 3 item a, revise fails on README-only proposed_changes/.

    When `<spec-target>/proposed_changes/` contains only the
    skill-owned `README.md` (zero in-flight proposal files), revise
    MUST exit 3 (PreconditionError) without any file-system
    mutations. Pins the precondition check at the railway boundary
    before any per-decision processing.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    _ = (proposed_changes / "README.md").write_text(
        "# Skill-owned README\n",
        encoding="utf-8",
    )
    (spec_target / "history" / "v001").mkdir(parents=True)
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 3
    assert not (spec_target / "history" / "v002").exists()


def test_revise_main_returns_precondition_exit_code_when_proposed_changes_completely_empty(
    *,
    tmp_path: Path,
) -> None:
    """Per v011 Proposal 3 item a, revise fails on completely empty proposed_changes/.

    Variant of the README-only test: `proposed_changes/` exists
    but has zero entries (not even `README.md`). Same exit-3
    outcome; no file-system mutations.
    """
    spec_target = tmp_path / "spec-root"
    proposed_changes = spec_target / "proposed_changes"
    proposed_changes.mkdir(parents=True)
    (spec_target / "history" / "v001").mkdir(parents=True)
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
            "--revise-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 3
    assert not (spec_target / "history" / "v002").exists()
