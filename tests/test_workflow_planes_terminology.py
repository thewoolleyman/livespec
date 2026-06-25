"""Terminology guard for the Spec / Orchestrator / Control planes.

`SPECIFICATION/spec.md` §"Workflow planes and the Planning Lane" carries
the load-bearing terminology guard of that section: the operator console
is the **Control Plane / operator cockpit** and is NEVER a "Driver"
("Driver" already names the per-agent-runtime binding —
`livespec-driver-claude`, `livespec-driver-codex`). The section is
otherwise descriptive architectural framing; this guard is its one
normative imperative ("Keep the two distinct in all prose and
diagrams").

This test pins the guard on core's own spec so that prose/diagram drift
which conflates the console with the Driver — or deletes the guard —
fails mechanically. It asserts on core's authored artifact, not on a
mock, per the maintainer directive to test each heading here or relocate
it (livespec-besm.5).
"""

from __future__ import annotations

import re
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "SPECIFICATION" / "spec.md"

_PLANES_HEADING = "## Workflow planes and the Planning Lane"

# The three plane names the section establishes; conflating them "is the
# recurring design error" the section calls out.
_PLANE_NAMES = ("Spec Plane", "Orchestrator Plane", "Control Plane")

# The normative terminology-guard clauses, pinned verbatim.
_GUARD_CLAUSES = (
    'The console is NOT a "Driver."',
    "Control Plane / operator cockpit",
    "Keep the two distinct in all prose and diagrams.",
)

# Tokens that mark a Mermaid subgraph label as the operator-console /
# Control-Plane role (case-insensitive). A subgraph carrying any of these
# MUST NOT also call itself a Driver.
_CONSOLE_LABEL_TOKENS = ("control plane", "operator console", "operator cockpit")

# Matches a Mermaid `subgraph <id>["<label>"]` declaration, capturing the label.
_SUBGRAPH_LABEL = re.compile(r'subgraph\s+\S+\["([^"]+)"\]')


def _planes_section() -> str:
    """The spec.md text from the planes H2 up to (not incl.) the next H2."""
    text = _SPEC.read_text(encoding="utf-8")
    start = text.find(_PLANES_HEADING)
    assert start != -1, f"spec.md is missing the planes heading {_PLANES_HEADING!r}"
    rest = text[start + len(_PLANES_HEADING) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_planes_section_names_all_three_planes() -> None:
    """The section names the Spec, Orchestrator, and Control planes."""
    section = _planes_section()
    for plane in _PLANE_NAMES:
        assert plane in section, (
            f"spec.md §{_PLANES_HEADING!r} must name the {plane!r}; the three "
            "planes are the section's load-bearing vocabulary"
        )


def test_terminology_guard_present() -> None:
    """The console-is-not-a-Driver terminology guard is stated verbatim."""
    section = _planes_section()
    for clause in _GUARD_CLAUSES:
        assert clause in section, (
            f"spec.md §{_PLANES_HEADING!r} must carry the terminology-guard "
            f"clause {clause!r}; the console is the Control Plane / operator "
            "cockpit, never a Driver"
        )


def test_diagrams_keep_console_distinct_from_driver() -> None:
    """No Mermaid subgraph in spec.md labels the console a Driver, and a
    distinct DRIVER subgraph is rendered.

    The structural realization of the terminology guard: across every
    Mermaid diagram authored in spec.md, a subgraph whose label marks it
    as the operator console / Control Plane MUST NOT also contain the
    word "Driver" — and the canonical architecture diagram keeps the
    Driver as its own separate subgraph, so the two roles are visibly
    distinct rather than merely both absent.
    """
    spec_text = _SPEC.read_text(encoding="utf-8")
    labels = _SUBGRAPH_LABEL.findall(spec_text)
    assert labels, "spec.md must author at least one Mermaid subgraph diagram"

    for label in labels:
        lowered = label.lower()
        if any(token in lowered for token in _CONSOLE_LABEL_TOKENS):
            assert "driver" not in lowered, (
                f"Mermaid subgraph label {label!r} marks the operator console "
                "/ Control Plane yet calls itself a Driver; the console is NOT "
                "a Driver (spec.md terminology guard)"
            )

    assert any("driver" in label.lower() for label in labels), (
        "spec.md's canonical architecture diagram must keep the Driver as its "
        "own subgraph, distinct from the Control-Plane console"
    )
