"""Seed sub-command supervisor.

Per PROPOSAL.md §"`seed`" + briefing "outside-in walking
direction": this is the wrapper entry-point importing
`livespec.commands.seed.main`. Drives the seed flow:
load+validate `--seed-json` payload, write `.livespec.jsonc`,
materialize the main + sub-spec trees, auto-capture the seed
proposed-change, run post-step doctor.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io import cli, fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate import seed_input as validate_seed_input_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_SEED_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "seed_input.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Construct the seed argparse parser without parsing.

    Pure: returns the configured parser; the caller (the io/cli
    facade) drives `parse_args()`. Per style doc §"CLI argument
    parsing seam", `exit_on_error=False` lets argparse signal
    errors via `argparse.ArgumentError` rather than `SystemExit`.
    """
    parser = argparse.ArgumentParser(prog="seed", exit_on_error=False)
    _ = parser.add_argument("--seed-json", required=True)
    _ = parser.add_argument("--project-root", default=None)
    return parser


def _load_seed_json(*, namespace: argparse.Namespace) -> IOResult[str, LivespecError]:
    """Read the --seed-json payload from disk; railway-stage 2.

    Threads the namespace's `seed_json` attribute into
    fs.read_text. Failure-track LivespecError values bubble
    untouched.
    """
    return fs.read_text(path=Path(namespace.seed_json))


def _parse_payload(*, text: str) -> IOResult[Any, LivespecError]:
    """Lift the pure JSONC parser onto the IOResult track.

    `jsonc.loads` returns `Result[Any, ValidationError]`;
    `IOResult.from_result(...)` lifts that into the
    `IOResult[Any, ValidationError]` shape the seed railway
    composes against.
    """
    return IOResult.from_result(jsonc.loads(text=text))


def _validate_payload(*, payload: dict[str, Any]) -> IOResult[SeedInput, LivespecError]:
    """Read the seed-input schema and validate the payload against it.

    Composes fs.read_text(schema) -> jsonc.loads(schema-text) ->
    validate_seed_input(payload, schema-dict). Failures bubble
    via the IOResult track: schema-file missing ->
    PreconditionError; schema malformed -> ValidationError;
    payload schema-violation -> ValidationError.
    """
    return (
        fs.read_text(path=_SEED_INPUT_SCHEMA_PATH)
        .bind(lambda schema_text: IOResult.from_result(jsonc.loads(text=schema_text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_seed_input_module.validate_seed_input(
                    payload=payload, schema=schema_dict,
                ),
            ),
        )
    )


def _write_livespec_config(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<project-root>/.livespec.jsonc` from the validated seed input.

    PROPOSAL.md §"`seed`" step 1 (line ~1996): the wrapper writes
    .livespec.jsonc with the payload's top-level `template` value.
    The minimum-viable skeleton emitted here carries just the
    template field; subsequent cycles widen to the full commented
    schema skeleton under consumer pressure (e.g., when a doctor
    check or downstream wrapper reads other config keys).

    Returns IOSuccess(seed_input) so the railway chain can keep
    composing additional file-shaping stages on the value.
    """
    skeleton = '{\n  "template": "' + seed_input.template + '"\n}\n'
    config_path = project_root / ".livespec.jsonc"
    return fs.write_text(path=config_path, text=skeleton).map(lambda _: seed_input)


def _write_main_spec_files(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write each main-spec `files[]` entry to its project-root-relative path.

    PROPOSAL.md §"`seed`" step 2 (line ~1999): "Write each
    main-spec `files[]` entry to its specified path." Each
    entry's `path` is project-root-relative; `content` goes
    verbatim. Sequencing across entries is fold-style: each
    write binds onto the previous IOResult so any failure
    short-circuits the rest with the typed Failure surface.
    """
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for entry in seed_input.files:
        target = project_root / entry["path"]
        text = entry["content"]
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target, text=text,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _write_main_spec_history_v001(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Materialize `<spec-root>/history/v001/<spec-file>` for each main-spec entry.

    PROPOSAL.md §"`seed`" step 4 (line ~2007): "Create
    `<spec-root>/history/v001/` for the main spec (including
    the initial versioned spec files...)." Per file: the
    spec_root is derived as the first path component of the
    file's project-root-relative path (e.g.,
    `SPECIFICATION/spec.md` -> spec_root `SPECIFICATION/`,
    file basename `spec.md`); the spec-file remainder beneath
    spec_root is preserved in the v001 snapshot
    (e.g., a file at `SPECIFICATION/sub/x.md` lands at
    `SPECIFICATION/history/v001/sub/x.md`). Content is the
    payload's verbatim bytes — the v001 baseline.
    """
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for entry in seed_input.files:
        original_path = Path(entry["path"])
        if len(original_path.parts) < 2:
            continue
        spec_root_name = original_path.parts[0]
        relative = Path(*original_path.parts[1:])
        target = project_root / spec_root_name / "history" / "v001" / relative
        text = entry["content"]
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target, text=text,
            ).map(lambda _: seed_input),
        )
    return accumulator


def _write_sub_spec_files(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write each sub-spec entry's `files[]` to project-root-relative paths.

    PROPOSAL.md §"`seed`" step 3 (line ~2000): "For each entry
    in sub_specs[], write every files[] entry in that sub-spec
    to its SPECIFICATION/templates/<template_name>/<spec-file>
    path." Sub-spec trees write atomically alongside the main
    tree; any failure short-circuits the rest of the seed via
    the IOResult Failure track (partial-write refusal — the
    user's recovery path is to fix the underlying cause and
    re-seed once the existing files are removed).
    """
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        files_list = sub_spec["files"]
        if not isinstance(files_list, list):
            continue
        for entry in files_list:
            if not isinstance(entry, dict):
                continue
            target = project_root / str(entry["path"])
            text = str(entry["content"])
            accumulator = accumulator.bind(
                lambda _value, target=target, text=text: fs.write_text(
                    path=target, text=text,
                ).map(lambda _: seed_input),
            )
    return accumulator


def _emit_seed_proposed_change(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Auto-emit `<spec-root>/history/v001/proposed_changes/seed.md`.

    PROPOSAL.md §"`seed`" step 6 + "Auto-generated...seed.md
    content" (lines ~2043-2057): front-matter (topic, author,
    created_at) + a `## Proposal: seed` section listing target
    files, summary, motivation (verbatim intent), and proposed
    changes (verbatim intent). The auto-captured proposed-change
    lands ONLY in the main spec's history (sub-specs do not each
    get their own — the single main-spec seed artifact documents
    the whole multi-tree creation per the spec).
    """
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < 2:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    target_files_block = "\n".join(
        f"- {entry['path']}" for entry in seed_input.files
    )
    body = (
        "---\n"
        "topic: seed\n"
        "author: livespec-seed\n"
        "---\n"
        "\n"
        "## Proposal: seed\n"
        "\n"
        "### Target specification files\n"
        "\n"
        f"{target_files_block}\n"
        "\n"
        "### Summary\n"
        "\n"
        "Initial seed of the specification from user-provided intent.\n"
        "\n"
        "### Motivation\n"
        "\n"
        f"{seed_input.intent}\n"
        "\n"
        "### Proposed Changes\n"
        "\n"
        f"{seed_input.intent}\n"
    )
    target = (
        project_root
        / spec_root_name
        / "history"
        / "v001"
        / "proposed_changes"
        / "seed.md"
    )
    return fs.write_text(path=target, text=body).map(lambda _: seed_input)


def _emit_seed_revision(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Auto-emit `<spec-root>/history/v001/proposed_changes/seed-revision.md`.

    PROPOSAL.md §"`seed`" "Auto-generated seed-revision.md"
    (lines ~2058-2064): front-matter `proposal: seed.md`,
    `decision: accept`, `author_llm: livespec-seed`, with
    `## Decision and Rationale` paragraph ("auto-accepted during
    seed") and `## Resulting Changes` enumerating every seed-
    written file. revised_at matches the paired seed.md's
    created_at; author_human resolves to the git user or
    "unknown" — both deferred to subsequent cycles where the
    `created_at` timestamp + git-user lookup are formalized.
    """
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < 2:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    resulting_changes = "\n".join(
        f"- {entry['path']}" for entry in seed_input.files
    )
    body = (
        "---\n"
        "proposal: seed.md\n"
        "decision: accept\n"
        "author_llm: livespec-seed\n"
        "author_human: unknown\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        "auto-accepted during seed\n"
        "\n"
        "## Resulting Changes\n"
        "\n"
        f"{resulting_changes}\n"
    )
    target = (
        project_root
        / spec_root_name
        / "history"
        / "v001"
        / "proposed_changes"
        / "seed-revision.md"
    )
    return fs.write_text(path=target, text=body).map(lambda _: seed_input)


def _write_sub_spec_history_v001(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Materialize history/v001/ for each sub-spec tree.

    PROPOSAL.md §"`seed`" step 5 (line ~2014-2020): "For each
    sub-spec tree, create
    SPECIFICATION/templates/<template_name>/history/v001/
    alongside the main-spec history — including the sub-spec's
    own versioned spec files..." Sub-spec spec_root is the
    first three path components (e.g.,
    `SPECIFICATION/templates/livespec`); the remainder is the
    spec-file path beneath it.
    """
    accumulator: IOResult[SeedInput, LivespecError] = IOResult.from_value(seed_input)
    for sub_spec in seed_input.sub_specs:
        files_list = sub_spec["files"]
        if not isinstance(files_list, list):
            continue
        for entry in files_list:
            if not isinstance(entry, dict):
                continue
            original_path = Path(str(entry["path"]))
            if len(original_path.parts) < 4:
                continue
            spec_root_parts = original_path.parts[:3]
            relative = Path(*original_path.parts[3:])
            target = (
                project_root.joinpath(*spec_root_parts)
                / "history"
                / "v001"
                / relative
            )
            text = str(entry["content"])
            accumulator = accumulator.bind(
                lambda _value, target=target, text=text: fs.write_text(
                    path=target, text=text,
                ).map(lambda _: seed_input),
            )
    return accumulator


def _pattern_match_io_result(
    *,
    io_result: IOResult[Any, LivespecError],
) -> int:
    """Pattern-match the final railway IOResult onto an exit code.

    Success(<value>) -> exit 0 per style doc §"Exit code
    contract". Failure(LivespecError) lifts via the error's
    err.exit_code attribute; assert_never closes the match.
    """
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd().

    PROPOSAL.md §"Wrapper CLI surface" lines 349-356: every
    wrapper that operates on project state accepts
    --project-root <path> with default Path.cwd(). The default
    is applied here at the supervisor edge (not at the parser
    layer) to keep the parser pure-data and the cwd-read inside
    the supervisor's effectful boundary.
    """
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def main(*, argv: list[str]) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    Threads argv through the railway:
      parse_argv -> read --seed-json file -> jsonc.loads ->
      validate_seed_input -> write .livespec.jsonc

    UsageError (parse) -> exit 2; PreconditionError (missing
    file) -> exit 3; ValidationError (malformed payload or
    schema violation) -> exit 4; success path now writes
    .livespec.jsonc and returns through the success branch.
    """
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=argv)
    railway: IOResult[Any, LivespecError] = parse_result.bind(
        lambda namespace: (
            _load_seed_json(namespace=namespace)
            .bind(lambda text: _parse_payload(text=text))
            .bind(lambda payload: _validate_payload(payload=payload))
            .bind(
                lambda seed_input: _write_livespec_config(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _write_main_spec_files(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _write_sub_spec_files(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _write_main_spec_history_v001(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _write_sub_spec_history_v001(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _emit_seed_proposed_change(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _emit_seed_revision(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)
