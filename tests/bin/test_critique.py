"""Outside-in integration test for `bin/critique.py` — Phase 3 exit-criterion rail.

Per PROPOSAL.md §"`critique`" lines 2280-2333 + Plan §"Phase 3"
lines 1408-1416, invoking `critique.py --findings-json <path>
[--author <id>] [--spec-target <path>]` against a tmp_path that
already carries a seeded spec tree internally delegates to
`propose_change`'s Python logic with the topic hint set to the
resolved author stem and the reserve-suffix parameter set to
`"-critique"` (v016 P3). The resulting canonicalized topic is
used for the proposed-change filename — e.g., resolved author
"test author" composes to topic `"test-author-critique"`,
filename `<spec-target>/proposed_changes/test-author-critique.md`.

This module holds the OUTERMOST integration test for the
critique exit-criterion round-trip. Per the v032 D2 outside-in
walking direction, the failure point of this single test
advances forward across many TDD cycles: first the wrapper file
does not exist (FileNotFoundError); next, the supervisor stub
exists but writes nothing (the `<topic>-critique.md` missing
assertion); then internal delegation produces a real file but
content / canonical-topic / front-matter pieces fail in turn.

The wrapper is invoked as a subprocess so the wrapper-shape +
bootstrap + supervisor plumbing is exercised end-to-end exactly
as Claude Code invokes it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "seed.py"
_CRITIQUE_WRAPPER = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin" / "critique.py"


def _seed_tmp_path(*, tmp_path: Path) -> None:
    """Pre-seed tmp_path with the minimum spec tree critique needs."""
    seed_payload: dict[str, object] = {
        "template": "livespec",
        "files": [
            {"path": "SPECIFICATION/spec.md", "content": "stub spec"},
        ],
        "intent": "pre-seed for critique integration test",
        "sub_specs": [],
    }
    seed_input = tmp_path / "seed_input.json"
    seed_input.write_text(json.dumps(seed_payload), encoding="utf-8")
    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload); no untrusted shell input.
    seed_result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SEED_WRAPPER), "--seed-json", str(seed_input)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        seed_result.returncode == 0
    ), f"pre-seed failed; stdout={seed_result.stdout!r} stderr={seed_result.stderr!r}"


def test_critique_writes_topic_critique_md_at_spec_target(*, tmp_path: Path) -> None:
    """critique.py with `--findings-json` + `--author` writes a `<slugged-author>-critique.md`.

    Per PROPOSAL.md §"`critique`" lines 2307-2325, `bin/critique.py`
    delegates internally to `propose_change`'s Python logic with
    topic hint `<resolved-author>` (author stem only) and the
    reserve-suffix parameter `"-critique"`. `propose_change` then
    canonicalizes the composite via its reserve-suffix
    canonicalization: the resolved-author stem is slugged
    (lowercase + non-alphanumeric → hyphen + truncate at 64-char
    cap with the `-critique` suffix preserved); the canonicalized
    composite drives filename, front-matter `topic`, and collision
    handling. Informally per the spec example: author
    `"Claude Opus 4.7"` → topic `"claude-opus-4-7-critique"`.

    For Phase-3-minimum determinism, this test passes
    `--author "test author"` so the slugged stem is `"test-author"`
    and the canonical critique topic is `"test-author-critique"`,
    yielding
    `<spec-target>/proposed_changes/test-author-critique.md`.

    Plan lines 1408-1416 confirm minimum-viable scope: invoke
    `propose_change.py` internally with the `-critique`
    reserve-suffix appended (the simplest delegation shape; full
    reserve-suffix algorithm lives in Phase 7). Accepts
    `--spec-target <path>` and routes the delegation with the
    same target.
    """
    _seed_tmp_path(tmp_path=tmp_path)
    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": "Critique-test proposal",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Stub critique-test summary.",
                "motivation": "Stub motivation paragraph for critique flow.",
                "proposed_changes": "Stub prose describing critique-derived changes.",
            },
        ],
    }
    findings_input = tmp_path / "findings.json"
    findings_input.write_text(json.dumps(findings_payload), encoding="utf-8")

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # wrapper path + tmp_path payload + literal author); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(_CRITIQUE_WRAPPER),
            "--findings-json",
            str(findings_input),
            "--author",
            "test author",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"critique wrapper exited {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    expected_topic = "test-author-critique"
    expected_path = tmp_path / "SPECIFICATION" / "proposed_changes" / f"{expected_topic}.md"
    assert expected_path.exists(), (
        f"critique-derived proposed-change file {expected_path} not written; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
