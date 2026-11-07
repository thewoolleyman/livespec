"""The shared judgement of whether a behaviour is stated by the ratified spec.

A SHARED-RUNTIME contract: `livespec` core names no slot for this judgement, and
both consuming producers — `livespec-orchestrator-beads-fabro` and
`livespec-orchestrator-git-jsonl` — run the SAME one. Defining it once is the
whole point: the prompt, the inputs, the verdict schema, the parser and the
persisted tier fields all live here, so two orchestrators cannot drift into two
different judgements of the same question.

The module reaches a model ONLY through the `run_model` callable its caller
supplies. It opens no subprocess, no socket and no network connection of its
own and holds no credential, so the library stays model-agnostic and every
provider binding — and every secret — stays in the consumer.

Two points the ratified contract leaves open, decided here and NOT invented
into validation:

- `generalization_target` is validated as a string or `None`, not as a heading
  present in the spec tree. Only `stated_by` is pinned to the tree by
  `contracts.md`, so refusing a target the ratified text does not refuse would
  make this parser stricter than the contract it implements.
- a `kind`/`stated_by` disagreement (an `unstated` verdict naming a heading, a
  `stated` one naming none) is carried through rather than refused, for the
  same reason: `contracts.md` describes `stated_by` as empty for `unstated`
  without making that a requirement the parser may enforce.

Both are reported to the maintainer as underspecification findings rather than
closed by this module's own reading.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

from returns.result import Failure, Result, Success

__all__: list[str] = [
    "CLASSIFY_PROMPT",
    "JUDGE_PROMPT",
    "ItemClass",
    "ModelRunner",
    "SpecChangeTier",
    "SpecStatedParseError",
    "SpecStatedVerdict",
    "StatedKind",
    "classify",
    "judge",
    "parse_verdict",
]

StatedKind: TypeAlias = Literal["stated", "partial", "unstated"]
ItemClass: TypeAlias = Literal["feature", "bug", "chore", "non_functional"]
ModelRunner: TypeAlias = Callable[[str], str]

_STATED_KINDS: tuple[StatedKind, ...] = ("stated", "partial", "unstated")
_ITEM_CLASSES: tuple[ItemClass, ...] = ("feature", "bug", "chore", "non_functional")
_REQUIRED_VERDICT_FIELDS = ("kind", "stated_by", "generalization_target", "rationale")

# One H2 heading line, captured WITH its leading `## ` marker, because that
# marker is part of the heading text the prompt asks the model to copy out and
# therefore part of what `stated_by` carries. `##` followed by a third `#` is
# an H3 and is not matched: the governing clause set is the H2 set.
_H2_HEADING = re.compile(r"^(##[ \t][^\n]*?)[ \t]*$", re.MULTILINE)

JUDGE_PROMPT: str = """You are judging ONE behaviour statement against a RATIFIED specification.

The specification tree follows, one block per file:

{spec_tree}

The behaviour statement under judgement:

{statement}

Decide whether the ratified text above STATES that behaviour, and name the
clause that states it. Reply with ONE JSON object and nothing else:

{{"kind": "stated" | "partial" | "unstated",
  "stated_by": ["## Verbatim H2 heading", "..."],
  "generalization_target": "## Verbatim H2 heading" or null,
  "rationale": "one or two sentences"}}

Rules:

- "stated" means the ratified text states the behaviour in full; "partial"
  means it states part of it; "unstated" means it does not state it.
- "stated_by" names EVERY governing H2 heading, VERBATIM and including its
  leading "## " marker, copied from the tree above. It is empty for "unstated".
- Name no heading that is absent from the tree above: an invented heading is
  refused rather than parsed.
- "generalization_target" names the one EXISTING H2 heading whose
  generalization would state the behaviour, or is null when none would.
"""

CLASSIFY_PROMPT: str = """Classify ONE work item into exactly one class.

Title: {title}

Description: {description}

Stored type, as EVIDENCE only: {item_type}

The stored type is whatever a human or an orchestrator happened to record, so
it is evidence ABOUT the item and never the answer. Weigh it against the title
and the description, and disagree with it when they say otherwise.

Reply with exactly one of these four words and nothing else:

feature — new observable behaviour.
bug — behaviour that contradicts what is already stated.
chore — work that changes no observable behaviour.
non_functional — a constraint on HOW the system behaves rather than on what it
does.
"""


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecStatedVerdict:
    """One judgement: whether the spec states a behaviour, and by which clause.

    `stated_by` carries the verbatim text of each governing H2 heading, its
    leading `## ` marker included, and is empty for an `unstated` verdict.
    `generalization_target` names the one existing heading whose generalization
    would state the behaviour, or is `None`.
    """

    kind: StatedKind
    stated_by: tuple[str, ...]
    generalization_target: str | None
    rationale: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecChangeTier:
    """The spec-change tier both orchestrators persist on a work-item.

    `tier` and `linked_proposal_topic` are the two persisted fields a consumer
    stores; `verdict` keeps the judgement they were derived from, and
    `judged_at` is an ISO-8601 UTC timestamp.
    """

    tier: Literal["spec-change", "none"]
    linked_proposal_topic: str | None
    verdict: SpecStatedVerdict | None
    judged_at: str


class SpecStatedParseError(Exception):
    """A model response this module could not read as a judgement.

    Returned as the `Failure` payload of `judge`, `classify` and
    `parse_verdict` — never raised. Inherits `Exception` directly: consumers
    catch this domain type, never a builtin ancestor.

    `field` names the offending JSON field, and is `None` when the response is
    not JSON at all.
    """

    def __init__(self, *, field: str | None, detail: str) -> None:
        super().__init__(detail)
        self.field = field
        self.detail = detail


def _rendered_spec_tree(*, spec_tree: Mapping[str, str]) -> str:
    """The spec tree rendered into the prompt: one block per path, in path order."""
    return "\n\n".join(f"--- {path} ---\n{spec_tree[path]}" for path in sorted(spec_tree))


def _governing_headings(*, spec_tree: Mapping[str, str]) -> tuple[str, ...]:
    """Every H2 heading the spec tree carries, verbatim and marker included.

    This is the clause set a verdict may cite, derived from the tree itself
    rather than trusted from the response: a heading the tree does not carry is
    a clause nobody can open, and a consumer would file a proposal against it.
    """
    return tuple(
        heading for path in sorted(spec_tree) for heading in _H2_HEADING.findall(spec_tree[path])
    )


def _stated_by(
    *, value: object, headings: Collection[str]
) -> Result[tuple[str, ...], SpecStatedParseError]:
    """The governing headings a response names, refused when they are not the tree's.

    A heading the tree does not carry is refused rather than carried: a verdict
    citing a clause that does not exist is worse than no verdict, because a
    consumer would file a proposal against it.
    """
    if not isinstance(value, list):
        return Failure(
            SpecStatedParseError(
                field="stated_by", detail=f"stated_by is not a list of headings: {value!r}"
            )
        )
    entries = cast("list[object]", value)
    if not all(isinstance(entry, str) for entry in entries):
        return Failure(
            SpecStatedParseError(
                field="stated_by", detail=f"stated_by names a non-string heading: {entries!r}"
            )
        )
    absent = [entry for entry in entries if entry not in headings]
    if absent:
        return Failure(
            SpecStatedParseError(
                field="stated_by",
                detail=f"stated_by names headings the spec tree does not carry: {absent!r}",
            )
        )
    return Success(tuple(cast("list[str]", entries)))


def _verdict_from(
    *, payload: Mapping[str, object], headings: Collection[str]
) -> Result[SpecStatedVerdict, SpecStatedParseError]:
    """One verdict out of a response whose required fields are all present."""
    kind = payload["kind"]
    if kind not in _STATED_KINDS:
        return Failure(
            SpecStatedParseError(
                field="kind", detail=f"kind is not one of {_STATED_KINDS}: {kind!r}"
            )
        )
    target = payload["generalization_target"]
    if target is not None and not isinstance(target, str):
        return Failure(
            SpecStatedParseError(
                field="generalization_target",
                detail=f"generalization_target is neither a heading nor null: {target!r}",
            )
        )
    rationale = payload["rationale"]
    if not isinstance(rationale, str):
        return Failure(
            SpecStatedParseError(
                field="rationale", detail=f"rationale is not a string: {rationale!r}"
            )
        )
    return _stated_by(value=payload["stated_by"], headings=headings).map(
        lambda stated_by: SpecStatedVerdict(
            kind=kind,
            stated_by=stated_by,
            generalization_target=target,
            rationale=rationale,
        )
    )


def parse_verdict(
    *, text: str, headings: Collection[str]
) -> Result[SpecStatedVerdict, SpecStatedParseError]:
    """Parse one raw model response into a verdict over the headings the tree carries.

    `headings` is the H2 heading set the verdict may cite — every entry of the
    verdict's `stated_by` MUST be one of them. A well-formed response yields
    the typed verdict; a response with a missing or ill-typed field yields a
    `Failure` whose error names that field; a response that is not JSON yields
    a `Failure` whose error carries `field` `None` and a `detail` naming the
    parse error.

    The `json.JSONDecodeError` catch is the narrow seam this boundary exists
    to be: a model response is foreign input, so its malformedness is an
    expected failure that rides the railway rather than an exception a caller
    has to guard.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        return Failure(SpecStatedParseError(field=None, detail=f"response is not JSON: {error}"))
    if not isinstance(parsed, dict):
        return Failure(
            SpecStatedParseError(
                field=None,
                detail=f"response is not a JSON object but a {type(parsed).__name__}",
            )
        )
    payload = cast("dict[str, object]", parsed)
    omitted = [field for field in _REQUIRED_VERDICT_FIELDS if field not in payload]
    if omitted:
        return Failure(
            SpecStatedParseError(
                field=omitted[0], detail=f"response omits the required field {omitted[0]!r}"
            )
        )
    return _verdict_from(payload=payload, headings=headings)


def judge(
    *, spec_tree: Mapping[str, str], statement: str, run_model: ModelRunner
) -> Result[SpecStatedVerdict, SpecStatedParseError]:
    """Judge whether `spec_tree` states `statement`, and by which clause.

    `spec_tree` maps each spec-tree-relative file path to its text. The model
    is reached exactly once, through `run_model`, with `JUDGE_PROMPT` rendered
    over the tree and the statement.

    The heading set the verdict is validated against is the TREE'S OWN H2
    headings, derived here rather than taken from the response, so a verdict
    citing a clause the supplied tree does not carry is refused as a
    `stated_by` failure instead of returned.
    """
    prompt = JUDGE_PROMPT.format(
        spec_tree=_rendered_spec_tree(spec_tree=spec_tree), statement=statement
    )
    return parse_verdict(text=run_model(prompt), headings=_governing_headings(spec_tree=spec_tree))


def classify(
    *, title: str, description: str, item_type: str, run_model: ModelRunner
) -> Result[ItemClass, SpecStatedParseError]:
    """Classify one work item, treating `item_type` as evidence and not as the answer.

    `item_type` is the stored type: it is rendered into the prompt as evidence
    about the item, and the class returned is the model's own reading of the
    title and the description. The model is reached exactly once, through
    `run_model`.

    An answer outside the four-member vocabulary rides the `Failure` track.
    The failure carries `field` `None` because a classification response is one
    bare word rather than a JSON object, so there is no field to name.
    """
    prompt = CLASSIFY_PROMPT.format(title=title, description=description, item_type=item_type)
    answer = run_model(prompt).strip()
    if answer not in _ITEM_CLASSES:
        return Failure(
            SpecStatedParseError(
                field=None, detail=f"answer is not one of {_ITEM_CLASSES}: {answer!r}"
            )
        )
    return Success(answer)
