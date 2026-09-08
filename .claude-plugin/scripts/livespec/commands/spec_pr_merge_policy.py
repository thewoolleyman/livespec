# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
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
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._spec_pr_merge_gather import Observations, gather
from livespec.commands._spec_pr_merge_outcome import (
    _AUTO_ON_GREEN,
    Decision,
    _blocked,
    _publish,
    _register,
)
from livespec.errors import LivespecError
from livespec.io import cli
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.pr_merge_derivation import derive
from livespec.spec_governance.spec_pr_merge import SPEC_ROOT, effective_spec_pr_merge

__all__: list[str] = ["Decision", "build_parser", "decide", "dispatch", "main"]

_COMMAND = "spec-pr-merge-policy"
_CONFIG_FILENAME = ".livespec.jsonc"
_EMPTY_CONFIG_TEXT = "{}"


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
