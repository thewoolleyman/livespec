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
import json as _json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Failure, Success, safe
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError, PreconditionError
from livespec.io import cli, fs, proc
from livespec.parse import jsonc
from livespec.schemas.dataclasses.seed_input import SeedInput
from livespec.validate import seed_input as validate_seed_input_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_SEED_INPUT_SCHEMA_PATH = _SCHEMAS_DIR / "seed_input.schema.json"
_BIN_DIR = Path(__file__).resolve().parents[2] / "bin"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"

# Path-shape minima for spec-file path validation. A main-spec path
# is `<spec_root>/<file>` (≥ 2 parts); a sub-spec path is
# `<spec_root>/templates/<template_name>/<file>` (≥ 4 parts).
# Paths shorter than these minima are silently skipped — the seed
# payload's schema doesn't enforce path-shape, so the supervisor
# defends against malformed entries here.
_MIN_PARTS_MAIN_SPEC: int = 2
_MIN_PARTS_SUB_SPEC: int = 4


_PROPOSED_CHANGES_README_TEXT = (
    "# Proposed Changes\n"
    "\n"
    "This directory holds in-flight proposed changes to the\n"
    "specification. Each file is named `<topic>.md` and contains\n"
    "one or more `## Proposal: <name>` sections with target\n"
    "specification files, summary, motivation, and proposed\n"
    "changes (prose or unified diff). Files are processed by\n"
    "`livespec revise` in creation-time order (YAML `created_at`\n"
    "front-matter field) and moved into\n"
    "`../history/vNNN/proposed_changes/` when revised. After a\n"
    "successful `revise`, this directory is empty.\n"
)


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
        if len(original_path.parts) < _MIN_PARTS_MAIN_SPEC:
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
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
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
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
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
            if len(original_path.parts) < _MIN_PARTS_SUB_SPEC:
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


def _emit_skill_owned_proposed_changes_readme(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<spec-root>/proposed_changes/README.md` (skill-owned dir marker).

    PROPOSAL.md lines 992-994: "The directory-README files in
    top-level `proposed_changes/` and `history/` are skill-owned:
    hard-coded inside the skill, written by `seed` only, not
    regenerated on every `revise`." Frozen content is in
    PROPOSAL.md lines 997-1009.

    Phase-3 minimum scope (this cycle): only the
    `<spec-root>/proposed_changes/README.md` is materialized.
    The dir's existence is what makes the post-step doctor's
    `proposed_changes_and_history_dirs` check pass on the
    minimally-seeded tree. The `<spec-root>/history/README.md`
    skill-owned README is intentionally deferred to Phase 7
    hardening: under the current Phase-3 minimum-subset doctor,
    `version_directories_complete` does not yet filter out
    non-directory entries when listing `history/`, so writing
    the README would trip the check on a freshly-seeded tree.
    Phase 7 widens the check (filter to directory + vNNN
    pattern) AND adds the `history/README.md` emission here.

    Empty `files[]` short-circuits to an unchanged Success —
    there's no spec_root to anchor against. Single-component
    first-file path also short-circuits (mirrors the existing
    `_emit_seed_proposed_change` guard at line 234-236).
    """
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    proposed_changes_readme = (
        project_root / spec_root_name / "proposed_changes" / "README.md"
    )
    return fs.write_text(
        path=proposed_changes_readme, text=_PROPOSED_CHANGES_README_TEXT,
    ).map(lambda _: seed_input)


def _run_post_step_doctor(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Invoke `bin/doctor_static.py` as a subprocess; fold fail findings -> Failure.

    Per PROPOSAL.md §"Sub-command lifecycle orchestration" lines
    767-773: "post-step doctor static" runs after sub-command
    logic. On any `status: "fail"` finding, the wrapper aborts
    with exit 3.

    Composition mechanism (cycle 145): subprocess invocation of
    `bin/doctor_static.py` via `livespec.io.proc.run_subprocess`.
    Chosen over direct in-process import because the layered-
    architecture import-linter contract `livespec.commands |
    livespec.doctor` treats the two layers as independent
    siblings that cannot import each other. Subprocess
    invocation respects that boundary while still letting
    `commands.<cmd>.main()` own the deterministic lifecycle per
    style doc lines 645-694.

    Pattern-match arms:

    - `proc.run_subprocess` itself fails (e.g., the wrapper file
      is missing) -> IOFailure(PreconditionError) bubbles up.
    - The subprocess ran but stdout is malformed JSON ->
      Failure(PreconditionError) lifted from the json.loads
      ValueError catch.
    - Any finding has `status == "fail"` ->
      Failure(PreconditionError) carries the count for the
      caller's diagnostic.
    - All findings pass -> IOSuccess(seed_input) and the
      supervisor's pattern-match emits exit 0.
    """
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_doctor_completed_process(
            seed_input=seed_input, completed=completed,
        ),
    )


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decorator-lifted strict-JSON decode for doctor's stdout contract.

    The `@safe(exceptions=(ValueError,))` decorator from
    `returns.result` catches `json.JSONDecodeError` (a
    `ValueError` subclass) inside the wrapper and returns
    `Failure(<exception>)`; the success path returns
    `Success(<parsed-value>)`. Per
    python-skill-script-style-requirements.md
    §"check-no-except-outside-io" the decorator-lifted form
    is the canonical replacement for explicit `try/except`
    in pure layers — the AST has no `Try` node, only a
    `Decorator` reference.
    """
    return _json.loads(text)


def _fold_doctor_completed_process(
    *,
    seed_input: SeedInput,
    completed: Any,
) -> IOResult[SeedInput, LivespecError]:
    """Parse the doctor subprocess's stdout JSON and fold findings into the railway.

    The doctor wrapper's documented stdout contract is a single
    `{"findings": [...]}` JSON object (per PROPOSAL.md §"`doctor`
    → Static-phase output contract"). This helper:

    1. Decodes stdout via the standard library `json` module
       (the doctor's output is strict JSON, not JSONC).
    2. Inspects each finding's `status` field. Any
       `status == "fail"` -> Failure(PreconditionError) on the
       railway, which the supervisor's pattern-match lifts to
       exit 3 via err.exit_code.
    3. Otherwise -> IOSuccess(seed_input) so the railway can
       continue (no more stages after post-step doctor; the
       supervisor's pattern-match emits exit 0).

    Malformed stdout or a missing `findings` key both lift to
    PreconditionError — the doctor's contract was violated, and
    seed cannot proceed.
    """
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor stdout malformed JSON: {parsed.failure()}",
            ),
        )
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return IOResult.from_failure(
            PreconditionError(
                "post-step doctor stdout missing 'findings' key",
            ),
        )
    findings_value = payload["findings"]
    if not isinstance(findings_value, list):
        return IOResult.from_failure(
            PreconditionError(
                "post-step doctor 'findings' is not a list",
            ),
        )
    fail_count = sum(
        1
        for finding in findings_value
        if isinstance(finding, dict) and finding.get("status") == "fail"
    )
    if fail_count > 0:
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor reported {fail_count} fail-status finding(s)",
            ),
        )
    return IOResult.from_value(seed_input)


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


def main(*, argv: list[str] | None = None) -> int:
    """Seed supervisor entry point. Returns the process exit code.

    When `argv` is None (the wrapper's default invocation per
    `raise SystemExit(main())`), defaults to sys.argv[1:] so the
    canonical 6-statement wrapper shape from style doc §"Wrapper
    shape" works without further plumbing. Tests pass argv
    explicitly to bypass sys.argv.

    Threads argv through the railway:
      parse_argv -> read --seed-json file -> jsonc.loads ->
      validate_seed_input -> write .livespec.jsonc -> ...

    UsageError (parse) -> exit 2; PreconditionError (missing
    file) -> exit 3; ValidationError (malformed payload or
    schema violation) -> exit 4; success path materializes the
    full seed-flow body and returns 0.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
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
            .bind(
                lambda seed_input: _emit_skill_owned_proposed_changes_readme(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
            .bind(
                lambda seed_input: _run_post_step_doctor(
                    seed_input=seed_input,
                    project_root=_resolve_project_root(namespace=namespace),
                ),
            )
        ),
    )
    return _pattern_match_io_result(io_result=railway)
