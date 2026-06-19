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

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code. The file-shaping railway
helpers live in the sibling private module
`_revise_railway_emits.py` (extracted at to keep
this file under the 250-LLOC hard ceiling).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import structlog
from returns.io import IOResult
from returns.result import Failure, Result, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.commands._revise_doctor import (
    _run_post_step_doctor,
)
from livespec.commands._revise_helpers import (
    _compose_resulting_changes_section as _compose_resulting_changes_section,
)
from livespec.commands._revise_helpers import (
    _now_utc_iso8601,
    _resolve_author,
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
from livespec.commands._revise_render import (
    _prepare_render_plan,
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
    _validate_resulting_files,
)
from livespec.commands._revise_validation import (
    _validate_resulting_files_paths as _validate_resulting_files_paths,
)
from livespec.commands._revise_validation import (
    _validate_resulting_files_targets_exist as _validate_resulting_files_targets_exist,
)
from livespec.errors import HelpRequestedError, LivespecError, UsageError
from livespec.io import cli, fs
from livespec.io import git as io_git
from livespec.parse import jsonc
from livespec.validate import revise_input as validate_revise_input_module

__all__: list[str] = ["build_parser", "main"]


_log = structlog.get_logger(__name__)

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_REVISE_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "revise_input.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the revise argparse parser without parsing.

     Per style doc §"CLI argument parsing seam":
     `exit_on_error=False` lets argparse signal errors via
     `argparse.ArgumentError` rather than `SystemExit`. The
     parser exposes `--revise-json <path>` (required), and the
     optional `--author`, `--spec-target`, `--project-root` flags
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
    doctor static invocation per `SPECIFICATION/contracts.md`
    §"Sub-command wire contracts" → "`revise` payload
    validation". When set, the wrapper invokes
    `bin/doctor_static.py` after the freshly-cut `vNNN/`
    snapshot lands; any `status: "fail"` finding
    short-circuits the railway with `IOFailure(PreconditionError)`
    so the supervisor lifts to exit 3 — but the `vNNN/` snapshot
    is already on disk; exit 3 is INFORMATIONAL, directing the
    user to resolve the named findings, then re-run doctor to
    verify resolution. SKILL.md prose passes the flag on every
    production invocation; file-shaping unit tests omit it.
    """
    parser = argparse.ArgumentParser(prog="revise", exit_on_error=False)
    _ = parser.add_argument("--revise-json", required=True)
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

    Success(<value>) -> exit 0 per style doc §"Exit code
    contract". Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.

    Per work-item li-revslnt + `SPECIFICATION/constraints.md`
    §"Structured logging" + the style spec's canonical
    `match`-arm example: the Failure arm MUST emit a
    `log.error(...)` diagnostic BEFORE returning the exit code.
    At the default `LIVESPEC_LOG_LEVEL=WARNING` the call renders
    as a JSON line on stderr (ERROR > WARNING), so the user
    sees the `LivespecError` subclass name + structured context
    rather than an unexplained non-zero wrapper exit.
    """
    unwrapped = unsafe_perform_io(io_result)  # pyright: ignore[reportArgumentType]
    match unwrapped:
        case Success(_):
            return 0
        case Failure(HelpRequestedError() as err):
            return err.exit_code
        case Failure(LivespecError() as err):
            _log.error(
                "revise failed",
                error_type=type(err).__name__,
                error=str(err),
                exit_code=err.exit_code,
            )
            return err.exit_code
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str] | None = None) -> int:
    """Revise supervisor entry point. Returns the process exit code.

    Threads argv through `parse_argv` -> `fs.read_text` ->
    `jsonc.loads` -> `validate_payload` -> `io_git.get_git_user`
    -> `_process_decisions` (in `_revise_railway_emits`), then
    pattern-matches the final IOResult onto an exit code per
    style doc §"Exit code contract".
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
                lambda revise_input: _validate_resulting_files(
                    revise_input=revise_input,
                    spec_target=_resolve_spec_target(namespace=namespace),
                ),
            )
            .bind(
                lambda revise_input: _prepare_render_plan(
                    revise_input=revise_input,
                    spec_target=_resolve_spec_target(namespace=namespace),
                    project_root=_resolve_project_root(namespace=namespace),
                ).bind(
                    lambda render_plan: io_git.get_git_user().bind(
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
                            render_plan=render_plan,
                        ),
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

    Per `SPECIFICATION/spec.md` §"Sub-command lifecycle": revise
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


def _check_decisions_nonempty(
    *,
    payload: dict[str, Any],
) -> Result[dict[str, Any], LivespecError]:
    """Reject payloads whose `decisions[]` is present-but-empty.

    Per `SPECIFICATION/spec.md` §"Sub-command lifecycle" revise
    clause (b) (v052): the wrapper MUST fail hard with UsageError
    (exit 2) when the inbound `--revise-json` payload's
    `decisions[]` array is empty. A revise pass with zero
    decisions would produce a no-op cut and is forbidden.

    This pre-check fires BEFORE schema validation so the user
    sees exit 2 (UsageError) for the explicit empty-list case
    rather than exit 4 (ValidationError) from the schema's
    `minItems: 1` constraint, which encodes the same precondition
    as defense-in-depth. Other malformations (missing `decisions`
    key, wrong type) fall through to schema validation
    unchanged.
    """
    # The isinstance(payload, dict) guard remains for runtime
    # defense-in-depth: jsonc.loads upstream returns Any, and
    # while pyright's bind-chain widening surfaces a narrower
    # dict type here, the runtime payload can still be a top-
    # level non-dict (e.g. a JSON array) that needs to fall
    # through to schema validation without crashing.
    if isinstance(payload, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        decisions = payload.get("decisions")
        if isinstance(decisions, list) and len(decisions) == 0:
            return Failure(
                UsageError(
                    "revise: decisions[] array is empty; " "revise requires at least one decision",
                ),
            )
    return Success(payload)


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[Any, LivespecError]:
    """Read revise_input.schema.json and validate the payload.

    Composes fs.read_text(schema) -> jsonc.loads(schema-text) ->
    validate_revise_input(payload, schema-dict). Mirrors
    propose_change/critique's same stage; failures bubble via the
    IOResult track (schema-file missing -> PreconditionError;
    schema malformed -> ValidationError; payload schema-violation
    -> ValidationError).
    """
    return (
        fs.read_text(path=_REVISE_INPUT_SCHEMA_PATH)
        .bind(
            lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(
            lambda schema_dict: IOResult.from_result(  # pyright: ignore[reportArgumentType]
                validate_revise_input_module.validate_revise_input(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )


def _resolve_spec_target(*, namespace: argparse.Namespace) -> Path:
    """Resolve --spec-target to a Path, defaulting to <project-root>/SPECIFICATION.

    Per Plan  +:
    `<spec-target>` is selected via --spec-target, defaulting to
    the project's main spec root (`<project-root>/SPECIFICATION/`
    under the built-in livespec template).
    """
    if namespace.spec_target is not None:
        return Path(namespace.spec_target)
    project_root = _resolve_project_root(namespace=namespace)
    return project_root / "SPECIFICATION"


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd().

    The post-step doctor invocation in `_revise_doctor._run_post_step_doctor`
    forwards `--project-root` to `bin/doctor_static.py` so the doctor
    resolves the spec root from the same project root the revise
    wrapper resolved. Per `SPECIFICATION/contracts.md` §"Wrapper CLI
    surface": `--project-root <path>` (default `Path.cwd()`).
    """
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)
