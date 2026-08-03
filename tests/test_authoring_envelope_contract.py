"""Contract guards for authoring invocation-envelope threading.

The spec-governance authoring envelope is intentionally a prose /
LLM-layer input. These tests keep the shipped operation prose and
built-in prompt input contracts aligned with that boundary: complete
safe envelopes suppress only answered questions, unsafe envelopes
escalate before mutation, journal metadata is written before wrapper
invocation, and Python mutation wrappers remain envelope-unaware.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROSE_DIR = _REPO_ROOT / ".claude-plugin" / "prose"
_TEMPLATE_DIR = _REPO_ROOT / ".claude-plugin" / "specification-templates"
_COMMANDS_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "livespec" / "commands"


def _normalized(*, path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_propose_change_prose_consumes_complete_batch_envelope() -> None:
    prose = _normalized(path=_PROSE_DIR / "propose-change.md")
    required = (
        "mode: interactive | batch",
        "`intent` and `topic` MUST both be non-empty",
        "suppresses only this question; interactive mode still asks every other unanswered",
        "one relationship unless `effective_in_flight_alignment` resolves to `default-align`",
        "`default-align` MAY satisfy only compatible alignment",
        "MUST NOT mask genuine conflict, partial supersession, or full supersession",
    )
    missing = [fragment for fragment in required if fragment not in prose]
    assert not missing, f"propose-change prose lost envelope contract fragments: {missing!r}"


def test_propose_change_prose_escalates_unsafe_envelopes_before_writes() -> None:
    prose = _normalized(path=_PROSE_DIR / "propose-change.md")
    required = (
        "internally contradictory input, ambiguity, design-record conflict",
        "escalates immediately and leaves the spec tree unchanged",
        "journal append fails, escalate before mutation and do not invoke the wrapper",
        "envelope omits a required relationship, asks to modify or supersede an item",
    )
    missing = [fragment for fragment in required if fragment not in prose]
    assert not missing, f"propose-change prose lost unsafe/no-write fragments: {missing!r}"


def test_critique_prose_consumes_exact_target_from_batch_envelope() -> None:
    prose = _normalized(path=_PROSE_DIR / "critique.md")
    required = (
        "MAY carry `mode: interactive | batch`, `spec_target`, and `target`",
        "Effective batch mode MUST carry a non-empty `target`, using this exact field name",
        "supplied non-empty `target`",
        "suppresses only this question; interactive mode still asks every other unanswered",
        "against the user-described or envelope-supplied target",
    )
    missing = [fragment for fragment in required if fragment not in prose]
    assert not missing, f"critique prose lost exact-target envelope fragments: {missing!r}"


def test_authoring_journal_precedes_wrapper_invocation_and_payload_is_digest_only() -> None:
    for filename, step in (("propose-change.md", "Step 8"), ("critique.md", "Step 7")):
        prose = _normalized(path=_PROSE_DIR / filename)
        journal_index = prose.find(
            "append a digest-only `authoring_auto_consumption` journal event"
        )
        wrapper_index = prose.find(f"before {step} invokes")
        assert journal_index != -1, f"{filename} lacks digest-only journal instruction"
        assert wrapper_index != -1, f"{filename} lacks journal-before-wrapper timing"
        assert journal_index < wrapper_index, f"{filename} does not state journal before wrapper"
        assert "never raw `intent`, `topic`, `target`, or the raw envelope body" in prose


def test_authoring_envelope_never_reaches_python_mutation_wrappers() -> None:
    for filename, wrapper_name in (
        ("propose-change.md", "bin/propose_change.py"),
        ("critique.md", "bin/critique.py"),
    ):
        prose = _normalized(path=_PROSE_DIR / filename)
        assert f"MUST NOT be passed to `{wrapper_name}`" in prose
        assert "Do not forward the invocation envelope, envelope digest" in prose
    for command in ("propose_change.py", "critique.py"):
        source = (_COMMANDS_DIR / command).read_text(encoding="utf-8")
        assert "--input-envelope" not in source
        assert "input_envelope" not in source
        assert "envelope" not in source


def test_built_in_prompt_inputs_expose_supplied_values() -> None:
    prompt_paths = (
        _TEMPLATE_DIR / "minimal" / "prompts" / "propose-change.md",
        _TEMPLATE_DIR / "livespec" / "prompts" / "propose-change.md",
    )
    for path in prompt_paths:
        text = _normalized(path=path)
        assert "exact non-empty `intent` supplied by a complete invocation envelope" in text
        assert "topic identifier supplied by dialogue or by a complete invocation envelope" in text
        assert "safely resolved as compatible default alignment by operation prose" in text


def test_built_in_critique_prompt_inputs_expose_supplied_target() -> None:
    prompt_paths = (
        _TEMPLATE_DIR / "minimal" / "prompts" / "critique.md",
        _TEMPLATE_DIR / "livespec" / "prompts" / "critique.md",
    )
    for path in prompt_paths:
        text = _normalized(path=path)
        assert "complete invocation envelope's non-empty `target` field" in text
        assert "consume it as the critique target" in text
        assert "do not reinterpret it as a broader search request" in text
