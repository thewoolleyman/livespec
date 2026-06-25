"""Single-source-of-truth guard for the canonical architecture diagram.

`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture" is the ONE home of the canonical Mermaid architecture
diagram; the repo `README.md` references that section and never embeds
a second copy (per the repo's architecture-diagram authoring
conventions — no duplication, no drift). This test asserts that
invariant: the canonical section carries the diagram, the README points
at it, and the README embeds no Mermaid block of its own.
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "SPECIFICATION" / "spec.md"
_README = _REPO_ROOT / "README.md"

_CANONICAL_HEADING = "## Contract + reference implementations architecture"
_MERMAID_FENCE = "```mermaid"


def _canonical_section() -> str:
    """The spec.md text from the canonical H2 up to (not incl.) the next H2."""
    text = _SPEC.read_text(encoding="utf-8")
    start = text.find(_CANONICAL_HEADING)
    assert start != -1, f"spec.md is missing the canonical heading {_CANONICAL_HEADING!r}"
    rest = text[start + len(_CANONICAL_HEADING) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_canonical_diagram_lives_in_the_spec_section() -> None:
    assert _MERMAID_FENCE in _canonical_section(), (
        "the canonical architecture Mermaid diagram must live in spec.md "
        f"§{_CANONICAL_HEADING!r}"
    )


def test_readme_references_the_canonical_section() -> None:
    readme = _README.read_text(encoding="utf-8")
    assert (
        "Contract + reference implementations architecture" in readme
    ), "README.md must reference the canonical architecture section, not duplicate it"


def test_readme_embeds_no_mermaid_diagram() -> None:
    readme = _README.read_text(encoding="utf-8")
    assert _MERMAID_FENCE not in readme, (
        "README.md must not embed a Mermaid block — the canonical architecture "
        "diagram is single-sourced in SPECIFICATION/spec.md and referenced, never copied"
    )
