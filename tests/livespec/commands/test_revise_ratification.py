"""Tests for livespec.commands._revise_ratification."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from livespec.commands._revise_helpers import _compose_revision_body
from livespec.commands._revise_ratification import (
    _canonical_ratification_digest,
    _validate_ratification_reviews,
)
from livespec.schemas.dataclasses.revise_input import RevisionInput
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

_DEFAULT_EVIDENCE = object()


def test_canonical_ratification_digest_matches_uint64_be_known_bytes() -> None:
    decision = {
        "resulting_files": [
            {"path": "ab", "content": "c"},
            {"path": "a", "content": "bc"},
        ],
    }
    expected_bytes = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x01a"
        b"\x00\x00\x00\x00\x00\x00\x00\x02bc"
        b"\x00\x00\x00\x00\x00\x00\x00\x02ab"
        b"\x00\x00\x00\x00\x00\x00\x00\x01c"
    )
    expected = hashlib.sha256(expected_bytes).hexdigest()

    assert _canonical_ratification_digest(decision=decision) == expected


def test_canonical_ratification_digest_is_independent_of_resulting_file_order() -> None:
    forward = [
        {"path": "a", "content": "first"},
        {"path": "z", "content": "last"},
    ]

    assert _canonical_ratification_digest(
        decision={"resulting_files": forward},
    ) == _canonical_ratification_digest(
        decision={"resulting_files": list(reversed(forward))},
    )


def test_canonical_ratification_digest_binds_proposal_bytes() -> None:
    decision = {"resulting_files": [{"path": "spec.md", "content": "final"}]}

    assert _canonical_ratification_digest(
        decision=decision,
        proposal_bytes=b"proposal one\n",
    ) != _canonical_ratification_digest(
        decision=decision,
        proposal_bytes=b"proposal two\n",
    )


def test_canonical_ratification_digest_skips_malformed_runtime_shapes() -> None:
    empty_proposal = hashlib.sha256(b"\x00" * 8).hexdigest()

    assert _canonical_ratification_digest(decision={"resulting_files": "bad"}) == empty_proposal
    assert _canonical_ratification_digest(decision={"resulting_files": ["bad"]}) == empty_proposal


def test_validate_ratification_reviews_accepts_valid_evidence_with_configured_model(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = _proposal_bytes(created_at="2026-08-03T12:30:00Z")
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"ratification_reviewer_model":"fable"}}',
        encoding="utf-8",
    )
    resulting_files = [{"path": "spec.md", "content": "new"}]
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            revised_at="2026-08-03T12:37:25Z",
            spec_target=spec_target,
        ),
    )

    assert result == Success(revise_input)


def test_validate_ratification_reviews_accepts_v197_shaped_review_gap(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = _proposal_bytes(created_at="2026-08-03T12:30:00Z")
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
        reviewed_at="2026-08-03T12:34:56Z",
    )
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=evidence,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            revised_at="2026-08-03T12:37:25Z",
            spec_target=spec_target,
        ),
    )

    assert result == Success(revise_input)


@pytest.mark.parametrize(
    "reviewed_at",
    [
        "2026-08-03T12:29:59Z",
        "2026-08-03T12:37:25Z",
        "2026-08-03T12:37:26Z",
    ],
)
def test_validate_ratification_reviews_rejects_out_of_order_review_timestamps(
    *,
    tmp_path: Path,
    reviewed_at: str,
) -> None:
    proposal_bytes = _proposal_bytes(created_at="2026-08-03T12:30:00Z")
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
        reviewed_at=reviewed_at,
    )
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=evidence,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            revised_at="2026-08-03T12:37:25Z",
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_honors_configured_review_gap_threshold(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = _proposal_bytes(created_at="2026-08-03T12:30:00Z")
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"ratification_min_review_age_seconds":3}}',
        encoding="utf-8",
    )
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
        reviewed_at="2026-08-03T12:37:23Z",
    )
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=evidence,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            revised_at="2026-08-03T12:37:25Z",
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_rejects_non_no_blockers_verdict(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = b"proposal\n"
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
    )
    evidence["verdict"] = "BLOCKERS"
    revise_input = RevisionInput(
        author=None,
        decisions=[
            {
                "proposal_topic": "demo",
                "decision": "accept",
                "rationale": ".",
                "resulting_files": resulting_files,
                "ratification_review": "auto-spawn",
                "ratification_evidence": evidence,
            },
        ],
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reviewer_identity", "other"),
        ("separate_reviewer", False),
        ("read_only", False),
        ("reviewed_at", "2026-08-03T12:34Z"),
        ("proposal_stem", "other"),
        ("content_digest", "bad"),
        ("content_digest", "0" * 64),
    ],
)
def test_validate_ratification_reviews_rejects_malformed_evidence_fields(
    *,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    proposal_bytes = b"proposal\n"
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    resulting_files = [{"path": "spec.md", "content": "new"}]
    evidence = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
    )
    evidence[field] = value
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=evidence,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_rejects_missing_evidence_and_bad_mode(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = b"proposal\n"
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    resulting_files = [{"path": "spec.md", "content": "new"}]
    missing = _evidence(
        proposal_bytes=proposal_bytes,
        resulting_files=resulting_files,
    )
    del missing["read_only"]
    bad_mode = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        mode="bad",
    )
    no_evidence = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=None,
    )
    missing_field = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
        evidence=missing,
    )

    for revise_input in (bad_mode, no_evidence, missing_field):
        result = unsafe_perform_io(
            _validate_ratification_reviews(
                revise_input=revise_input,
                project_root=tmp_path,
                spec_target=spec_target,
            ),
        )
        assert isinstance(result, Failure)


def test_validate_ratification_reviews_rejects_configured_model_mismatch(
    *,
    tmp_path: Path,
) -> None:
    proposal_bytes = b"proposal\n"
    spec_target = _write_proposal(tmp_path=tmp_path, proposal_bytes=proposal_bytes)
    (tmp_path / ".livespec.jsonc").write_text(
        '{"spec_governance":{"ratification_reviewer_model":"other"}}',
        encoding="utf-8",
    )
    resulting_files = [{"path": "spec.md", "content": "new"}]
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


def test_validate_ratification_reviews_allows_reject_without_evidence(
    *,
    tmp_path: Path,
) -> None:
    spec_target = tmp_path / "SPECIFICATION"
    revise_input = RevisionInput(
        author=None,
        decisions=[
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": ".",
            },
        ],
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        ),
    )

    assert result == Success(revise_input)


def test_validate_ratification_reviews_never_spawns_agents() -> None:
    source = Path(
        ".claude-plugin/scripts/livespec/commands/_revise_ratification.py",
    ).read_text(encoding="utf-8")

    assert "subprocess" not in source
    assert "Task(" not in source
    assert "fable" not in source.lower()


def test_compose_revision_body_handles_malformed_runtime_evidence_defensively() -> None:
    body = _compose_revision_body(
        decision={
            "proposal_topic": "demo",
            "decision": "accept",
            "rationale": ".",
            "resulting_files": [],
            "ratification_review": "manual-spawn",
            "ratification_evidence": "bad",
        },
        author_human="Human <human@example.com>",
        author_llm="llm",
        revised_at="2026-08-03T12:34:56Z",
    )

    assert "## Ratification Review\n\n(none)" in body


@pytest.mark.parametrize("proposal_exists", [False, True])
def test_validate_ratification_reviews_fails_closed_when_proposal_cannot_be_read(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    proposal_exists: bool,
) -> None:
    proposal_bytes = b"proposal\n"
    spec_target = tmp_path / "SPECIFICATION"
    proposal_path = spec_target / "proposed_changes" / "demo.md"
    if proposal_exists:
        proposal_path.parent.mkdir(parents=True)
        proposal_path.write_bytes(proposal_bytes)

        def deny_proposal_read(path: Path) -> bytes:
            assert path == proposal_path
            raise PermissionError("proposal unreadable")

        monkeypatch.setattr(Path, "read_bytes", deny_proposal_read)

    resulting_files = [{"path": "spec.md", "content": "new"}]
    revise_input = _mutating_input(
        resulting_files=resulting_files,
        proposal_bytes=proposal_bytes,
    )

    result = unsafe_perform_io(
        _validate_ratification_reviews(
            revise_input=revise_input,
            project_root=tmp_path,
            spec_target=spec_target,
        ),
    )

    assert isinstance(result, Failure)


def _contract_digest(
    *,
    proposal_bytes: bytes,
    resulting_files: list[dict[str, str]],
) -> str:
    digest = hashlib.sha256()
    digest.update(len(proposal_bytes).to_bytes(8, "big"))
    digest.update(proposal_bytes)
    for entry in sorted(resulting_files, key=lambda item: item["path"].encode("utf-8")):
        for value in (entry["path"].encode("utf-8"), entry["content"].encode("utf-8")):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return digest.hexdigest()


def _evidence(
    *,
    proposal_bytes: bytes,
    resulting_files: list[dict[str, str]],
    reviewed_at: str = "2026-08-03T12:34:56Z",
) -> dict[str, object]:
    return {
        "reviewer_identity": "fable",
        "reviewer_model": "fable",
        "separate_reviewer": True,
        "read_only": True,
        "reviewed_at": reviewed_at,
        "verdict": "NO BLOCKERS",
        "proposal_stem": "demo",
        "content_digest": _contract_digest(
            proposal_bytes=proposal_bytes,
            resulting_files=resulting_files,
        ),
    }


def _write_proposal(*, tmp_path: Path, proposal_bytes: bytes) -> Path:
    spec_target = tmp_path / "SPECIFICATION"
    proposal_path = spec_target / "proposed_changes" / "demo.md"
    proposal_path.parent.mkdir(parents=True)
    proposal_path.write_bytes(proposal_bytes)
    return spec_target


def _proposal_bytes(*, created_at: str) -> bytes:
    return (
        "---\n"
        "topic: demo\n"
        "author: Human <human@example.com>\n"
        f"created_at: {created_at}\n"
        "---\n"
        "## Proposal\n"
        "Review me.\n"
    ).encode()


def _mutating_input(
    *,
    resulting_files: list[dict[str, str]],
    proposal_bytes: bytes,
    mode: str = "auto-spawn",
    evidence: dict[str, object] | None | object = _DEFAULT_EVIDENCE,
) -> RevisionInput:
    decision: dict[str, object] = {
        "proposal_topic": "demo",
        "decision": "accept",
        "rationale": ".",
        "resulting_files": resulting_files,
        "ratification_review": mode,
    }
    if evidence is _DEFAULT_EVIDENCE:
        decision["ratification_evidence"] = _evidence(
            proposal_bytes=proposal_bytes,
            resulting_files=resulting_files,
        )
    elif evidence is not None:
        decision["ratification_evidence"] = evidence
    return RevisionInput(author=None, decisions=[decision])


def test_ratification_errors_module_is_a_leaf() -> None:
    """The extracted error builders must not import back into their parent.

    `_digest_error` stayed in `_revise_ratification` precisely because it
    needs `_canonical_ratification_digest`; if a later edit moves it — or
    any other parent-dependent helper — into the errors module, the two
    modules form an import cycle. Nothing else would catch that: the cycle
    is legal Python and only bites at import order.
    """
    source = (
        Path(__file__).resolve().parents[3]
        / ".claude-plugin"
        / "scripts"
        / "livespec"
        / "commands"
        / "_revise_ratification_errors.py"
    ).read_text(encoding="utf-8")
    assert "_revise_ratification import" not in source, (
        "the errors module must not import from its parent; keeping it a leaf "
        "is what prevents an import cycle between the two"
    )
    assert "_canonical_ratification_digest" not in source, (
        "the canonical-digest helper is the parent's public surface; depending "
        "on it here would create the cycle this extraction avoided"
    )
