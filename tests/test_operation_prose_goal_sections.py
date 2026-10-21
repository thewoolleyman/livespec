"""Contract-conformance test for the Goal section every operation prose opens with.

`SPECIFICATION/spec.md` makes the core-owned operation prose under
`.claude-plugin/prose/<name>.md` the artifact that orchestrates each
operation. A reader — human or agent — reaching one of
those files must learn the operation's FINISH CONDITION before it reads
the flow that pursues it, so the prose opens with a `## Goal` section
stating what the operation must leave true when it ends.

The section carries two things, and the second is the one that is easy
to lose: the finish condition itself, and the statement that a rejected
or refused path is INCOMPLETE WORK rather than a finish. Without the
second, an operation that aborts at a precondition reads as having run
to completion, which is exactly the misreport the Goal section exists
to prevent.

This test asserts core's shipped prose honors that shape. The file set is
derived from the `prose/` directory rather than from a hardcoded list, so
a prose artifact added for a new operation is covered the moment it ships.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROSE_DIR = _REPO_ROOT / ".claude-plugin" / "prose"

_GOAL_HEADING = "## Goal"
# The flow sections: the dialogue-entry condition, the inputs the flow
# consumes, and the numbered steps themselves. The Goal must precede
# every one of them, so the finish condition is read before the flow.
_FLOW_HEADINGS = ("## When to run", "## Inputs", "## Steps")

_H2_RE = re.compile(r"^## .*$", re.MULTILINE)
_GOAL_SECTION_RE = re.compile(r"^## Goal$(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)

# The finish condition must NAME what the operation leaves true, not
# merely gesture at success, so the section carries an explicit
# leaves-true clause.
_LEAVES_TRUE_PHRASE = "MUST leave"
# The not-a-finish clause, spelled identically across every operation so
# a reader who has learned it in one prose recognizes it in the next.
_NOT_A_FINISH_PHRASE = "INCOMPLETE WORK, not a finish"
# At least one of these must name the path the clause covers: the
# operation refusing, or a decision/invocation being rejected.
_REFUSAL_WORDS = ("refus", "reject")


def _prose_paths() -> list[Path]:
    return sorted(_PROSE_DIR.glob("*.md"))


def _h2_headings(*, path: Path) -> list[str]:
    return [match.group(0).rstrip() for match in _H2_RE.finditer(path.read_text(encoding="utf-8"))]


def _goal_body(*, path: Path) -> str:
    """Return the Goal section's body with every whitespace run collapsed.

    The prose is hard-wrapped, so a contract phrase spans line breaks;
    collapsing whitespace makes the substring assertions robust to
    rewrapping without weakening them.
    """
    match = _GOAL_SECTION_RE.search(path.read_text(encoding="utf-8"))
    return "" if match is None else re.sub(r"\s+", " ", match.group("body")).strip()


def test_prose_directory_ships_operation_artifacts() -> None:
    """Guard the derivation: an empty glob would make every case below vacuous."""
    paths = _prose_paths()
    assert paths, f"no operation prose artifacts found under {_PROSE_DIR}"


@pytest.mark.parametrize("prose_path", _prose_paths(), ids=lambda path: path.stem)
def test_goal_is_the_first_section_of_every_operation_prose(*, prose_path: Path) -> None:
    headings = _h2_headings(path=prose_path)
    assert headings, (
        f"{prose_path.relative_to(_REPO_ROOT)} carries no `## ` section at all, "
        f"so it cannot open with {_GOAL_HEADING!r}"
    )
    assert headings[0] == _GOAL_HEADING, (
        f"{prose_path.relative_to(_REPO_ROOT)} must open with {_GOAL_HEADING!r} so the "
        f"operation's finish condition is stated before its flow; its first section "
        f"is {headings[0]!r}"
    )


@pytest.mark.parametrize("prose_path", _prose_paths(), ids=lambda path: path.stem)
def test_goal_precedes_every_flow_section(*, prose_path: Path) -> None:
    headings = _h2_headings(path=prose_path)
    goal_index = headings.index(_GOAL_HEADING) if _GOAL_HEADING in headings else -1
    assert (
        goal_index != -1
    ), f"{prose_path.relative_to(_REPO_ROOT)} is missing a {_GOAL_HEADING!r} section"
    for flow_heading in _FLOW_HEADINGS:
        if flow_heading not in headings:
            continue
        assert goal_index < headings.index(flow_heading), (
            f"{prose_path.relative_to(_REPO_ROOT)} states {flow_heading!r} before "
            f"{_GOAL_HEADING!r}; the finish condition must come first"
        )


@pytest.mark.parametrize("prose_path", _prose_paths(), ids=lambda path: path.stem)
def test_goal_names_what_the_operation_must_leave_true(*, prose_path: Path) -> None:
    body = _goal_body(path=prose_path)
    assert body, f"{prose_path.relative_to(_REPO_ROOT)} has an empty {_GOAL_HEADING!r} section"
    assert _LEAVES_TRUE_PHRASE in body, (
        f"{prose_path.relative_to(_REPO_ROOT)}'s Goal section must name what the "
        f"operation leaves true when it ends via a {_LEAVES_TRUE_PHRASE!r} clause; "
        f"a bare restatement of the operation's purpose is not a finish condition"
    )


@pytest.mark.parametrize("prose_path", _prose_paths(), ids=lambda path: path.stem)
def test_goal_reports_a_refused_path_as_incomplete_work(*, prose_path: Path) -> None:
    body = _goal_body(path=prose_path)
    assert body, f"{prose_path.relative_to(_REPO_ROOT)} has an empty {_GOAL_HEADING!r} section"
    assert _NOT_A_FINISH_PHRASE in body, (
        f"{prose_path.relative_to(_REPO_ROOT)}'s Goal section must state that a rejected "
        f"or refused path is {_NOT_A_FINISH_PHRASE!r}, so an operation that aborts is "
        f"never narrated as having finished"
    )
    assert any(word in body.lower() for word in _REFUSAL_WORDS), (
        f"{prose_path.relative_to(_REPO_ROOT)}'s not-a-finish clause must name the "
        f"rejected or refused path it covers; found none of {_REFUSAL_WORDS}"
    )
