"""Single-source-of-truth guard for the tool-agnostic *lifecycle* diagram.

`SPECIFICATION/spec.md` — its "Tool-agnostic workflow — spec /
implementation lifecycle" section — is the ONE home of the top-level
lifecycle/dataflow Mermaid diagram; the repo `README.md` references that
section by anchor and never embeds a second copy OF THE LIFECYCLE DIAGRAM
("Single-sourced in the spec and referenced here, never copied" — the
README's own framing).

Sibling of `test_architecture_diagram_single_source.py`, same narrowed
invariant: only THIS diagram is guarded; the README MAY embed other,
non-architecture Mermaid diagrams (e.g. the work-item-lifecycle
`stateDiagram-v2`). The three plane names cannot serve as the signature
here — the lifecycle diagram deliberately shares them with the canonical
architecture diagram (the different-zoom-levels exception) — so this guard
keys on labels unique to the lifecycle/dataflow view.

Covers the `## Tool-agnostic workflow — spec / implementation lifecycle`
entry in `tests/heading-coverage.json` (the section is diagram + caption
only, carrying no MUST/SHOULD behavior clause; single-sourcing is its
testable discipline).
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "SPECIFICATION" / "spec.md"
_README = _REPO_ROOT / "README.md"

_LIFECYCLE_HEADING = "## Tool-agnostic workflow — spec / implementation lifecycle"
_LIFECYCLE_README_ANCHOR = "#tool-agnostic-workflow--spec--implementation-lifecycle"
_MERMAID_FENCE = "```mermaid"

# The lifecycle diagram's distinguishing signature. The plane names are
# unusable here (shared with the canonical architecture diagram by the
# deliberate different-zoom-levels exception), so the signature is two
# labels that exist ONLY in the lifecycle/dataflow view: the intent
# entry node and the Dispatcher's parallelism caption. Matched
# case-insensitively so a re-cased copy cannot slip through.
_LIFECYCLE_SIGNATURE = (
    "initial intent / prompt / instruction",
    "dispatcher: owns parallelism",
)


def _lifecycle_section() -> str:
    """The spec.md text from the lifecycle H2 up to (not incl.) the next H2."""
    text = _SPEC.read_text(encoding="utf-8")
    start = text.find(_LIFECYCLE_HEADING)
    assert start != -1, f"spec.md is missing the lifecycle heading {_LIFECYCLE_HEADING!r}"
    rest = text[start + len(_LIFECYCLE_HEADING) :]
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


def test_lifecycle_diagram_lives_in_the_spec_section() -> None:
    assert _MERMAID_FENCE in _lifecycle_section(), (
        "the tool-agnostic lifecycle Mermaid diagram must live in spec.md "
        f"§{_LIFECYCLE_HEADING!r}"
    )


def test_readme_references_the_lifecycle_section() -> None:
    readme = _README.read_text(encoding="utf-8")
    assert _LIFECYCLE_README_ANCHOR in readme, (
        "README.md must reference the lifecycle section by anchor "
        f"({_LIFECYCLE_README_ANCHOR!r}), not duplicate it"
    )


def test_lifecycle_signature_identifies_the_diagram() -> None:
    # Guard the guard: the labels the duplicate check below keys on MUST
    # actually be present in the lifecycle diagram, else that check
    # silently rots into a rubber stamp when the diagram is reworded.
    section = _lifecycle_section().lower()
    for token in _LIFECYCLE_SIGNATURE:
        assert token in section, (
            f"the lifecycle diagram no longer contains {token!r}; update "
            "_LIFECYCLE_SIGNATURE to its current distinguishing labels"
        )


def test_readme_does_not_duplicate_lifecycle_diagram() -> None:
    for block in _mermaid_blocks(_README.read_text(encoding="utf-8")):
        lowered = block.lower()
        reproduced = [token for token in _LIFECYCLE_SIGNATURE if token in lowered]
        assert not reproduced, (
            "README.md must not embed a copy of the tool-agnostic lifecycle "
            "diagram — it is single-sourced in SPECIFICATION/spec.md "
            f"§{_LIFECYCLE_HEADING!r} and referenced, never copied. A README "
            f"Mermaid block reproduces its signature {reproduced!r}."
        )
