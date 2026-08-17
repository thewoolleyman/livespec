"""Single-topic selection guard for `livespec.commands.revise`."""

from __future__ import annotations

from returns.result import Failure, Result, Success

from livespec.errors import LivespecError, UsageError
from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = ["_check_only_topic_matches"]


def _check_only_topic_matches(
    *,
    payload: RevisionInput,
    only_topic: str | None,
) -> Result[RevisionInput, LivespecError]:
    """Reject payloads that violate the optional single-topic guard.

    `--only-topic <topic>` is a guard over the LLM-authored
    payload, not a payload-construction shortcut. When present,
    The caller runs this guard after schema validation and before
    any file-shaping work, so `decisions[]` is known to be a
    list of decision objects.
    """
    if only_topic is None:
        return Success(payload)
    decisions = payload.decisions
    if len(decisions) != 1:
        return Failure(
            UsageError(_only_topic_count_message(only_topic=only_topic, count=len(decisions))),
        )
    proposal_topic = str(decisions[0].get("proposal_topic", ""))
    if proposal_topic != only_topic:
        return Failure(
            UsageError(
                _only_topic_mismatch_message(
                    only_topic=only_topic,
                    proposal_topic=proposal_topic,
                ),
            ),
        )
    return Success(payload)


def _only_topic_count_message(*, only_topic: str, count: int) -> str:
    return "".join(
        [
            f"revise: --only-topic {only_topic} requires exactly one ",
            f"decisions[] entry; payload contains {count}",
        ],
    )


def _only_topic_mismatch_message(*, only_topic: str, proposal_topic: str) -> str:
    return "".join(
        [
            f"revise: --only-topic {only_topic} requires decisions[0].",
            f"proposal_topic '{only_topic}', got proposal_topic ",
            f"'{proposal_topic}'",
        ],
    )
