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
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "seed.py"


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
