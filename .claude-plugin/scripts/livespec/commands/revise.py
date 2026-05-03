"""Revise sub-command supervisor.

Per PROPOSAL.md §"`revise`" (line ~2335) and Plan Phase 3
(lines 1533-1553): revise is minimum-viable per v019 Q1 —
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
IOResult to derive the exit code. Cycle 123 wires
build_parser + parse_argv + UsageError exit-code mapping;
subsequent cycles widen the railway.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.revise_input import RevisionInput
from livespec.validate import revise_input as validate_revise_input_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_REVISE_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "revise_input.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the revise argparse parser without parsing.

    Per style doc §"CLI argument parsing seam":
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`. The
    parser exposes `--revise-json <path>` (required), and the
    optional `--author`, `--spec-target`, `--project-root` flags
    per PROPOSAL.md §"revise" lines 2375-2410.
    """
    parser = argparse.ArgumentParser(prog="revise", exit_on_error=False)
    _ = parser.add_argument("--revise-json", required=True)
    _ = parser.add_argument("--author", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per style doc §"Exit code
    contract". Failure(LivespecError) lifts via err.exit_code;
    assert_never closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def main(*, argv: list[str] | None = None) -> int:
    """Revise supervisor entry point. Returns the process exit code.

    Cycle 123 wires parse_argv; cycle 124 appends fs.read_text on
    the --revise-json path; cycle 125 lifts the pure jsonc.loads
    onto the IOResult track. Cycle 126 appends schema validation
    against revise_input.schema.json. Cycle 127 appends the
    per-decision processing stage: for each decision, write the
    paired `<stem>-revision.md` under `<spec-target>/history/
    vNNN/proposed_changes/` (where vNNN = max-existing-version+1).
    Phase-3 minimum-viable; subsequent cycles add the move of the
    proposed-change file into the new history directory + the
    accept/modify version-cut materializing resulting_files.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            fs.read_text(path=Path(namespace.revise_json))
            .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda revise_input: _process_decisions(
                    revise_input=revise_input,
                    spec_target=_resolve_spec_target(namespace=namespace),
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)


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
        .bind(lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_revise_input_module.validate_revise_input(
                    payload=payload,
                    schema=schema_dict,
                ),
            ),
        )
    )


def _resolve_spec_target(*, namespace: argparse.Namespace) -> Path:
    """Resolve --spec-target to a Path, defaulting to <project-root>/SPECIFICATION.

    Per Plan Phase 3 (lines 1533-1553) + PROPOSAL.md §"revise":
    `<spec-target>` is selected via --spec-target, defaulting to
    the project's main spec root (`<project-root>/SPECIFICATION/`
    under the built-in livespec template).
    """
    if namespace.spec_target is not None:
        return Path(namespace.spec_target)
    project_root = Path.cwd() if namespace.project_root is None else Path(namespace.project_root)
    return project_root / "SPECIFICATION"


def _next_history_version_dir(
    *,
    spec_target: Path,
) -> IOResult[Path, LivespecError]:
    """Compute `<spec-target>/history/v(max+1)/` from existing v* dirs.

    Lists the spec-target's `history/` directory, filters for
    entries matching `v\\d+`, computes the next version number,
    and returns the path. When `history/` is missing or empty,
    defaults to v001 (the seed-baseline case never reaches revise
    because revise requires an in-flight proposed-change which
    presupposes a v001 already exists, but the bootstrap-friendly
    default keeps the helper safe).
    """
    history_dir = spec_target / "history"
    return fs.list_dir(path=history_dir).map(
        lambda children: history_dir / _format_next_version_name(children=children),
    )


def _format_next_version_name(*, children: list[Path]) -> str:
    """Compute the next `vNNN` directory name from existing children.

    Walks the children list looking for `vNNN` patterns; tracks
    the maximum N found; returns `v(max+1)` zero-padded to three
    digits. When no `vNNN` children are present, returns "v001".
    """
    max_version = 0
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        max_version = max(max_version, version)
    return f"v{max_version + 1:03d}"


def _compose_revision_body(*, decision: dict[str, object]) -> str:
    """Compose the `<stem>-revision.md` body from a decision dict.

    Per PROPOSAL.md §"Revision file format" (line ~3037): the
    body has front-matter (proposal, decision, rationale) plus
    a `## Decision and Rationale` section. Phase-3 minimum-viable
    keeps the front-matter to the three required keys; richer
    fields (`author_llm`, `author_human`, `revised_at`) widen
    under consumer pressure once the doctor's
    `revision-to-proposed-change-pairing` check pulls them in.
    """
    topic = str(decision.get("proposal_topic", ""))
    decision_value = str(decision.get("decision", ""))
    rationale = str(decision.get("rationale", ""))
    return (
        "---\n"
        f"proposal: {topic}.md\n"
        f"decision: {decision_value}\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        f"{rationale}\n"
    )


def _process_decisions(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """Process each decision in payload order; write paired revisions + move proposals.

    For each decision: (1) compose the `<stem>-revision.md` body
    and write it under `<spec-target>/history/vNNN/proposed_changes/`,
    and (2) move `<spec-target>/proposed_changes/<stem>.md`
    byte-identically into `<spec-target>/history/vNNN/proposed_changes/`.
    Phase-3 minimum-viable; the accept/modify version-cut that
    materializes resulting_files in the working spec is appended
    by a subsequent cycle.
    """
    return _next_history_version_dir(spec_target=spec_target).bind(
        lambda version_dir: _write_and_move_per_decision(
            revise_input=revise_input,
            spec_target=spec_target,
            version_dir=version_dir,
        ),
    )


def _write_and_move_per_decision(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
    version_dir: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """For each decision, write revision + move proposal + materialize resulting_files.

    Fold-style accumulator: each per-decision triple (revision-
    write + proposed-change-move + (for accept/modify)
    resulting-files-materialize) binds onto the previous IOResult
    so any failure short-circuits the rest via the typed Failure
    surface. Mirrors seed.py's `_write_main_spec_files` shape.
    """
    accumulator: IOResult[RevisionInput, LivespecError] = IOResult.from_value(
        revise_input,
    )
    for decision in revise_input.decisions:
        topic = str(decision.get("proposal_topic", ""))
        revision_target = version_dir / "proposed_changes" / f"{topic}-revision.md"
        revision_body = _compose_revision_body(decision=decision)
        proposed_source = spec_target / "proposed_changes" / f"{topic}.md"
        proposed_target = version_dir / "proposed_changes" / f"{topic}.md"
        accumulator = accumulator.bind(
            lambda _value, target=revision_target, body=revision_body: fs.write_text(
                path=target,
                text=body,
            ).map(lambda _: revise_input),
        )
        accumulator = accumulator.bind(
            lambda _value, source=proposed_source, target=proposed_target: fs.move(
                source=source,
                target=target,
            ).map(lambda _: revise_input),
        )
        accumulator = _bind_resulting_files(
            accumulator=accumulator,
            decision=decision,
            spec_target=spec_target,
            revise_input=revise_input,
        )
    return accumulator


def _bind_resulting_files(
    *,
    accumulator: IOResult[RevisionInput, LivespecError],
    decision: dict[str, object],
    spec_target: Path,
    revise_input: RevisionInput,
) -> IOResult[RevisionInput, LivespecError]:
    """Append resulting_files writes to the accumulator for accept/modify.

    Per PROPOSAL.md §"`revise`" lines 2411-2421: only `accept`
    and `modify` decisions materialize resulting_files into the
    working spec; `reject` decisions produce no working-spec
    changes (just the audit-trail revision file).
    """
    decision_value = str(decision.get("decision", ""))
    if decision_value not in ("accept", "modify"):
        return accumulator
    resulting_files = decision.get("resulting_files", [])
    if not isinstance(resulting_files, list):
        return accumulator
    for entry in resulting_files:
        if not isinstance(entry, dict):
            continue
        target = spec_target / str(entry["path"])
        text = str(entry["content"])
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target,
                text=text,
            ).map(lambda _: revise_input),
        )
    return accumulator
