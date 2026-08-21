# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# livespec-lloc-soft-band-owner: livespec-n33rwg.2
# This file measures 230 LLOC, inside the 201-250 soft band. The marker
# names who owes the refactor; it does NOT bless the debt. Carrying it is
# permitted, not blessed, and removing this block is part of closing the
# item above. Without a marker the file fails the release gate AFTER the
# tag is pushed, which is how v0.34.2..v0.37.0 all published un-gated.
"""Spec pull-request merge-policy gate supervisor.

`SPECIFICATION/non-functional-requirements.md` requires this derivation to
exist as ONE core-shipped implementation every caller executes, under its
shared-CI-logic contract. This module is that implementation's entry
point: `livespec`'s own `auto-enable-merge.yml` invokes it directly, and
the copier template's generated workflow reaches it through the core-hosted
reusable workflow. Two independent copies are prohibited, so nothing that
decides anything may be re-spelled in workflow YAML.

The gate answers ONE question — may this pull request have auto-merge
registered on it? — and answers it on stdout plus, when asked, as a CI step
output parameter. Every DECIDED outcome, `blocked` included, exits 0: blocking
is a decision, not an error, and failing the step for it would mark a
legitimately human-merged spec pull request as broken. The exit code is
reserved for the cases where no decision could be communicated at all, where a
failed step is exactly the fail-closed behaviour wanted.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._spec_pr_merge_gather import Observations, gather
from livespec.errors import LivespecError
from livespec.io import cli, fs, streams
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.journal import append_journal_payload
from livespec.spec_governance.pr_merge_derivation import derive
from livespec.spec_governance.spec_pr_merge import SPEC_ROOT, effective_spec_pr_merge

__all__: list[str] = ["Decision", "build_parser", "decide", "dispatch", "main"]

_COMMAND = "spec-pr-merge-policy"
_AUTO_ON_GREEN = "auto-on-green"
_CONFIG_FILENAME = ".livespec.jsonc"
_EMPTY_CONFIG_TEXT = "{}"


@dataclass(frozen=True, kw_only=True, slots=True)
class Decision:
    """The gate's answer, the reason to log, and the policy it rests on."""

    decision: Literal["auto", "blocked"]
    reason: str
    stems: tuple[str, ...]
    effective_policy: str | None
    effective_source: str | None


def build_parser() -> argparse.ArgumentParser:
    """Construct the spec-PR merge-policy argparse parser without parsing."""
    parser = argparse.ArgumentParser(prog=_COMMAND, exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    _ = parser.add_argument("--repo", required=True)
    _ = parser.add_argument("--pull-request", required=True, type=int)
    _ = parser.add_argument("--base-sha", required=True)
    _ = parser.add_argument("--head-sha", required=True)
    _ = parser.add_argument("--github-output", default=None)
    return parser


def main(*, argv: list[str] | None = None) -> int:
    """Spec-PR merge-policy supervisor entry point."""
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    railway: IOResult[Any, LivespecError] = cli.parse_argv(
        parser=parser,
        argv=resolved_argv,
    ).bind(lambda namespace: dispatch(namespace=namespace))  # pyright: ignore[reportArgumentType]
    unwrapped = unsafe_perform_io(railway)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return cli.emit_livespec_failure(command=_COMMAND, err=err)
        case _:
            assert_never(unwrapped)


def dispatch(*, namespace: argparse.Namespace) -> IOResult[Decision, LivespecError]:
    """Resolve the decision, narrate it, and publish it as a step output."""
    project_root = (
        Path.cwd() if namespace.project_root is None else Path(str(namespace.project_root))
    )
    return decide(
        project_root=project_root,
        repo=str(namespace.repo),
        pull_request_number=int(namespace.pull_request),
        base_sha=str(namespace.base_sha),
        head_sha=str(namespace.head_sha),
    ).bind(
        lambda decision: _publish(
            decision=decision,
            github_output=(
                None if namespace.github_output is None else Path(str(namespace.github_output))
            ),
        ),
    )


def decide(
    *,
    project_root: Path,
    repo: str,
    pull_request_number: int,
    base_sha: str,
    head_sha: str,
) -> IOResult[Decision, LivespecError]:
    """Return the gate's decision, resolving every observation failure as blocked.

    `lash` is what makes a git or hosting-API error BLOCK rather than propagate:
    `SPECIFICATION/spec.md` `effective_spec_pr_merge` classes such an error as
    derivation FAILURE, which is a decision the gate must publish, not a crash.
    """
    return (
        gather(
            project_root=project_root,
            spec_root=SPEC_ROOT,
            base_sha=base_sha,
            head_sha=head_sha,
            repo=repo,
            pull_request_number=pull_request_number,
        )
        .map(
            lambda observations: _decide_from(
                observations=observations,
                project_root=project_root,
                repo=repo,
                pull_request_number=pull_request_number,
            ),
        )
        .lash(
            lambda err: IOSuccess(
                _blocked(reason=f"derivation FAILURE: {err}"),
            ),
        )
    )


def _decide_from(
    *,
    observations: Observations,
    project_root: Path,
    repo: str,
    pull_request_number: int,
) -> Decision:
    derivation = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=observations.touched_spec_root,
        total_changed_files=observations.total_changed_files,
        local_paths=observations.local_paths,
        api_files=observations.api_files,
    )
    if derivation.outcome == "auto":
        return Decision(
            decision="auto",
            reason=derivation.reason,
            stems=(),
            effective_policy=None,
            effective_source=None,
        )
    if derivation.outcome == "blocked":
        return _blocked(reason=derivation.reason)
    return _fold_governed(
        stems=derivation.stems,
        project_root=project_root,
        repo=repo,
        pull_request_number=pull_request_number,
    )


def _fold_governed(
    *,
    stems: tuple[str, ...],
    project_root: Path,
    repo: str,
    pull_request_number: int,
) -> Decision:
    """Fold the pull-request effective policy, then gate on the journal append."""
    config_path = project_root / _CONFIG_FILENAME
    text = config_path.read_text(encoding="utf-8") if config_path.is_file() else _EMPTY_CONFIG_TEXT
    policy = effective_spec_pr_merge(
        project_root=project_root,
        config=parse_config_text(text=text).effective,
        proposal_stems=stems,
    )
    if policy.value != _AUTO_ON_GREEN:
        return Decision(
            decision="blocked",
            reason=f"effective policy is {policy.value}; leaving for human merge",
            stems=stems,
            effective_policy=policy.value,
            effective_source=policy.source,
        )
    return _register(
        stems=stems,
        project_root=project_root,
        repo=repo,
        pull_request_number=pull_request_number,
        effective_source=policy.source,
    )


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
