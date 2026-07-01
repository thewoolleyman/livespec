"""Single-source-of-truth guard for the canonical *architecture* diagram.

`SPECIFICATION/spec.md` — its Contract + reference implementations
architecture section — is the ONE home of the canonical Mermaid ARCHITECTURE
diagram; the repo
`README.md` references that section and never embeds a second copy OF THE
ARCHITECTURE DIAGRAM (per the repo's architecture-diagram authoring
conventions — no duplication, no drift for that one diagram).

The narrowed invariant: only the canonical architecture diagram is
single-sourced. The README MAY still embed OTHER, non-architecture Mermaid
diagrams — e.g. the human-readable work-item-lifecycle `stateDiagram-v2` — so
this guard forbids a DUPLICATE of the architecture diagram, not all Mermaid.

This test asserts that: the canonical section carries the diagram, the README
points at it, and no Mermaid block the README embeds reproduces the
architecture diagram's distinguishing signature (its three named planes).
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "SPECIFICATION" / "spec.md"
_README = _REPO_ROOT / "README.md"

_CANONICAL_HEADING = "## Contract + reference implementations architecture"
_MERMAID_FENCE = "```mermaid"

# The canonical architecture diagram is structured as three named planes,
# rendered as Mermaid subgraphs. Those plane names are its distinguishing
# signature: they appear in the spec.md architecture diagram and in NO other
# livespec diagram (the lifecycle stateDiagram uses none of them), so a README
# Mermaid block that reproduces any of them is a copy of the architecture
# diagram — exactly what this guard forbids. Matched case-insensitively: the
# spec renders them upper-case ("SPEC PLANE") while the authoring convention
# titles them ("Spec Plane"), so a re-cased copy cannot slip through.
_ARCHITECTURE_PLANE_SIGNATURE = ("spec plane", "orchestrator plane", "control plane")


def _canonical_section() -> str:
    """The spec.md text from the canonical H2 up to (not incl.) the next H2."""
    text = _SPEC.read_text(encoding="utf-8")
    start = text.find(_CANONICAL_HEADING)
    assert start != -1, f"spec.md is missing the canonical heading {_CANONICAL_HEADING!r}"
    rest = text[start + len(_CANONICAL_HEADING) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _mermaid_blocks(markdown: str) -> list[str]:
    """Return the body text of every ```mermaid fenced block in `markdown`."""
    blocks: list[str] = []
    current: list[str] | None = None
    for line in markdown.splitlines():
        if current is None:
            if line.strip().startswith(_MERMAID_FENCE):
                current = []
        elif line.strip() == "```":
            blocks.append("\n".join(current))
            current = None
        else:
            current.append(line)
    return blocks


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


def test_architecture_plane_signature_identifies_the_canonical_diagram() -> None:
    # Guard the guard: the plane names the duplicate check below keys on MUST
    # actually be present in the canonical architecture diagram, else that
    # check silently rots into a rubber stamp when the diagram is reworded.
    section = _canonical_section().lower()
    for token in _ARCHITECTURE_PLANE_SIGNATURE:
        assert token in section, (
            f"the canonical architecture diagram no longer contains {token!r}; "
            "update _ARCHITECTURE_PLANE_SIGNATURE to its current plane labels"
        )


def test_readme_does_not_duplicate_architecture_diagram() -> None:
    for block in _mermaid_blocks(_README.read_text(encoding="utf-8")):
        lowered = block.lower()
        reproduced = [token for token in _ARCHITECTURE_PLANE_SIGNATURE if token in lowered]
        assert not reproduced, (
            "README.md must not embed a copy of the canonical architecture "
            "diagram — it is single-sourced in SPECIFICATION/spec.md "
            f"§{_CANONICAL_HEADING!r} and referenced, never copied. A README "
            f"Mermaid block reproduces its plane signature {reproduced!r}. "
            "(Non-architecture diagrams — e.g. the work-item-lifecycle "
            "stateDiagram — MAY be embedded in the README.)"
        )
