"""The spec-PR gate's outcome, and the effects that record and publish it.

One concern, split out of `spec_pr_merge_policy` so the supervisor stays under
the LLOC soft ceiling: the `Decision` the gate reaches, the constructor for its
blocked path, the journal registration that must succeed before a merge is
permitted, and the narration that tells a reader which of the two happened.

`Decision` lives HERE rather than in the supervisor because `_blocked` and
`_register` both construct it and `_publish` consumes it — leaving it behind
would have made this module import from the module that imports it back. The
supervisor re-exports it, so `spec_pr_merge_policy.Decision` still resolves and
no importer moves.

This is the sibling of `_spec_pr_merge_gather`, which owns the impure
observation half; the pure rules live in
`livespec.spec_governance.pr_merge_derivation`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from returns.io import IOResult, IOSuccess

from livespec.errors import LivespecError
from livespec.io import fs, streams
from livespec.spec_governance.journal import append_journal_payload

__all__: list[str] = ["Decision", "_blocked", "_publish", "_register"]

_AUTO_ON_GREEN = "auto-on-green"


@dataclass(frozen=True, kw_only=True, slots=True)
class Decision:
    """The gate's answer, the reason to log, and the policy it rests on."""

    decision: Literal["auto", "blocked"]
    reason: str
    stems: tuple[str, ...]
    effective_policy: str | None
    effective_source: str | None


def _register(
    *,
    stems: tuple[str, ...],
    project_root: Path,
    repo: str,
    pull_request_number: int,
    effective_source: str,
) -> Decision:
    """Append the journal event BEFORE registering; a failed append blocks.

    `SPECIFICATION/contracts.md`'s merge-registration mechanics make the append
    the gate for this step — it records which setting governed the attempt and
    refuses to proceed when it cannot be written — rather than a durable
    archive, which the pull-request timeline supplies.
    """
    appended = append_journal_payload(
        project_root=project_root,
        event={
            "event_type": "spec_pr_merge",
            "pull_request_identity": f"{repo}#{pull_request_number}",
            "proposal_stems": list(stems),
            "effective_policy": _AUTO_ON_GREEN,
            "effective_source": effective_source,
            "registration_result": "registered",
            "required_gate_state": "pending",
            "outcome": "consumed",
        },
    )
    if isinstance(appended, str):
        return Decision(
            decision="blocked",
            reason=f"journal append FAILED — per contract this PREVENTS registration: {appended}",
            stems=stems,
            effective_policy=_AUTO_ON_GREEN,
            effective_source=effective_source,
        )
    return Decision(
        decision="auto",
        reason="pull-request effective policy is auto-on-green; registration permitted",
        stems=stems,
        effective_policy=_AUTO_ON_GREEN,
        effective_source=effective_source,
    )


def _blocked(*, reason: str) -> Decision:
    return Decision(
        decision="blocked",
        reason=reason,
        stems=(),
        effective_policy=None,
        effective_source=None,
    )


def _publish(
    *,
    decision: Decision,
    github_output: Path | None,
) -> IOResult[Decision, LivespecError]:
    """Narrate the decision on stdout and, when asked, append the step output.

    The narration is deliberately unconditional: reading the CI run's
    `auto_merge` field alone cannot tell a blocked decision apart from a step
    that crashed before deciding anything, so the gate must always say which
    of the two happened in its own words.
    """
    _ = streams.write_stdout(
        text=json.dumps(
            {
                "decision": decision.decision,
                "reason": decision.reason,
                "proposal_stems": list(decision.stems),
                "effective_policy": decision.effective_policy,
                "effective_source": decision.effective_source,
            },
            sort_keys=True,
        )
        + "\n",
    )
    if github_output is None:
        return IOSuccess(decision)
    return fs.append_text(
        path=github_output,
        text=f"decision={decision.decision}\n",
    ).map(lambda _: decision)
