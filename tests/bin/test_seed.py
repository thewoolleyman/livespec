"""Outside-in integration test for `bin/seed.py` — Phase 3 exit-criterion rail.

Per Phase 5 plan §"Phase 3 — Minimum viable `livespec seed`" exit
criterion (lines 1578-1620) and PROPOSAL.md §"`seed`" (lines
1823-2133), invoking `seed.py --seed-json <path>` against a
throwaway tmp_path materializes — atomically, in one wrapper
invocation — `.livespec.jsonc` at repo root, the main spec tree
with `history/v001/`, and any sub-spec trees declared in the
payload's `sub_specs[]` array.

This module holds the OUTERMOST integration test for that
exit-criterion round-trip. Per the v032 D2 outside-in walking
direction, the failure point of this single test advances forward
across many TDD cycles: first the wrapper file does not exist
(FileNotFoundError); next, the supervisor stub exists but writes
nothing (`.livespec.jsonc` missing assertion); and so on until
every Phase 3 exit-criterion artifact is materialized. Lower-layer
unit tests (under `tests/livespec/...`) are pulled into existence
when this rail's failure is too coarse to drive design at a
specific layer.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly
as Claude Code invokes it; runtime version-check, `sys.path`
setup, and structlog configuration all run for real here.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "seed.py"


def _extract_front_matter(*, content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", content, flags=re.DOTALL)
    assert match is not None, f"missing YAML front-matter delimited by `---`; content={content!r}"
    return match.group(1)


def _extract_field(*, front_matter: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}: (.+)$", front_matter, flags=re.MULTILINE)
    assert match is not None, f"front-matter missing `{key}:`; front_matter={front_matter!r}"
    return match.group(1).strip()


def test_seed_writes_livespec_jsonc_at_repo_root(*, tmp_path: Path) -> None:
    """`seed.py --seed-json <payload>` writes `.livespec.jsonc` at the project root.

    Minimal valid payload (template `livespec`, empty `files`,
    empty `sub_specs`, single-line `intent`) is the smallest
    valid input the wrapper can accept. The exit-criterion
    artifact this cycle pins is the wrapper-owned
    `.livespec.jsonc` (per PROPOSAL.md §"`seed`" lines 1894-1924
    — `.livespec.jsonc` is wrapper-owned; the absent branch
    writes the full commented schema skeleton with the payload's
    `template` value).
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [],
        "intent": "test seed for Phase 3 exit-criterion round-trip",
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert (tmp_path / ".livespec.jsonc").exists(), (
        f".livespec.jsonc not written under {tmp_path}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_seed_writes_each_main_spec_file_to_its_payload_path(*, tmp_path: Path) -> None:
    """`seed.py` materializes every `files[]` entry to its declared path with declared content.

    Per PROPOSAL.md §"`seed`" lines 1992-2042 (the deterministic
    seed file-shaping work order, step 2: "Write each main-spec
    `files[]` entry to its specified path"), a non-empty
    `files[]` array drives the supervisor to write each entry's
    `content` to its `path` (relative to the project root /
    cwd). Parent directories are created on demand — the payload
    can declare paths nested under arbitrary subdirectories
    (e.g., `SPECIFICATION/spec.md`) without the wrapper
    pre-creating them.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec content"},
            {"path": "SPECIFICATION/contracts.md", "content": "stub contracts"},
        ],
        "intent": "test seed materializes main-spec files[] entries",
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    spec_path = tmp_path / "SPECIFICATION" / "spec.md"
    contracts_path = tmp_path / "SPECIFICATION" / "contracts.md"
    assert spec_path.exists(), (
        f"main-spec file {spec_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert contracts_path.exists(), (
        f"main-spec file {contracts_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert spec_path.read_text(encoding="utf-8") == "stub spec content"
    assert contracts_path.read_text(encoding="utf-8") == "stub contracts"


def test_seed_writes_history_v001_for_main_spec(*, tmp_path: Path) -> None:
    """`seed.py` materializes `<spec-root>/history/v001/` for the main spec.

    Per PROPOSAL.md §"`seed`" lines 1992-2042 step 4: "Create
    `<spec-root>/history/v001/` for the main spec (including the
    initial versioned spec files, a `proposed_changes/` subdir,
    and, for templates whose versioned surface includes one, a
    per-version README copy)." Per PROPOSAL.md lines 981-986,
    "Historic files under `history/vNNN/` use plain filenames
    (no `vNNN-` prefix)" and the parallel structure mirrors the
    active spec_root tree shape. For the `livespec` template,
    `spec_root` is `SPECIFICATION/` (per
    `template_config.schema.json` default, confirmed by
    `.claude-plugin/specification-templates/livespec/template.json`).

    This test pins the v001-snapshot of the spec file plus the
    empty `proposed_changes/` subdir. The auto-captured seed
    proposed-change (PROPOSAL.md lines 2043-2064) and the
    per-version README snapshot (lines 1071-1074) are deferred
    to later cycles.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": "test seed materializes history/v001/ for main spec",
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    history_v001 = tmp_path / "SPECIFICATION" / "history" / "v001"
    history_spec = history_v001 / "spec.md"
    history_proposed_changes = history_v001 / "proposed_changes"
    assert history_spec.exists(), (
        f"v001 snapshot {history_spec} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert history_spec.read_text(encoding="utf-8") == "stub spec"
    assert history_proposed_changes.is_dir(), (
        f"v001 proposed_changes/ {history_proposed_changes} not a directory; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_seed_writes_sub_spec_files_to_payload_paths(*, tmp_path: Path) -> None:
    """`seed.py` materializes every `sub_specs[].files[]` entry to its declared path.

    Per PROPOSAL.md §"`seed`" lines 1992-2042 step 3: "**(v018
    Q1)** For each entry in `sub_specs[]`, write every `files[]`
    entry in that sub-spec to its
    `SPECIFICATION/templates/<template_name>/<spec-file>` path.
    The sub-spec trees are written alongside the main tree,
    atomically with it." Per
    `seed_input.schema.json#/properties/sub_specs/items/properties/files/items/properties/path`,
    each sub-spec file's `path` is a project-root-relative path,
    conventionally `SPECIFICATION/templates/<template_name>/<spec-file>`.

    This test pins ONLY the sub-spec working-tree files. The
    sub-spec `history/v001/` snapshot (PROPOSAL.md lines
    2014-2028 step 5) is deferred to a later cycle.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [],
        "intent": "test seed materializes sub_specs[].files[] entries",
        "sub_specs": [
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "stub livespec sub-spec",
                    },
                    {
                        "path": "SPECIFICATION/templates/livespec/contracts.md",
                        "content": "stub contracts",
                    },
                ],
            },
        ],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    sub_spec_root = tmp_path / "SPECIFICATION" / "templates" / "livespec"
    sub_spec_path = sub_spec_root / "spec.md"
    sub_contracts_path = sub_spec_root / "contracts.md"
    assert sub_spec_path.exists(), (
        f"sub-spec file {sub_spec_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert sub_contracts_path.exists(), (
        f"sub-spec file {sub_contracts_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert sub_spec_path.read_text(encoding="utf-8") == "stub livespec sub-spec"
    assert sub_contracts_path.read_text(encoding="utf-8") == "stub contracts"


def test_seed_writes_history_v001_for_each_sub_spec(*, tmp_path: Path) -> None:
    """`seed.py` materializes `<sub-spec-root>/history/v001/` for each sub-spec.

    Per PROPOSAL.md §"`seed`" lines 2014-2028 step 5: "**(v018
    Q1; v020 Q1 uniform README)** For each sub-spec tree, create
    `SPECIFICATION/templates/<template_name>/history/v001/`
    alongside the main-spec history — including the sub-spec's
    own versioned spec files and `proposed_changes/` subdir."
    Per PROPOSAL.md lines 981-986, "Historic files under
    `history/vNNN/` use plain filenames (no `vNNN-` prefix)" and
    the parallel structure mirrors the active sub-spec-root tree
    shape. The sub-spec-root for each `sub_specs[]` entry is
    `SPECIFICATION/templates/<template_name>/`.

    This test pins the v001-snapshot of the sub-spec working-tree
    files plus the empty `proposed_changes/` subdir. The
    sub-spec-root README.md and the per-version README snapshot
    (PROPOSAL.md lines 2019-2020) are deferred until a content
    assertion (or a payload carrying a README entry) forces them
    — the skill-owned `proposed_changes/README.md` and
    `history/README.md` paragraphs (lines 2025-2028) are also
    deferred until that cycle.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [],
        "intent": "test seed materializes history/v001/ for each sub-spec",
        "sub_specs": [
            {
                "template_name": "livespec",
                "files": [
                    {
                        "path": "SPECIFICATION/templates/livespec/spec.md",
                        "content": "stub livespec sub-spec",
                    },
                    {
                        "path": "SPECIFICATION/templates/livespec/contracts.md",
                        "content": "stub contracts",
                    },
                ],
            },
        ],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    sub_spec_root = tmp_path / "SPECIFICATION" / "templates" / "livespec"
    history_v001 = sub_spec_root / "history" / "v001"
    history_spec = history_v001 / "spec.md"
    history_contracts = history_v001 / "contracts.md"
    history_proposed_changes = history_v001 / "proposed_changes"
    assert history_spec.exists(), (
        f"sub-spec v001 snapshot {history_spec} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert history_contracts.exists(), (
        f"sub-spec v001 snapshot {history_contracts} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert history_spec.read_text(encoding="utf-8") == "stub livespec sub-spec"
    assert history_contracts.read_text(encoding="utf-8") == "stub contracts"
    assert history_proposed_changes.is_dir(), (
        f"sub-spec v001 proposed_changes/ {history_proposed_changes} not a directory; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_seed_writes_auto_captured_seed_proposal_for_main_spec(*, tmp_path: Path) -> None:
    """`seed.py` auto-captures `<spec-root>/history/v001/proposed_changes/seed.md`.

    Per PROPOSAL.md §"`seed`" lines 2043-2057 (the auto-generated
    `seed.md` content) and §"Proposed-change file format" (lines
    2939-3033, the canonical format every proposed-change file
    conforms to). The wrapper writes a proposed-change file with
    YAML front-matter (`topic: seed`, `author: livespec-seed`,
    `created_at: <UTC ISO-8601 seconds>`) followed by one
    `## Proposal: seed` section with `### Target specification
    files`, `### Summary` (verbatim "Initial seed of the
    specification from user-provided intent."), `### Motivation`
    (verbatim payload `intent`), and `### Proposed Changes`
    (verbatim payload `intent` again).

    Sub-specs do NOT receive their own auto-captured seed.md per
    PROPOSAL.md lines 2031-2035 ("the single main-spec seed
    artifact documents the whole multi-tree creation"). The
    paired `seed-revision.md` is deferred to the next TDD cycle.
    """
    intent_text = "capture this verbatim as motivation"
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": intent_text,
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    seed_proposal = tmp_path / "SPECIFICATION" / "history" / "v001" / "proposed_changes" / "seed.md"
    assert seed_proposal.exists(), (
        f"auto-captured seed.md {seed_proposal} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    content = seed_proposal.read_text(encoding="utf-8")

    # Front-matter delimiters and required keys.
    front_matter_match = re.match(r"^---\n(.*?)\n---\n", content, flags=re.DOTALL)
    assert (
        front_matter_match is not None
    ), f"seed.md missing YAML front-matter delimited by `---`; content={content!r}"
    front_matter = front_matter_match.group(1)
    assert (
        "topic: seed" in front_matter
    ), f"seed.md front-matter missing `topic: seed`; front_matter={front_matter!r}"
    assert (
        "author: livespec-seed" in front_matter
    ), f"seed.md front-matter missing `author: livespec-seed`; front_matter={front_matter!r}"
    created_at_match = re.search(r"^created_at: (\S+)$", front_matter, flags=re.MULTILINE)
    assert (
        created_at_match is not None
    ), f"seed.md front-matter missing `created_at:`; front_matter={front_matter!r}"
    # ISO-8601 seconds in UTC: parses cleanly with UTC timezone.
    parsed_ts = datetime.fromisoformat(created_at_match.group(1).replace("Z", "+00:00"))
    assert parsed_ts.utcoffset() == timezone.utc.utcoffset(
        parsed_ts
    ), f"seed.md created_at not UTC-anchored; created_at={created_at_match.group(1)!r}"

    # Body sections in order: ## Proposal: seed → its sub-headings.
    assert (
        "## Proposal: seed" in content
    ), f"seed.md missing `## Proposal: seed` heading; content={content!r}"
    assert (
        "### Target specification files" in content
    ), f"seed.md missing `### Target specification files` heading; content={content!r}"
    assert (
        "SPECIFICATION/spec.md" in content
    ), f"seed.md does not list SPECIFICATION/spec.md as target; content={content!r}"
    assert "### Summary" in content, f"seed.md missing `### Summary` heading; content={content!r}"
    assert (
        "Initial seed of the specification from user-provided intent." in content
    ), f"seed.md missing canonical Summary text; content={content!r}"
    assert (
        "### Motivation" in content
    ), f"seed.md missing `### Motivation` heading; content={content!r}"
    assert (
        "### Proposed Changes" in content
    ), f"seed.md missing `### Proposed Changes` heading; content={content!r}"
    # Verbatim intent appears under both Motivation and Proposed Changes
    # (one occurrence each — two total).
    expected_intent_occurrences = 2
    assert content.count(intent_text) >= expected_intent_occurrences, (
        f"seed.md does not include verbatim intent under both Motivation and "
        f"Proposed Changes (expected >={expected_intent_occurrences} occurrences "
        f"of {intent_text!r}); content={content!r}"
    )


def test_seed_writes_auto_captured_seed_revision_for_main_spec(*, tmp_path: Path) -> None:
    """`seed.py` auto-captures `<spec-root>/history/v001/proposed_changes/seed-revision.md`.

    Per PROPOSAL.md §"`seed`" lines 2058-2064 (the auto-generated
    revision pairing) and §"Revision file format" (lines
    3037-3097, the canonical format every revision file conforms
    to). The wrapper writes a revision file with YAML
    front-matter (`proposal: seed.md`, `decision: accept`,
    `revised_at: <UTC ISO-8601 seconds>` matching the paired
    seed.md `created_at`, `author_llm: livespec-seed`,
    `author_human: <git user info or "unknown">`) followed by
    `## Decision and Rationale` ("auto-accepted during seed") and
    `## Resulting Changes` (every seed-written file path).
    """
    intent_text = "capture this verbatim as motivation"
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": intent_text,
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"seed wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    proposed_changes_dir = tmp_path / "SPECIFICATION" / "history" / "v001" / "proposed_changes"
    seed_revision = proposed_changes_dir / "seed-revision.md"
    assert seed_revision.exists(), (
        f"auto-captured seed-revision.md {seed_revision} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    content = seed_revision.read_text(encoding="utf-8")

    # Front-matter delimiters and required keys.
    front_matter = _extract_front_matter(content=content)
    assert (
        "proposal: seed.md" in front_matter
    ), f"seed-revision.md missing `proposal: seed.md`; front_matter={front_matter!r}"
    assert (
        "decision: accept" in front_matter
    ), f"seed-revision.md missing `decision: accept`; front_matter={front_matter!r}"
    assert (
        "author_llm: livespec-seed" in front_matter
    ), f"seed-revision.md missing `author_llm: livespec-seed`; front_matter={front_matter!r}"
    # author_human is either "<name> <email>" (git config populated) or the literal "unknown".
    # Both are acceptable per PROPOSAL.md §"Git" lines 700-704.
    author_human_value = _extract_field(front_matter=front_matter, key="author_human")
    assert (
        author_human_value != ""
    ), f"seed-revision.md `author_human:` is empty; front_matter={front_matter!r}"
    revised_at_value = _extract_field(front_matter=front_matter, key="revised_at")
    parsed_revised_at = datetime.fromisoformat(revised_at_value.replace("Z", "+00:00"))
    assert parsed_revised_at.utcoffset() == timezone.utc.utcoffset(
        parsed_revised_at
    ), f"seed-revision.md revised_at not UTC-anchored; revised_at={revised_at_value!r}"

    # revised_at MUST match the paired seed.md created_at exactly.
    seed_content = (proposed_changes_dir / "seed.md").read_text(encoding="utf-8")
    seed_front_matter = _extract_front_matter(content=seed_content)
    created_at_value = _extract_field(front_matter=seed_front_matter, key="created_at")
    assert created_at_value == revised_at_value, (
        f"seed-revision.md revised_at ({revised_at_value!r}) does not match "
        f"seed.md created_at ({created_at_value!r})"
    )

    # Body sections.
    assert (
        "## Decision and Rationale" in content
    ), f"seed-revision.md missing `## Decision and Rationale` heading; content={content!r}"
    assert (
        "auto-accepted during seed" in content
    ), f"seed-revision.md missing 'auto-accepted during seed' text; content={content!r}"
    assert (
        "## Resulting Changes" in content
    ), f"seed-revision.md missing `## Resulting Changes` heading; content={content!r}"
    assert "SPECIFICATION/spec.md" in content, (
        f"seed-revision.md does not list SPECIFICATION/spec.md as a resulting change; "
        f"content={content!r}"
    )


def test_seed_refuses_when_any_target_file_already_exists(*, tmp_path: Path) -> None:
    """Re-running `seed.py` against an already-seeded tree refuses with exit 3.

    Per PROPOSAL.md §"`seed`" lines 2065-2071: "if any
    template-declared target file already exists at its target
    path, `seed` MUST refuse and list the existing files."
    Per PROPOSAL.md §"Sub-command lifecycle orchestration" line
    2128: "Seed's idempotency refusal stays strict; there is no
    `--force-reseed` flag." Per PROPOSAL.md lines 2839-2843, a
    `PreconditionError` (which idempotency-refusal is) maps to
    exit code 3.

    The check happens BEFORE any writes (PROPOSAL.md lines
    1919-1924: "preserves the non-doctor fail-fast rule ... never
    silently overwrites a user's manual edit"). This test pins
    the second seed invocation as exit-3-with-listed-paths; it
    does NOT pin "the second seed leaves the tree byte-identical
    to after the first" because that's a stronger no-partial-write
    guarantee covered separately.

    Template-declared target files per PROPOSAL.md line 1902 are
    the `payload["files"][].path` (and
    `payload["sub_specs"][].files[].path`) entries;
    `.livespec.jsonc` is wrapper-owned, NOT template-declared,
    and goes through its own three-branch logic (PROPOSAL.md
    lines 1894-1924). This test relies on at least one
    template-declared target (`SPECIFICATION/spec.md`) existing
    post-first-seed to trigger idempotency-refusal.
    """
    payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": "test seed idempotency refusal",
        "sub_specs": [],
    }
    payload_path = tmp_path / "seed_input.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    # First seed: succeeds.
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    first = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        first.returncode == 0
    ), f"first seed unexpectedly failed; stdout={first.stdout!r} stderr={first.stderr!r}"
    assert (tmp_path / ".livespec.jsonc").exists()
    assert (tmp_path / "SPECIFICATION" / "spec.md").exists()

    # Second seed: must refuse with exit 3 and surface the existing path.
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    second = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(payload_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    expected_precondition_exit_code = 3
    assert second.returncode == expected_precondition_exit_code, (
        f"second seed should refuse with exit {expected_precondition_exit_code}; "
        f"got returncode={second.returncode} "
        f"stdout={second.stdout!r} stderr={second.stderr!r}"
    )
    # Stderr surfaces at least one of the existing template-declared targets
    # so the user can locate the offending files.
    assert (
        "SPECIFICATION/spec.md" in second.stderr
    ), f"second seed stderr does not list SPECIFICATION/spec.md; stderr={second.stderr!r}"
