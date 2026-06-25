"""Contract-conformance test for the doctor per-finding disposition dialogue.

`SPECIFICATION/contracts.md` §"Doctor per-finding disposition dialogue"
mandates that the `doctor` operation prose — which core ships at
`.claude-plugin/prose/doctor.md` and the active Driver binding executes
— offers a per-finding disposition menu of at minimum FIVE options in a
fixed canonical order, always-offers two of them, and runs the dialogue
before the wrapper's Exit 3 abort and for `warn` findings too. This test
asserts core's shipped prose honors that contract (it guards against the
prose drifting back to the earlier three-option menu).
"""

from __future__ import annotations

import re
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCTOR_PROSE = _REPO_ROOT / ".claude-plugin" / "prose" / "doctor.md"

# The disposition menu renders each option in bold; the bold form is
# unique to the menu (the bare names also appear as CLI/operation names
# elsewhere in the prose), so anchoring on the bold token scopes the
# canonical-order assertion to the menu itself.
_CANONICAL_OPTIONS = (
    "**fix-now**",
    "**capture-as-work-item**",
    "**propose-change**",
    "**defer**",
    "**dismiss**",
)


def _prose() -> str:
    # The prose is hard-wrapped, so contract phrases like "MUST ALWAYS be
    # offered" span line breaks. Collapse every whitespace run to a single
    # space so substring assertions are robust to wrapping. Bold option
    # tokens carry no internal spaces, so their relative order is preserved.
    return re.sub(r"\s+", " ", _DOCTOR_PROSE.read_text(encoding="utf-8"))


def test_disposition_menu_lists_five_canonical_options_in_order() -> None:
    prose = _prose()
    indices: list[int] = []
    for option in _CANONICAL_OPTIONS:
        position = prose.find(option)
        assert position != -1, f"doctor disposition menu is missing option {option}"
        indices.append(position)
    assert indices == sorted(indices), (
        "doctor disposition menu options are out of canonical order: "
        f"{_CANONICAL_OPTIONS} resolved to positions {indices}"
    )


def test_capture_and_propose_change_are_always_offered() -> None:
    prose = _prose()
    # Both options carry an explicit always-offered guarantee in the contract.
    assert "capture-as-work-item" in prose
    assert "propose-change" in prose
    assert (
        prose.count("MUST ALWAYS be offered") >= 2
    ), "capture-as-work-item and propose-change must each be marked always-offered"


def test_dialogue_runs_before_exit_3_and_for_warn_findings() -> None:
    prose = _prose()
    assert "Exit 3" in prose, "the dialogue's run-before-abort timing must reference Exit 3"
    assert "warn" in prose, "the dialogue must state it runs for warn findings too"
