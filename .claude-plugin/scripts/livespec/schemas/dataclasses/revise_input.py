"""Dataclass paired with `revise_input.schema.json`.

Represents the parsed JSON payload from the active template's
`prompts/revise.md` that `bin/revise.py` consumes via
`--revise-json`. Per PROPOSAL.md §"revise" lines 2365-2400.

`ResultingFile` is the inlined `{path, content}` shape. It is
intentionally a separate type from `SeedFile` and `SubSpecFile`
so schema-validation drift between the three wire-protocol leaves
is detected by `check-schema-dataclass-pairing`.

Three-way pairing with `revise_input.schema.json` and
`validate/revise_input.py`.
"""

from dataclasses import dataclass, field
from typing import Literal

from livespec.types import Author, TopicSlug

__all__: list[str] = [
    "Decision",
    "ProposalDecision",
    "ResultingFile",
    "ReviseInput",
]


Decision = Literal["accept", "modify", "reject"]


def _empty_resulting_files() -> list["ResultingFile"]:
    """Default factory for `ProposalDecision.resulting_files`. Returns
    a fresh empty list per instance (reject decisions, or accept/modify
    with no file changes)."""
    return []


@dataclass(frozen=True, kw_only=True, slots=True)
class ResultingFile:
    path: str
    content: str


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposalDecision:
    proposal_topic: TopicSlug
    decision: Decision
    rationale: str
    modifications: str | None = None
    resulting_files: list[ResultingFile] = field(
        default_factory=_empty_resulting_files,
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class ReviseInput:
    decisions: list[ProposalDecision]
    author: Author | None = None
