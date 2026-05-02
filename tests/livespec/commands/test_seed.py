"""Tests for livespec.commands.seed.

The seed sub-command is the Phase 3 outermost rail per the
briefing's outside-in walking direction. Cycles drive its
behavior step-by-step from the supervisor entrypoint
(`main(argv)`) inward.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.commands import seed

__all__: list[str] = []


def _write_valid_seed_payload(
    *,
    tmp_path: Path,
    sub_specs: list[dict[str, object]] | None = None,
) -> Path:
    """Helper: write a schema-valid seed-input payload to tmp_path.

    Used by success-arm tests to satisfy the parse_argv ->
    read_text -> jsonc.loads -> validate_seed_input chain so the
    railway reaches the file-shaping stages without short-
    circuiting on the earlier failure rails. When `sub_specs`
    is supplied, the payload's sub_specs[] carries those entries
    (otherwise empty per the v020 Q2 default).
    """
    payload_dict = {
        "template": "livespec",
        "intent": "Demo intent text.",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "# Spec\n"},
        ],
        "sub_specs": sub_specs if sub_specs is not None else [],
    }
    payload_path = tmp_path / "seed-input.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    return payload_path


def test_seed_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/seed.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Subsequent cycles widen the body
    behavior-by-behavior.
    """
    exit_code = seed.main(argv=["--seed-json", "/tmp/x.json"])
    assert isinstance(exit_code, int)


def test_seed_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing --seed-json (UsageError) returns exit code 2.

    Threads argv through io/cli.parse_argv and pattern-matches
    the IOFailure(UsageError) onto its err.exit_code per style
    doc §"Exit code contract". Drives seed.main's first real
    railway-composition behavior.
    """
    exit_code = seed.main(argv=[])
    assert exit_code == 2


def test_seed_main_returns_precondition_exit_code_on_missing_seed_json_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --seed-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to seed.main's pattern-match, which lifts to exit 3
    via err.exit_code per style doc §"Exit code contract".
    """
    missing = tmp_path / "no-such-payload.json"
    exit_code = seed.main(argv=["--seed-json", str(missing)])
    assert exit_code == 3


def test_seed_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) reaches
    seed.main's pattern-match through bind chaining; exit 4
    per style doc §"Exit code contract".
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = seed.main(argv=["--seed-json", str(payload)])
    assert exit_code == 4


def test_seed_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives seed.main's railway widening to include schema
    validation: parse_argv -> read_text -> jsonc.loads ->
    validate_seed_input. The payload `{}` is valid JSON so
    jsonc.loads succeeds; it then trips schema validation
    (missing required `template`/`intent`/`files`/`sub_specs`)
    which returns Failure(ValidationError) and lifts to exit 4.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = seed.main(argv=["--seed-json", str(payload)])
    assert exit_code == 4


def test_seed_main_defaults_argv_to_sys_argv_when_called_without_args(
    *,
    monkeypatch: object,
) -> None:
    """`main()` (no args) defaults argv to `sys.argv[1:]`.

    The bin/seed.py wrapper invokes `main()` per the canonical
    6-statement wrapper shape (style doc §"Wrapper shape"). The
    supervisor must therefore read sys.argv[1:] when no argv
    is supplied, otherwise the wrapper raises TypeError on
    missing keyword argument. Drives the default-argv contract
    that the wrapper depends on.
    """
    import sys as _sys

    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setattr(_sys, "argv", ["seed.py"])
    exit_code = seed.main()
    assert exit_code == 2
    """The pure argparse factory accepts `--seed-json <path>` and binds it.

    Per PROPOSAL.md §"`seed`" lines 1937-1942 (`bin/seed.py
    --seed-json <path>` is the sole wrapper entry point) and
    style doc §"CLI argument parsing seam" (commands/<cmd>.py
    exposes a pure `build_parser() -> ArgumentParser` factory
    that constructs but does NOT parse). Constructing-only lets
    us introspect the parser shape without effectful invocation.
    """
    parser = seed.build_parser()
    namespace = parser.parse_args(["--seed-json", "/tmp/payload.json"])
    assert namespace.seed_json == "/tmp/payload.json"


def test_seed_main_writes_livespec_jsonc_at_project_root_on_success(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed writes `<project-root>/.livespec.jsonc` with the template.

    Per PROPOSAL.md §"`seed`" step 1 (line ~1996): the wrapper
    writes `.livespec.jsonc` at repo root using the payload's
    top-level `template` field value. This is the first
    deterministic file-shaping stage — drives the success-arm
    out of the cycle-76 stub-1 return into a real materialized
    output.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    config_path = project_root / ".livespec.jsonc"
    assert config_path.exists(), f"expected {config_path} to be written"
    assert "livespec" in config_path.read_text(encoding="utf-8")


def test_seed_main_writes_main_spec_files_at_their_paths(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed writes each main-spec `files[]` entry to its path.

    Per PROPOSAL.md §"`seed`" step 2 (line ~1999): "Write each
    main-spec `files[]` entry to its specified path." Each
    entry's `path` is project-root-relative; content goes
    verbatim. Drives the second deterministic file-shaping
    stage out of the railway's success arm.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    spec_path = project_root / "SPECIFICATION" / "spec.md"
    assert spec_path.exists(), f"expected {spec_path} to be written"
    assert spec_path.read_text(encoding="utf-8") == "# Spec\n"


def test_seed_main_writes_sub_spec_files_at_their_paths(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed writes each sub-spec entry's `files[]` to its path.

    Per PROPOSAL.md §"`seed`" step 3 (line ~2000): "For each
    entry in `sub_specs[]`, write every `files[]` entry in
    that sub-spec to its
    `SPECIFICATION/templates/<template_name>/<spec-file>` path."
    Sub-spec trees are written alongside the main tree;
    failure of any sub-spec write rolls back the entire seed
    (partial-write refusal).
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    sub_specs = [
        {
            "template_name": "livespec",
            "files": [
                {
                    "path": "SPECIFICATION/templates/livespec/spec.md",
                    "content": "# Sub-spec spec\n",
                },
            ],
        },
    ]
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path, sub_specs=sub_specs)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    sub_spec_path = project_root / "SPECIFICATION/templates/livespec/spec.md"
    assert sub_spec_path.exists(), f"expected {sub_spec_path} to be written"
    assert sub_spec_path.read_text(encoding="utf-8") == "# Sub-spec spec\n"


def test_seed_main_creates_history_v001_with_versioned_main_spec_files(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed materializes `<spec-root>/history/v001/<spec-file>`.

    Per PROPOSAL.md §"`seed`" step 4 (line ~2007): "Create
    `<spec-root>/history/v001/` for the main spec (including
    the initial versioned spec files...)." With the built-in
    `livespec` template's spec_root = `SPECIFICATION/`, each
    main-spec file at `SPECIFICATION/<file>` gets a versioned
    snapshot at `SPECIFICATION/history/v001/<file>` carrying
    the same content (the v001 baseline).
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    versioned = project_root / "SPECIFICATION/history/v001/spec.md"
    assert versioned.exists(), f"expected {versioned} to be written"
    assert versioned.read_text(encoding="utf-8") == "# Spec\n"


def test_seed_main_creates_sub_spec_history_v001(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed materializes sub-spec history/v001/ for each sub-spec tree.

    Per PROPOSAL.md §"`seed`" step 5 (line ~2014-2020): "For
    each sub-spec tree, create
    SPECIFICATION/templates/<template_name>/history/v001/
    alongside the main-spec history — including the sub-spec's
    own versioned spec files..." Each sub-spec entry's files
    get a v001 snapshot beneath the sub-spec's spec_root.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    sub_specs = [
        {
            "template_name": "livespec",
            "files": [
                {
                    "path": "SPECIFICATION/templates/livespec/spec.md",
                    "content": "# Sub-spec spec\n",
                },
            ],
        },
    ]
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path, sub_specs=sub_specs)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    versioned = (
        project_root / "SPECIFICATION/templates/livespec/history/v001/spec.md"
    )
    assert versioned.exists(), f"expected {versioned} to be written"
    assert versioned.read_text(encoding="utf-8") == "# Sub-spec spec\n"


def test_seed_main_emits_auto_captured_seed_proposed_change(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed writes `<spec-root>/history/v001/proposed_changes/seed.md`.

    Per PROPOSAL.md §"`seed`" step 6 (line ~2029) and the
    "Auto-generated...seed.md content" subsection (line ~2043):
    the wrapper writes a proposed-change file with front-matter
    `topic: seed`, `author: livespec-seed`, plus a
    `## Proposal: seed` section. Drives the smallest visible
    behavior: the file exists with the topic-front-matter line.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    seed_md = project_root / "SPECIFICATION/history/v001/proposed_changes/seed.md"
    assert seed_md.exists(), f"expected {seed_md} to be written"
    text = seed_md.read_text(encoding="utf-8")
    assert "topic: seed" in text
    assert "author: livespec-seed" in text
    assert "## Proposal: seed" in text


def test_seed_main_emits_auto_captured_seed_revision(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed writes `<spec-root>/history/v001/proposed_changes/seed-revision.md`.

    Per PROPOSAL.md §"`seed`" "Auto-generated...seed-revision.md"
    (lines ~2058-2064): front-matter `proposal: seed.md`,
    `decision: accept`, `author_llm: livespec-seed`, with
    `## Decision and Rationale` paragraph "auto-accepted during
    seed" and `## Resulting Changes`. Drives the smallest visible
    behavior: the file exists with the canonical front-matter
    + section markers.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    _ = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    revision_md = (
        project_root
        / "SPECIFICATION/history/v001/proposed_changes/seed-revision.md"
    )
    assert revision_md.exists(), f"expected {revision_md} to be written"
    text = revision_md.read_text(encoding="utf-8")
    assert "proposal: seed.md" in text
    assert "decision: accept" in text
    assert "author_llm: livespec-seed" in text
    assert "## Decision and Rationale" in text
    assert "## Resulting Changes" in text


def test_seed_main_returns_exit_zero_on_successful_seed(
    *,
    tmp_path: Path,
) -> None:
    """Successful seed returns exit code 0.

    Per style doc §"Exit code contract": exit 0 is the canonical
    success exit. Drives the supervisor's pattern-match success
    branch from the cycle-76 stub `1` to the real `0`. Composes
    the now-complete success arm: parse_argv -> read_text ->
    jsonc.loads -> validate_seed_input -> write .livespec.jsonc
    -> Success(SeedInput) -> exit 0.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    exit_code = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    assert exit_code == 0


def test_seed_build_parser_accepts_project_root_flag() -> None:
    """The argparse factory accepts `--project-root <path>` and binds it.

    Per PROPOSAL.md §"Wrapper CLI surface" (lines 349-356):
    every wrapper that operates on project state accepts
    `--project-root <path>` as an optional CLI flag with default
    `Path.cwd()`. Seed uses this to anchor `.livespec.jsonc`
    placement (the file is written at `<project-root>/.livespec.jsonc`
    per §"`seed`" step 1).
    """
    parser = seed.build_parser()
    namespace = parser.parse_args(
        ["--seed-json", "/tmp/payload.json", "--project-root", "/tmp/proj"],
    )
    assert namespace.project_root == "/tmp/proj"


def test_write_sub_spec_history_v001_skips_paths_with_fewer_than_four_components(
    *,
    tmp_path: Path,
) -> None:
    """A sub_spec file path with fewer than 4 components is skipped from history/v001/.

    Per `_write_sub_spec_history_v001` line 354-355 guard: the
    canonical sub-spec file shape is
    `SPECIFICATION/templates/<name>/<spec-file>` (4 path
    components). A path with fewer components can't be split into
    `spec_root_parts = parts[:3]` plus a remainder — `parts[3:]`
    would be empty, producing a malformed v001 target. The guard
    skips that entry rather than constructing a malformed path.
    Tested by calling the helper directly with a sub_spec entry
    whose path is `SPECIFICATION/templates/spec.md` (3 parts —
    one too few). The IOResult is Success, the malformed entry's
    history is silently omitted, and a second well-formed entry's
    v001 snapshot still lands.
    """
    from livespec.commands.seed import _write_sub_spec_history_v001
    from livespec.schemas.dataclasses.seed_input import SeedInput
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/spec.md",
                        "content": "# Too few components\n",
                    },
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Sub\n",
                    },
                ],
            },
        ],
    )
    result = _write_sub_spec_history_v001(
        seed_input=seed_input, project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    versioned = (
        project_root / "SPECIFICATION/templates/livespec/history/v001/spec.md"
    )
    assert versioned.exists(), f"the well-formed entry should still produce v001"


def test_write_sub_spec_history_v001_skips_non_dict_entry_inside_files_list(
    *,
    tmp_path: Path,
) -> None:
    """A non-dict entry inside a sub_spec's `files` is skipped from history/v001/.

    Per `_write_sub_spec_history_v001` line 351-352 guard: the
    inner-loop `if not isinstance(entry, dict): continue`. Mirror
    of cycle 109's pattern in the sub-spec history-materialization
    helper. Tested by calling the helper directly with a sub-spec
    whose `files` list mixes a non-dict (None) with a well-formed
    entry — the IOResult is Success, the well-formed entry's v001
    snapshot still lands, the None is silently skipped.
    """
    from livespec.commands.seed import _write_sub_spec_history_v001
    from livespec.schemas.dataclasses.seed_input import SeedInput
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {
                "template_name": "livespec",
                "files": [
                    None,
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Sub\n",
                    },
                ],
            },
        ],
    )
    result = _write_sub_spec_history_v001(
        seed_input=seed_input, project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    versioned = (
        project_root / "SPECIFICATION/templates/livespec/history/v001/spec.md"
    )
    assert versioned.exists(), f"well-formed entry should still produce v001"


def test_write_sub_spec_history_v001_skips_entries_with_non_list_files_field(
    *,
    tmp_path: Path,
) -> None:
    """A sub_spec whose `files` is not a list is skipped from history/v001/.

    Per `_write_sub_spec_history_v001` line 348-349 guard: same
    type-defensive pattern as cycle 108's `_write_sub_spec_files`,
    but in the sub-spec-history-materialization helper. The
    dataclass surface still types each sub-spec's `files` value as
    `object` even though schema validation guarantees a list.
    Tested by calling the helper directly with a malformed sub-spec
    (`files` is a string); the IOResult is Success and the
    well-formed second sub-spec's history copy still lands.
    """
    from livespec.commands.seed import _write_sub_spec_history_v001
    from livespec.schemas.dataclasses.seed_input import SeedInput
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {"template_name": "broken", "files": "not-a-list"},
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Sub\n",
                    },
                ],
            },
        ],
    )
    result = _write_sub_spec_history_v001(
        seed_input=seed_input, project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    versioned = (
        project_root / "SPECIFICATION/templates/livespec/history/v001/spec.md"
    )
    assert versioned.exists(), f"the well-formed sub-spec should still produce v001"


def test_write_sub_spec_files_skips_non_dict_entry_inside_files_list(
    *,
    tmp_path: Path,
) -> None:
    """A non-dict entry inside a sub_spec's `files` list is skipped defensively.

    Per `_write_sub_spec_files` line 204-205 guard: inside the
    per-sub-spec `files` iteration, each entry must be a dict
    before its `path`/`content` keys can be read. The dataclass
    surface types each entry as `object` (the inner items live
    behind the `dict[str, object]` value of the outer sub-spec
    dict), so pyright strict-mode requires a runtime narrowing
    check before subscripting. Schema validation guarantees this
    never fires under the canonical seed flow, so the test calls
    the helper directly with a sub_spec whose `files` list mixes
    a non-dict (`None`) with a well-formed entry — the IOResult
    is Success and only the well-formed entry is written.
    """
    from livespec.commands.seed import _write_sub_spec_files
    from livespec.schemas.dataclasses.seed_input import SeedInput
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {
                "template_name": "livespec",
                "files": [
                    None,
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Sub\n",
                    },
                ],
            },
        ],
    )
    result = _write_sub_spec_files(seed_input=seed_input, project_root=project_root)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    well_formed = project_root / "SPECIFICATION/templates/livespec/spec.md"
    assert well_formed.exists(), f"well-formed entry should still be written"


def test_write_sub_spec_files_skips_entries_with_non_list_files_field(
    *,
    tmp_path: Path,
) -> None:
    """A sub_spec whose `files` is not a list is skipped defensively.

    Per `_write_sub_spec_files` line 201-202 guard: the supervisor
    is type-defensive against the dataclass's
    `sub_specs: list[dict[str, object]]` typing, where the inner
    dict's values are `object`. Schema validation guarantees
    `files` is a list at runtime, but the static type permits any
    object — so the helper carries an `isinstance(files_list, list)`
    runtime check to keep pyright strict-mode happy AND to cope
    with a hypothetical future caller that bypasses validation.
    The guard's contract: skip the malformed sub-spec entry, let
    the rest of the seed flow proceed.

    Tested by calling the helper directly with a hand-built
    `SeedInput` carrying a sub_spec whose `files` value is a
    non-list (a string here). The IOResult must succeed
    (Success(seed_input)) — the sub-spec is silently skipped and
    the railway keeps composing. Tests the guard's selectivity
    too: a second well-formed sub-spec entry's files DO get
    written.
    """
    from livespec.commands.seed import _write_sub_spec_files
    from livespec.schemas.dataclasses.seed_input import SeedInput
    from returns.unsafe import unsafe_perform_io
    from returns.result import Success

    project_root = tmp_path / "proj"
    project_root.mkdir()
    seed_input = SeedInput(
        template="livespec",
        intent="x",
        files=[],
        sub_specs=[
            {"template_name": "broken", "files": "not-a-list"},
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "# Sub\n",
                    },
                ],
            },
        ],
    )
    result = _write_sub_spec_files(seed_input=seed_input, project_root=project_root)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success), f"expected Success, got {unwrapped!r}"
    well_formed = project_root / "SPECIFICATION/templates/livespec/spec.md"
    assert well_formed.exists(), f"the second sub-spec's file should still be written"


def test_seed_main_skips_seed_md_emission_when_files_array_is_empty(
    *,
    tmp_path: Path,
) -> None:
    """An empty `files[]` array short-circuits the seed.md / seed-revision.md emission.

    Per `_emit_seed_proposed_change` line 232-233 + `_emit_seed_revision`
    line 293-294 guards: when the payload carries no main-spec
    `files[]`, both auto-captured-proposed-change emission and
    auto-revision emission early-return with the unchanged
    seed_input. The body of those files derives a target path
    from `seed_input.files[0]["path"]` — which would IndexError
    on an empty list. The guards avoid that IndexError and let
    the seed file-shaping flow complete; only the seed.md /
    seed-revision.md history artifacts are omitted.

    With post-step doctor wired (cycle 145), the supervisor exit
    code is 3 (NOT 0): the empty `files[]` payload produces a
    skeletal `<project-root>/.livespec.jsonc` with NO spec tree
    materialized, so the doctor's `template_files_present` check
    fails when reading `<spec-root>/spec.md`. The defensive
    guards' contract is preserved (no IndexError, no malformed
    paths) — the seed-write side-effects all complete BEFORE the
    post-step doctor short-circuits the supervisor with exit 3.
    Negative assertions still pin the guard behavior: no
    seed.md / seed-revision.md emitted.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_dict: dict[str, object] = {
        "template": "livespec",
        "intent": "Demo intent text.",
        "files": [],
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed-input.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    exit_code = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    assert exit_code == 3, (
        f"expected exit 3 (post-step doctor fail on empty seed tree), got {exit_code}"
    )
    # Negative assertions: with no files[] entries, neither auto-
    # captured artifact is materialized (no spec_root to anchor
    # the path against). The guards' selectivity is preserved
    # despite the supervisor's exit-3 short-circuit.
    seed_md_candidates = list(project_root.rglob("seed.md"))
    revision_md_candidates = list(project_root.rglob("seed-revision.md"))
    assert seed_md_candidates == [], (
        f"empty files[] should skip seed.md emission; found {seed_md_candidates}"
    )
    assert revision_md_candidates == [], (
        f"empty files[] should skip seed-revision.md emission; "
        f"found {revision_md_candidates}"
    )


def test_seed_main_skips_main_spec_history_for_single_component_paths(
    *,
    tmp_path: Path,
) -> None:
    """A main-spec `files[]` entry with a single-component path is skipped from history/v001/.

    Per `_write_main_spec_history_v001` line 168-169 guard: when
    a file's project-root-relative path has fewer than 2
    components (e.g., `loose-file.md` directly at the project
    root, with no `<spec-root>/<file>` shape), it cannot be
    derived to a `<spec-root>/history/v001/<remainder>` path —
    the spec_root would be the file itself with no remainder
    inside it. The supervisor's history-materialization stage
    skips that entry rather than constructing a malformed v001
    path. Only the history copy of that loose file is omitted
    (the well-formed entry's history still lands).

    With post-step doctor wired (cycle 145), the supervisor exit
    code is 3 (NOT 0): the skill-owned README emission anchors
    on `seed_input.files[0]["path"]`, which is the loose
    single-component file in this fixture, so the README's
    early-return guard fires and `<spec-root>/proposed_changes/`
    is never materialized. The doctor's
    `proposed_changes_and_history_dirs` check therefore fails
    on the seeded tree. The test still pins the file-shaping
    guard's selectivity: the well-formed entry's
    SPECIFICATION/history/v001/spec.md DOES land, and the loose
    file's spurious history dir does NOT.
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_dict = {
        "template": "livespec",
        "intent": "Demo intent text.",
        "files": [
            {"path": "loose-file.md", "content": "# Loose\n"},
            {"path": "SPECIFICATION/spec.md", "content": "# Spec\n"},
        ],
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed-input.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    exit_code = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    assert exit_code == 3, (
        f"expected exit 3 (post-step doctor fail on incomplete tree), got {exit_code}"
    )
    versioned = project_root / "SPECIFICATION/history/v001/spec.md"
    assert versioned.exists(), f"expected {versioned} to be written"
    # The single-component file's history copy is omitted; verify the
    # plausible-but-incorrect target was NOT materialized.
    spurious = project_root / "loose-file.md/history/v001"
    assert not spurious.exists(), f"single-component path should not produce history dir"


def test_fold_doctor_completed_process_returns_failure_on_malformed_json_stdout(
    *,
    tmp_path: Path,
) -> None:
    """Malformed-JSON stdout from the doctor subprocess -> Failure(PreconditionError).

    Per `_fold_doctor_completed_process` line 510-515 guard: the
    doctor wrapper's documented stdout contract is a single
    `{"findings": [...]}` JSON object (PROPOSAL.md §"`doctor` →
    Static-phase output contract"). If stdout cannot be decoded
    by `json.loads`, the doctor's contract was violated and seed
    cannot proceed — the helper lifts the json.ValueError catch
    into a Failure(PreconditionError) so the supervisor pattern-
    matches it onto exit 3 via err.exit_code.

    Tested by calling the helper directly with a hand-built
    CompletedProcess whose stdout is `not json {`. The IOResult
    is Failure(PreconditionError); the supervisor's exit-code
    contract folds it to 3.
    """
    import subprocess as _subprocess  # noqa: S404  # test-only import for the dataclass shape
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    from livespec.commands.seed import _fold_doctor_completed_process
    from livespec.errors import PreconditionError
    from livespec.schemas.dataclasses.seed_input import SeedInput

    _ = tmp_path  # fixture present for symmetry; helper does not touch the disk
    seed_input = SeedInput(
        template="livespec", intent="x", files=[], sub_specs=[],
    )
    completed = _subprocess.CompletedProcess[str](
        args=["doctor"], returncode=0, stdout="not json {", stderr="",
    )
    result = _fold_doctor_completed_process(
        seed_input=seed_input, completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected Failure(PreconditionError), got {unwrapped!r}",
            )


def test_fold_doctor_completed_process_returns_failure_on_missing_findings_key(
    *,
    tmp_path: Path,
) -> None:
    """Doctor stdout JSON without a `findings` key -> Failure(PreconditionError).

    Per `_fold_doctor_completed_process` line 516-521 guard: the
    payload must be a dict carrying a `findings` key. A non-dict
    payload (e.g., a JSON array at the root) or a dict missing
    the `findings` key both signal a contract violation; the
    helper lifts to Failure(PreconditionError).

    Tested by calling the helper directly with stdout `{}` —
    valid JSON, decodes to a dict, but lacks the `findings` key.
    """
    import subprocess as _subprocess  # noqa: S404
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    from livespec.commands.seed import _fold_doctor_completed_process
    from livespec.errors import PreconditionError
    from livespec.schemas.dataclasses.seed_input import SeedInput

    _ = tmp_path
    seed_input = SeedInput(
        template="livespec", intent="x", files=[], sub_specs=[],
    )
    completed = _subprocess.CompletedProcess[str](
        args=["doctor"], returncode=0, stdout="{}", stderr="",
    )
    result = _fold_doctor_completed_process(
        seed_input=seed_input, completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected Failure(PreconditionError), got {unwrapped!r}",
            )


def test_fold_doctor_completed_process_returns_failure_on_non_list_findings(
    *,
    tmp_path: Path,
) -> None:
    """Doctor stdout `{"findings": <not-a-list>}` -> Failure(PreconditionError).

    Per `_fold_doctor_completed_process` line 522-528 guard: the
    `findings` value MUST be a list per the doctor contract.
    Any other shape (dict, string, number) signals a contract
    violation; the helper lifts to Failure(PreconditionError).

    Tested by calling the helper directly with stdout
    `{"findings": "oops"}` — a JSON string at the findings key
    instead of a list.
    """
    import subprocess as _subprocess  # noqa: S404
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    from livespec.commands.seed import _fold_doctor_completed_process
    from livespec.errors import PreconditionError
    from livespec.schemas.dataclasses.seed_input import SeedInput

    _ = tmp_path
    seed_input = SeedInput(
        template="livespec", intent="x", files=[], sub_specs=[],
    )
    completed = _subprocess.CompletedProcess[str](
        args=["doctor"], returncode=0, stdout='{"findings": "oops"}', stderr="",
    )
    result = _fold_doctor_completed_process(
        seed_input=seed_input, completed=completed,
    )
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(
                f"expected Failure(PreconditionError), got {unwrapped!r}",
            )


def test_seed_main_invokes_post_step_doctor_and_returns_exit_three_on_fail_finding(
    *,
    tmp_path: Path,
) -> None:
    """After seed completes, post-step doctor runs; any fail finding -> exit 3.

    Per PROPOSAL.md §"Sub-command lifecycle orchestration" lines
    767-773 + §"`seed`" lines 2037-2042: "Seed is exempt from
    pre-step doctor-static; post-step runs normally after the
    wrapper's deterministic work completes." On any `status:
    "fail"` finding from post-step, the wrapper aborts with exit
    3 after sub-command logic has already mutated on-disk state.

    Composition mechanism (cycle 144 + cycle 145): the supervisor
    invokes `bin/doctor_static.py` as a subprocess via
    `livespec.io.proc.run_subprocess` — chosen over direct
    in-process import because the layered-architecture import-
    linter contract `livespec.commands | livespec.doctor`
    treats the two layers as independent siblings that cannot
    import each other.

    The fixture uses `template: "unknown-template-name"` —
    schema-valid (the schema's `template` is a free-form string)
    so the seed-input validation stage doesn't short-circuit, but
    the doctor's `template_exists` check rejects it (not in
    BUILTIN_TEMPLATES, not a path on disk) and yields a
    fail-status Finding. Post-step doctor therefore reports at
    least one fail-status finding -> seed exits 3.

    Asserts the seed-write side-effects DID happen (sub-command
    logic ran to completion BEFORE the post-step doctor failure
    short-circuited the supervisor) — `.livespec.jsonc` and
    `SPECIFICATION/spec.md` exist on disk. This pins the
    lifecycle contract: "post-step failure aborts AFTER
    sub-command logic has mutated state."
    """
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_dict: dict[str, object] = {
        "template": "unknown-template-name",
        "intent": "Demo intent text.",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "# Spec\n"},
        ],
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed-input.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    exit_code = seed.main(
        argv=["--seed-json", str(payload_path), "--project-root", str(project_root)],
    )
    assert exit_code == 3, (
        f"expected exit 3 (post-step doctor fail), got {exit_code}"
    )
    config_path = project_root / ".livespec.jsonc"
    assert config_path.exists(), (
        "sub-command logic should have written .livespec.jsonc BEFORE "
        "post-step doctor short-circuited the supervisor"
    )
    spec_path = project_root / "SPECIFICATION" / "spec.md"
    assert spec_path.exists(), (
        "sub-command logic should have written SPECIFICATION/spec.md "
        "BEFORE post-step doctor short-circuited the supervisor"
    )


def test_seed_main_defaults_project_root_to_cwd_when_flag_omitted(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """Without --project-root, the supervisor defaults to `Path.cwd()`.

    Per PROPOSAL.md §"Wrapper CLI surface" lines 349-356: every
    wrapper accepts `--project-root <path>` with the default
    applied at the supervisor edge as `Path.cwd()` (NOT at the
    parser layer; the parser keeps default=None so the supervisor
    is the single place the cwd-read happens). Drives
    `_resolve_project_root`'s cwd-fallback branch (line 404:
    `if namespace.project_root is None: return Path.cwd()`).
    `monkeypatch.chdir(project_root)` anchors the cwd at a writable
    deterministic location so the seed flow's full success arm
    materializes there.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    project_root = tmp_path / "proj"
    project_root.mkdir()
    payload_path = _write_valid_seed_payload(tmp_path=tmp_path)
    monkeypatch.chdir(project_root)
    exit_code = seed.main(argv=["--seed-json", str(payload_path)])
    assert exit_code == 0
    config_path = project_root / ".livespec.jsonc"
    assert config_path.exists(), f"expected {config_path} to be written under cwd"


def test_path_minima_constants_pin_documented_shapes() -> None:
    """The `_MIN_PARTS_*` constants pin path-shape minima.

    A main-spec path is `<spec_root>/<file>` (≥ 2 parts); a
    sub-spec path is `<spec_root>/templates/<template_name>/<file>`
    (≥ 4 parts). This test pins those values in code so a future
    deepening of either layout requires explicit test failure +
    intentional bump.
    """
    assert seed._MIN_PARTS_MAIN_SPEC == 2  # noqa: SLF001
    assert seed._MIN_PARTS_SUB_SPEC == 4  # noqa: SLF001
