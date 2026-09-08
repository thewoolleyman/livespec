# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Revise sub-command supervisor.

Per and Plan
: revise is minimum-viable per the spec Q1 —
validates `--revise-json <path>` against revise_input.schema.json,
processes per-proposal `decisions[]` in payload order, writes
the paired `<stem>-revision.md` per decision, moves each
processed `<spec-target>/proposed_changes/<stem>.md` byte-
identically into `<spec-target>/history/vNNN/proposed_changes/
<stem>.md`, and on any `accept`/`modify` cuts a new
`<spec-target>/history/vNNN/` materialized from the active
template's versioned spec files. Accepts `--spec-target <path>`.

`build_parser()` is the pure argparse factory per the style doc;
`main()` is the supervisor that threads argv through the railway
and pattern-matches the final IOResult to derive the exit code.
The file-shaping railway helpers live in the sibling private
module
`_revise_railway_emits.py` (extracted at to keep
this file under the 250-LLOC hard ceiling).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._revise_decision import enforce_revise_decisions
from livespec.commands._revise_doctor import (
    _run_post_step_doctor,
)
from livespec.commands._revise_helpers import (
    _compose_resulting_changes_section as _compose_resulting_changes_section,
)
from livespec.commands._revise_helpers import (
    _now_utc_iso8601,
    _resolve_author,
    _resolve_project_root,
    _resolve_spec_target,
)
from livespec.commands._revise_only_topic import (
    _check_only_topic_matches as _check_only_topic_matches,
)
from livespec.commands._revise_railway_emits import (
    _bind_resulting_files as _bind_resulting_files,
)
from livespec.commands._revise_railway_emits import (
    _format_next_version_name as _format_next_version_name,
)
from livespec.commands._revise_railway_emits import (
    _process_decisions,
)
from livespec.commands._revise_ratification import (
    _canonical_ratification_digest as _canonical_ratification_digest,
)
from livespec.commands._revise_ratification import (
    _validate_ratification_reviews,
)
from livespec.commands._revise_validation import (
    _check_decisions_nonempty,
    _validate_payload,
    _validate_resulting_files,
)
from livespec.commands._revise_validation import (
    _iter_proposal_topics as _iter_proposal_topics,
)
from livespec.commands._revise_validation import (
    _iter_resulting_files_paths as _iter_resulting_files_paths,
)
from livespec.commands._revise_validation import (
    _validate_proposal_topics_exist as _validate_proposal_topics_exist,
)
from livespec.commands._revise_validation import (
    _validate_resulting_files_paths as _validate_resulting_files_paths,
)
from livespec.commands._revise_validation import (
    _validate_resulting_files_targets_exist as _validate_resulting_files_targets_exist,
)
from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.io import git as io_git
from livespec.parse import jsonc

__all__: list[str] = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Construct the revise argparse parser without parsing.

     Per the style doc CLI argument parsing seam:
     `exit_on_error=False` lets argparse signal errors via
     `argparse.ArgumentError` rather than `SystemExit`. The
     parser exposes `--revise-json <path>` (required), the
     optional `--author`, `--spec-target`, `--project-root` flags,
     and the optional `--only-topic <topic>` single-decision guard
    .

    The Step 3.5 stale-branch precondition (per PC
    `coordinating-epic-stale-revise-enforcement` Layer 1) is
    owned by the SKILL.md prose; the wrapper accepts the flag
    pair `--skip-stale-branch-check` / `--run-stale-branch-check`
    as a mutually-exclusive group so the skill's forwarded argv
    parses cleanly even though the wrapper does not act on the
    flags itself. The shared check `no_stale_revise_branches`
    that the SKILL.md prose invokes is owned by
    livespec-dev-tooling per the cross-cutting epic.

    `--post-step-doctor` (default off) gates the post-step
    doctor static invocation per `SPECIFICATION/contracts.md`.
    When set, the wrapper invokes
    `bin/doctor_static.py` after the freshly-cut `vNNN/`
    snapshot lands; any `status: "fail"` finding
    short-circuits the railway with `IOFailure(PreconditionError)`
    so the supervisor lifts to exit 3 — but the `vNNN/` snapshot
    is already on disk; exit 3 is INFORMATIONAL, directing the
    user to resolve the named findings, then re-run doctor to
    verify resolution. SKILL.md prose passes the flag on every
    production invocation; file-shaping unit tests omit it.
    """
    parser = argparse.ArgumentParser(
        prog="revise",
        exit_on_error=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, width=100),
    )
    _ = parser.add_argument(
        "--revise-json",
        required=True,
        help=(
            "Path to the LLM-authored revise payload. Its decisions[] array "
            "may cover one or more pending proposals and need not cover every "
            "pending proposal."
        ),
    )
    _ = parser.add_argument(
        "--only-topic",
        default=None,
        metavar="TOPIC",
        help=(
            "Guard assertion: --revise-json must contain exactly one decisions[] "
            "entry whose proposal_topic equals TOPIC; decision content still "
            "comes from the payload."
        ),
    )
    _ = parser.add_argument("--author", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    _ = parser.add_argument("--project-root", default=None)
    _ = parser.add_argument("--post-step-doctor", action="store_true")
    stale_branch_group = parser.add_mutually_exclusive_group()
    _ = stale_branch_group.add_argument("--skip-stale-branch-check", action="store_true")
    _ = stale_branch_group.add_argument("--run-stale-branch-check", action="store_true")
    return parser


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per the style doc exit code
    contract. Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.

    Per work-item li-revslnt + `SPECIFICATION/constraints.md`
    + the style spec's canonical `match`-arm example: the
    Failure arm MUST emit a `log.error(...)` diagnostic BEFORE
    returning the exit code.
    At the default `LIVESPEC_LOG_LEVEL=WARNING` the call renders
    as a JSON line on stderr (ERROR > WARNING), so the user
    sees the `LivespecError` subclass name + structured context
    rather than an unexplained non-zero wrapper exit.
    """
    unwrapped = unsafe_perform_io(io_result)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return cli.emit_livespec_failure(command="revise", err=err)
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str] | None = None) -> int:
    """Revise supervisor entry point. Returns the process exit code.

    Threads argv through `parse_argv` -> `fs.read_text` ->
    `jsonc.loads` -> `validate_payload` -> `io_git.get_git_user`
    -> `_process_decisions` (in `_revise_railway_emits`), then
    pattern-matches the final IOResult onto an exit code per
    the style doc exit code contract.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    revised_at = _now_utc_iso8601()
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (  # pyright: ignore[reportArgumentType]
            fs.read_text(path=Path(namespace.revise_json))
            .bind(
                lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
            )
            .bind(lambda payload: IOResult.from_result(_check_decisions_nonempty(payload=payload)))
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda revise_input: IOResult.from_result(
                    _check_only_topic_matches(
                        payload=revise_input,
                        only_topic=namespace.only_topic,
                    ),
                ),
            )
            .bind(
                lambda revise_input: _validate_resulting_files(
                    revise_input=revise_input,
                    spec_target=_resolve_spec_target(namespace=namespace),
                ),
            )
            .bind(
                lambda revise_input: _validate_ratification_reviews(
                    revise_input=revise_input,
                    project_root=_resolve_project_root(namespace=namespace),
                    revised_at=revised_at,
                    spec_target=_resolve_spec_target(namespace=namespace),
                ),
            )
            .bind(
                lambda revise_input: enforce_revise_decisions(
                    revise_input=revise_input,
                    project_root=_resolve_project_root(namespace=namespace),
                    spec_target=_resolve_spec_target(namespace=namespace),
                ),
            )
            .bind(
                lambda revise_input: io_git.get_git_user().bind(
                    lambda author_human: _process_decisions(
                        revise_input=revise_input,
                        spec_target=_resolve_spec_target(namespace=namespace),
                        author_human=author_human,
                        author_llm=_resolve_author(
                            namespace=namespace,
                            payload=revise_input,
                            env_lookup=os.environ.get,
                        ),
                        revised_at=revised_at,
                    ),
                ),
            )
            .bind(
                lambda revise_input: _maybe_run_post_step_doctor(
                    revise_input=revise_input,
                    namespace=namespace,
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)


def _maybe_run_post_step_doctor(
    *,
    revise_input: Any,
    namespace: argparse.Namespace,
) -> IOResult[Any, LivespecError]:
    """Conditionally invoke the post-step doctor static phase.

    Per `SPECIFICATION/spec.md`: revise
    runs a post-step doctor static check against the freshly-cut
    `vNNN/` snapshot. The full static-phase doctor registry is
    exercised; the gating semantics are exit 3 on any
    fail-status finding.

    The post-step doctor invocation is gated on the
    `--post-step-doctor` flag (default off) so existing
    file-shaping unit tests continue to compose without needing
    a full doctor-clean project root. SKILL.md prose passes the
    flag explicitly on every production invocation; unit tests
    that scope-down to file-shaping concerns may omit it.

    Per the work-item description (li-f2dk3t): "the snapshot is
    already cut by the time post-step runs; the exit 3 surfaces
    the gap and the user's corrective action is to file the
    declared work-items then re-run doctor to verify
    resolution."
    """
    if not getattr(namespace, "post_step_doctor", False):
        return IOResult.from_value(revise_input)
    return _run_post_step_doctor(
        revise_input=revise_input,
        project_root=_resolve_project_root(namespace=namespace),
    )
