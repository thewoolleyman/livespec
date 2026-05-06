"""Tests for livespec.commands.prune_history.

Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle" prune-history
paragraph: the wrapper resolves the spec root from `--project-root`,
enumerates `<spec-root>/history/`, and short-circuits with a
`prune-history-no-op` skipped JSON finding when the no-op
preconditions are met.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.commands import prune_history
from returns.io import IOResult

__all__: list[str] = []


@pytest.fixture(autouse=True)
def _stub_pre_step_doctor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default-stub `_invoke_pre_step_doctor` to a no-op pass for every test.

    Cycle 6.c.10 wires the pre-step doctor static invocation per
    v012 SPECIFICATION/spec.md §"Sub-command lifecycle". When the
    resolved skip value is False, the wrapper invokes
    `bin/doctor_static.py` as a subprocess via
    `livespec.io.proc.run_subprocess`. Pre-existing tests in this
    file did NOT design fixtures that the real doctor would
    consider valid (most use `_make_v001_only_spec_root` which
    lacks `spec.md`, `.livespec.jsonc`, etc.) — the real doctor
    would emit fail findings and short-circuit the wrapper before
    the body runs, breaking every existing assertion.

    This autouse fixture monkeypatches the helper to a passing
    no-op so existing tests (which test orthogonal concerns:
    flag parsing, no-op short-circuits, marker writes, skip-
    resolution) continue to exercise the body without the doctor
    interfering. Tests that specifically cover the pre-step doctor
    wiring opt out by re-monkeypatching with their own stub.

    `raising=False` is required so the fixture is lenient when
    the helper does not yet exist (Red commit at cycle 6.c.10
    adds the test surface BEFORE the impl lands the helper; the
    first-stage Red tests reference `_invoke_pre_step_doctor`
    via direct attribute access and FAIL with AttributeError —
    that's the intentional Red signal).
    """

    def _passing_no_op(*, project_root: Path) -> IOResult[None, object]:
        del project_root
        return IOResult.from_value(None)

    monkeypatch.setattr(
        prune_history,
        "_invoke_pre_step_doctor",
        _passing_no_op,
        raising=False,
    )


def _make_v001_only_spec_root(*, tmp_path: Path) -> Path:
    """Set up `<tmp_path>/SPECIFICATION/history/v001/` and return tmp_path."""
    (tmp_path / "SPECIFICATION" / "history" / "v001").mkdir(parents=True)
    return tmp_path


def test_prune_history_main_exists_and_returns_int(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/prune_history.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Uses `monkeypatch.chdir(tmp_path)` to
    isolate the cwd-fallback `_resolve_spec_root` branch from the
    real repo's `SPECIFICATION/`; without isolation this test would
    leak into the developer's working tree.
    """
    _ = _make_v001_only_spec_root(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = prune_history.main(argv=[])
    assert isinstance(exit_code, int)


def test_prune_history_main_returns_zero_on_valid_argv(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """prune-history with no flags + only v001 in history returns exit code 0.

    Per v012 spec.md no-op short-circuit (i): only-v001 case
    emits the skipped finding and exits 0. Drives the cwd-fallback
    `_resolve_spec_root` branch + the no-op path.
    """
    _ = _make_v001_only_spec_root(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = prune_history.main(argv=[])
    assert exit_code == 0


def test_prune_history_main_returns_usage_exit_code_on_unknown_flag() -> None:
    """Unknown CLI flag returns exit code 2.

    Drives the parse_argv stage on the railway: an unknown flag
    surfaces as an argparse SystemExit, which io/cli's
    @impure_safe maps to UsageError and the supervisor's
    pattern-match lifts to exit 2 via err.exit_code. The
    UsageError fires before the body runs, so no spec-root
    setup is needed.
    """
    exit_code = prune_history.main(argv=["--no-such-flag"])
    assert exit_code == 2


def test_prune_history_main_accepts_skip_pre_check_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--skip-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--skip-pre-check` as one half of the mutually-exclusive
    flag pair codified in v012 spec.md §"Pre-step skip control".
    The body widening at cycle 6.c.3 means the wrapper now requires
    a valid `<spec-root>/history/` to short-circuit on; this test
    sets up a v001-only history and drives the no-op path.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--skip-pre-check", "--project-root", str(project_root)],
    )
    assert exit_code == 0


def test_prune_history_main_accepts_run_pre_check_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--run-pre-check` is a recognized optional flag (exit 0).

    Per v012 §"Wrapper CLI surface" prune-history row: the wrapper
    accepts `--run-pre-check` as the override-config half of the
    mutually-exclusive flag pair codified in v012 spec.md
    §"Pre-step skip control".
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    assert exit_code == 0


def test_prune_history_main_rejects_both_skip_and_run_pre_check_flags_together() -> None:
    """Passing both `--skip-pre-check` AND `--run-pre-check` exits 2.

    Per v012 spec.md §"Pre-step skip control" rule (4): both flags
    set together MUST result in argparse mutually-exclusive usage
    error, lifting to exit 2 via `IOFailure(UsageError)`. Drives
    the `add_mutually_exclusive_group` enforcement. The
    UsageError fires before the body runs, so no spec-root setup
    is needed.
    """
    exit_code = prune_history.main(argv=["--skip-pre-check", "--run-pre-check"])
    assert exit_code == 2


def test_prune_history_main_emits_no_op_finding_when_only_v001_exists(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md no-op short-circuit (i): only v001 exists.

    When `<spec-root>/history/` contains only `v001`, the wrapper
    emits a single-finding `{"findings": [{"check_id": "prune-
    history-no-op", "status": "skipped", "message": "..."}]}` JSON
    document to stdout and exits 0; the existing tree is NOT
    re-written, no commit-worthy diff is produced. Drives spec-
    root resolution from `--project-root`, history enumeration,
    max-version detection, and the JSON finding emission.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert payload["findings"][0]["status"] == "skipped"


def test_prune_history_main_accepts_project_root_flag(
    *,
    tmp_path: Path,
) -> None:
    """`--project-root <path>` is a recognized optional flag (exit 0).

    Per SPECIFICATION/contracts.md §"Wrapper CLI surface"
    prune-history row + the universal `--project-root <path>`
    baseline.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    assert exit_code == 0


def test_prune_history_main_does_not_short_circuit_on_only_v001_guard_when_max_version_is_two(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The `if max_version == 1:` guard's "not-taken" branch fires when max_version == 2.

    Drives the `if max_version == 1:` guard's "guard not taken"
    branch in `_maybe_no_op_or_resolve`. The fixture sets up v001
    and v002, so max_version = 2; the (i) short-circuit does NOT
    fire. The (ii) short-circuit ALSO does not fire (v001 has no
    `PRUNED_HISTORY.json`), so the wrapper proceeds into
    carry-forward `first` resolution per spec.md step (b) and the
    full 5-step mechanic. With N=2: step (c) deletes nothing (no
    K<N-1=1); step (d) replaces v(N-1)=v001 contents with
    `PRUNED_HISTORY.json` carrying `{"pruned_range": [1, 1]}`;
    step (e) leaves v002 (vN) intact. The supervisor emits the
    `prune-history-pruned` `pass` finding.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v002").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    marker_path = spec_root / "history" / "v001" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [1, 1]}
    assert (spec_root / "history" / "v002").is_dir()


def test_prune_history_find_max_version_skips_non_directory_entries(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips non-directory children defensively.

    Drives the `if not child.is_dir(): continue` guard branch.
    The fixture mixes a regular file (skipped) with a v001 dir
    (counted). Mirrors the
    `test_revise_format_next_version_name_skips_non_directory_entries`
    precedent.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001


def test_prune_history_find_max_version_skips_non_v_prefix_dirs(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips directory children whose name doesn't start with `v`.

    Drives the `if not name.startswith("v"): continue` guard
    branch. The fixture mixes a non-v-prefixed dir with a v001
    dir (counted). Mirrors the analogous revise-side test.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "scratch").mkdir()
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001


def test_prune_history_find_max_version_skips_v_prefix_with_non_digit_suffix(
    *,
    tmp_path: Path,
) -> None:
    """`_find_max_version` skips `v<non-digits>` directory children.

    Drives the `if not suffix.isdigit(): continue` guard branch.
    The fixture mixes a `vextra` dir (skipped) with a v001 dir
    (counted). Mirrors the analogous revise-side test.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "vextra").mkdir()
    children = sorted(history.iterdir())
    assert prune_history._find_max_version(children=children) == 1  # noqa: SLF001


def test_prune_history_main_emits_no_op_finding_when_oldest_surviving_is_pruned_history_marker(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md no-op short-circuit (ii): oldest surviving has PRUNED_HISTORY.json.

    When `<spec-root>/history/` has multiple v* dirs and the
    smallest-K (oldest surviving) v-dir already contains a
    `PRUNED_HISTORY.json` marker, no full versions remain to
    prune below the prior marker. The wrapper emits the same
    single-finding `prune-history-no-op` skipped JSON document
    to stdout and exits 0 without re-writing anything. Drives
    the new (ii) detection branch in `_maybe_no_op` plus the
    `_oldest_below_has_pruned_marker` helper.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v001" / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [1, 1]}',
        encoding="utf-8",
    )
    (spec_root / "history" / "v002").mkdir()
    (spec_root / "history" / "v003").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert payload["findings"][0]["status"] == "skipped"


def test_prune_history_oldest_below_has_pruned_marker_returns_true_when_marker_present(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` returns True when smallest-K v-dir has marker.

    Drives the `return (child / "PRUNED_HISTORY.json").is_file()`
    True-side branch. The fixture sets up v001/PRUNED_HISTORY.json
    + v002 and asks for max_version=2; v001 is the oldest below
    max and it carries the marker.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "v001" / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=2,
        )
        is True
    )


def test_prune_history_oldest_below_has_pruned_marker_returns_false_when_marker_absent(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` returns False when smallest-K v-dir lacks marker.

    Drives the `return ... .is_file()` False-side branch. The
    fixture sets up v001 + v002 (no PRUNED_HISTORY.json anywhere)
    and asks for max_version=2; v001 is oldest below max but has
    no marker.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=2,
        )
        is False
    )


def test_prune_history_oldest_below_has_pruned_marker_skips_non_directory_entries(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` skips non-directory children defensively.

    Drives the `if not child.is_dir(): continue` guard branch.
    The fixture mixes a regular file (skipped) with a v001 dir
    that carries the marker; the helper must walk past the file
    and find v001.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "README.txt").write_text("not a v-dir", encoding="utf-8")
    (history / "v001").mkdir()
    (history / "v001" / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=2,
        )
        is True
    )


def test_prune_history_oldest_below_has_pruned_marker_skips_non_v_prefix_dirs(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` skips dir children whose name lacks `v` prefix.

    Drives the `if not name.startswith("v"): continue` guard
    branch. Sorted iteration encounters `aaa` first (skipped),
    then v001 (has marker).
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "aaa").mkdir()
    (history / "v001").mkdir()
    (history / "v001" / "PRUNED_HISTORY.json").write_text("{}", encoding="utf-8")
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=2,
        )
        is True
    )


def test_prune_history_oldest_below_has_pruned_marker_skips_v_prefix_with_non_digit_suffix(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` skips `v<non-digits>` dir children.

    Drives the `if not suffix.isdigit(): continue` guard True-side
    branch. The fixture has only a `vextra` dir (no eligible v-
    digit children at all); the helper iterates, hits the
    isdigit-False filter, continues, exits the loop, and returns
    False via the post-loop fallthrough.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "vextra").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=3,
        )
        is False
    )


def test_prune_history_oldest_below_has_pruned_marker_skips_versions_at_or_above_max(
    *,
    tmp_path: Path,
) -> None:
    """`_oldest_below_has_pruned_marker` returns False when no v<max-version dirs exist.

    Drives the `if version >= max_version: continue` guard True-
    side AND the post-loop `return False` branch. The fixture
    has only v002 and asks for max_version=2; v002 is filtered
    out (version >= max_version), no candidates remain, return
    False.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    assert (
        prune_history._oldest_below_has_pruned_marker(  # noqa: SLF001
            children=children,
            max_version=2,
        )
        is False
    )


def test_prune_history_resolve_first_returns_pruned_range_zero_when_marker_text_provided(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` returns `pruned_range[0]` when prior-marker text is supplied.

    Per v012 spec.md §"Sub-command lifecycle" prune-history
    paragraph step (b): if `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json`
    exists, the wrapper reads its `pruned_range[0]` and uses it as
    the carry-forward `first` field. Drives the marker-present
    branch of the pure resolver: text overrides any children
    enumeration. Children list is irrelevant to the marker-
    present branch.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v007").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=7,
        prior_marker_text='{"pruned_range": [5, 7]}',
    )
    assert first == 5


def test_prune_history_resolve_first_returns_smallest_v_dir_when_marker_text_absent(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` returns smallest-numbered v-dir when no marker text supplied.

    Per v012 spec.md prune-history paragraph step (b): when no
    prior `PRUNED_HISTORY.json` marker exists at v(N-1), `first`
    is the smallest-numbered v-directory currently under
    `<spec-root>/history/`. Drives the marker-absent branch of
    the pure resolver. Fixture has v002/v003/v004/v005, so the
    smallest-numbered v-dir is 2 (NOT 1; nothing was ever
    seeded at v001 in this synthetic fixture, exercising that
    `first` is NOT hard-coded to 1).
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    (history / "v004").mkdir()
    (history / "v005").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=5,
        prior_marker_text=None,
    )
    assert first == 2


def test_prune_history_resolve_first_returns_one_when_only_v001_exists(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` returns 1 when `<spec-root>/history/` has only v001.

    Edge case of the marker-absent branch per spec.md prune-
    history paragraph step (b): the smallest-numbered v-dir is
    v001 → `first` = 1. The (i) no-op short-circuit normally
    prevents the resolver from being called when only v001
    exists, but the pure helper is called via direct unit test
    to cover the degenerate-but-valid input.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=1,
        prior_marker_text=None,
    )
    assert first == 1


def test_prune_history_resolve_first_skips_non_directory_entries_when_marker_absent(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` skips non-directory children defensively in the marker-absent branch.

    Drives the `if not child.is_dir(): continue` guard branch of
    the pure resolver. Mirrors the analogous defensive guard in
    `_find_max_version` and `_oldest_below_has_pruned_marker`.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "README.txt").write_text("not a v-dir", encoding="utf-8")
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=3,
        prior_marker_text=None,
    )
    assert first == 3


def test_prune_history_resolve_first_skips_non_v_prefix_dirs_when_marker_absent(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` skips dir children whose name doesn't start with `v` (marker-absent branch).

    Drives the `if not name.startswith("v"): continue` guard
    branch of the pure resolver. Sorted iteration yields `aaa`
    first (skipped), then v003 (smallest remaining v-dir).
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "aaa").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=3,
        prior_marker_text=None,
    )
    assert first == 3


def test_prune_history_resolve_first_skips_v_prefix_with_non_digit_suffix_when_marker_absent(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_first` skips `v<non-digits>` dir children (marker-absent branch).

    Drives the `if not suffix.isdigit(): continue` guard branch
    of the pure resolver. Sorted iteration yields `vextra`
    (skipped), then v003 (counted).
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "vextra").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    first = prune_history._resolve_first(  # noqa: SLF001
        children=children,
        max_version=3,
        prior_marker_text=None,
    )
    assert first == 3


def test_prune_history_main_resolves_first_via_marker_at_n_minus_1(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When v(N-1) has PRUNED_HISTORY.json and (ii) no-op does NOT fire, marker is read.

    Per v012 spec.md prune-history paragraph step (b): the
    wrapper resolves the carry-forward `first` field from
    `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json`'s
    `pruned_range[0]`. Fixture is constructed so the (ii) no-op
    short-circuit does NOT fire (v002 — the OLDEST surviving v-
    dir below max=5 — has NO marker), but v(N-1)=v004 DOES
    carry a marker `{"pruned_range": [3, 4]}` (so first=3). The
    resolver path runs end-to-end through the impure
    `fs.read_text` boundary, exercising the integration seam
    between `_run_prune` and `_resolve_first`. With N=5, step (c)
    deletes v002 + v003 (K<4); step (d) replaces v004's contents
    with a fresh `PRUNED_HISTORY.json` carrying
    `{"pruned_range": [3, 4]}` (the marker is rewritten with
    first carried forward and last advanced to N-1=4 — same
    payload here since first was already 3 and last was already
    4); step (e) leaves v005 intact. The supervisor emits the
    `prune-history-pruned` `pass` finding.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v002").mkdir(parents=True)
    (spec_root / "history" / "v003").mkdir()
    (spec_root / "history" / "v004").mkdir()
    (spec_root / "history" / "v004" / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [3, 4]}',
        encoding="utf-8",
    )
    (spec_root / "history" / "v005").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    assert not (spec_root / "history" / "v002").exists()
    assert not (spec_root / "history" / "v003").exists()
    marker_path = spec_root / "history" / "v004" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [3, 4]}
    assert (spec_root / "history" / "v005").is_dir()


def test_prune_history_main_resolves_first_via_smallest_v_dir_when_marker_absent_at_n_minus_1(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When v(N-1) has NO PRUNED_HISTORY.json, `first` falls back to smallest-numbered v-dir.

    Per v012 spec.md prune-history paragraph step (b)'s `else`
    clause: when the v(N-1) marker is absent, `first` is the
    smallest-numbered v-directory currently under
    `<spec-root>/history/`. Fixture is constructed so the (ii)
    no-op short-circuit does NOT fire (v002 — oldest surviving
    below max=5 — has NO marker) AND v(N-1)=v004 has NO marker
    either. The resolver path runs through the marker-absent
    impure branch (no `fs.read_text` is invoked) and the pure
    resolver is called with `prior_marker_text=None`. At cycle
    6.c.6b the deletion mechanic widens; v002/v003 (K < N-1 = 4)
    are removed, v004 + v005 remain. At cycle 6.c.7 the
    full step (d) marker write replaces v004's contents with a
    single `PRUNED_HISTORY.json` file containing
    `{"pruned_range": [first, N-1]}` and the supervisor emits
    the `prune-history-pruned` `pass` finding instead of the
    `prune-history-no-op` placeholder.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v002").mkdir(parents=True)
    (spec_root / "history" / "v003").mkdir()
    (spec_root / "history" / "v004").mkdir()
    (spec_root / "history" / "v005").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    # Per v012 spec.md prune-history paragraph step (c): every
    # `<spec-root>/history/vK/` with K < N-1 is deleted. With
    # N=5, that means v002 + v003 are gone; v004 + v005 remain.
    assert not (spec_root / "history" / "v002").exists()
    assert not (spec_root / "history" / "v003").exists()
    assert (spec_root / "history" / "v004").is_dir()
    assert (spec_root / "history" / "v005").is_dir()
    # Per v012 spec.md prune-history paragraph step (d): v(N-1)
    # contents are replaced with a single PRUNED_HISTORY.json
    # carrying `{"pruned_range": [first, N-1]}`. With first=2
    # (smallest surviving v-dir, marker-absent branch) and N=5,
    # the marker contains `{"pruned_range": [2, 4]}`.
    marker_path = spec_root / "history" / "v004" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [2, 4]}
    # Step (e): vN (here v005) is left fully intact — no marker
    # was written into v005, no contents were rearranged. The
    # `is_dir()` assertion above covers existence; this asserts
    # the absence of a stray marker file inside v005.
    assert list((spec_root / "history" / "v005").iterdir()) == []


def test_prune_history_v_dirs_below_threshold_returns_empty_when_max_version_is_one(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` returns [] when max_version == 1.

    Drives the K < N-1 = 0 case: no v-directory satisfies K < 0,
    so the helper returns an empty list. The supervisor's no-op
    short-circuit (i) prevents this branch from being reached in
    practice, but the pure helper is exercised directly to cover
    the degenerate boundary.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=1,
    )
    assert paths == []


def test_prune_history_v_dirs_below_threshold_returns_empty_when_max_version_is_two(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` returns [] when max_version == 2.

    Drives the K < N-1 = 1 case: no v-directory satisfies K < 1
    (v001's K is 1, not less than 1), so the helper returns an
    empty list. v(N-1) = v001 is preserved at this cycle (its
    replacement-with-marker happens at 6.c.7).
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=2,
    )
    assert paths == []


def test_prune_history_v_dirs_below_threshold_returns_v001_when_max_version_is_three(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` returns [v001] when max_version == 3.

    Drives the K < N-1 = 2 case with N=3 history: v001 (K=1)
    satisfies K<2, v002 (K=2) does NOT (it is v(N-1) and is
    preserved at this cycle), v003 (K=3) is fully intact.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=3,
    )
    assert paths == [history / "v001"]


def test_prune_history_v_dirs_below_threshold_returns_v001_v002_when_max_version_is_four(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` returns [v001, v002] when max_version == 4.

    Drives the K < N-1 = 3 case with N=4 history: v001 (K=1) and
    v002 (K=2) both satisfy K<3; v003 (K=3) does NOT (v(N-1)
    preserved); v004 (K=4) is fully intact.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    (history / "v004").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=4,
    )
    assert paths == [history / "v001", history / "v002"]


def test_prune_history_v_dirs_below_threshold_skips_non_directory_entries(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` skips non-directory children defensively.

    Drives the `if not child.is_dir(): continue` guard branch.
    Mirrors the analogous defensive guards in `_find_max_version`
    and `_oldest_below_has_pruned_marker`.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "README.txt").write_text("not a v-dir", encoding="utf-8")
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=3,
    )
    assert paths == [history / "v001"]


def test_prune_history_v_dirs_below_threshold_skips_non_v_prefix_dirs(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` skips directory children whose name lacks `v` prefix.

    Drives the `if not name.startswith("v"): continue` guard
    branch.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "scratch").mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=3,
    )
    assert paths == [history / "v001"]


def test_prune_history_v_dirs_below_threshold_skips_v_prefix_with_non_digit_suffix(
    *,
    tmp_path: Path,
) -> None:
    """`_v_dirs_below_threshold` skips `v<non-digits>` directory children.

    Drives the `if not suffix.isdigit(): continue` guard branch.
    """
    history = tmp_path / "history"
    history.mkdir()
    (history / "vextra").mkdir()
    (history / "v001").mkdir()
    (history / "v002").mkdir()
    (history / "v003").mkdir()
    children = sorted(history.iterdir())
    paths = prune_history._v_dirs_below_threshold(  # noqa: SLF001
        children=children,
        max_version=3,
    )
    assert paths == [history / "v001"]


def test_prune_history_main_deletes_v_dirs_below_threshold_with_n_equal_4(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md prune-history step (c)+(d): with N=4, v001+v002 deleted, v003 marker-replaced.

    Fixture sets up v001/v002/v003/v004 (N=4) with sub-content
    in v001 + v002 + v003 to confirm recursive deletion. After
    prune-history runs, step (c) removes v001 (K=1<3) and v002
    (K=2<3); step (d) replaces v003's contents (K=3=N-1) with a
    single `PRUNED_HISTORY.json` containing
    `{"pruned_range": [1, 3]}`; step (e) leaves v004 (vN) fully
    intact. The supervisor emits the `prune-history-pruned`
    `pass` finding to stdout. Drives the supervisor-level
    integration through `_delete_old_v_dirs` +
    `_replace_v_n_minus_one_with_marker` end-to-end via
    `fs.rmtree` and `fs.write_text`.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    _ = (spec_root / "history" / "v001" / "spec.md").write_text(
        "# v001\n",
        encoding="utf-8",
    )
    (spec_root / "history" / "v002").mkdir()
    (spec_root / "history" / "v002" / "proposed_changes").mkdir()
    _ = (spec_root / "history" / "v002" / "proposed_changes" / "demo.md").write_text(
        "## demo\n",
        encoding="utf-8",
    )
    (spec_root / "history" / "v003").mkdir()
    # Sub-content inside v003 confirms `rmtree` runs on v(N-1)
    # before the marker write — not just empty-dir removal.
    _ = (spec_root / "history" / "v003" / "spec.md").write_text(
        "# v003\n",
        encoding="utf-8",
    )
    (spec_root / "history" / "v003" / "proposed_changes").mkdir()
    _ = (spec_root / "history" / "v003" / "proposed_changes" / "leftover.md").write_text(
        "## leftover\n",
        encoding="utf-8",
    )
    (spec_root / "history" / "v004").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    assert not (spec_root / "history" / "v001").exists()
    assert not (spec_root / "history" / "v002").exists()
    assert (spec_root / "history" / "v003").is_dir()
    assert (spec_root / "history" / "v004").is_dir()
    # Step (d): v003's contents are exactly one PRUNED_HISTORY.json
    # carrying `{"pruned_range": [1, 3]}`. The leftover sub-content
    # written to v003 above MUST be gone (rmtree before write).
    marker_path = spec_root / "history" / "v003" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [1, 3]}
    assert sorted((spec_root / "history" / "v003").iterdir()) == [marker_path]


def test_prune_history_main_deletes_v_dirs_below_threshold_with_n_equal_3(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md prune-history step (c)+(d): with N=3, only v001 deleted, v002 marker-replaced.

    Fixture sets up v001/v002/v003 (N=3); after prune-history
    runs, step (c) removes v001 (K=1<2); step (d) replaces v002's
    contents (K=2=N-1) with `PRUNED_HISTORY.json` containing
    `{"pruned_range": [1, 2]}`; step (e) leaves v003 (vN) fully
    intact. Smallest non-trivial deletion set (single path).
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v002").mkdir()
    (spec_root / "history" / "v003").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    assert not (spec_root / "history" / "v001").exists()
    assert (spec_root / "history" / "v002").is_dir()
    assert (spec_root / "history" / "v003").is_dir()
    marker_path = spec_root / "history" / "v002" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [1, 2]}


def test_prune_history_main_replaces_v_n_minus_one_when_prior_marker_present(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md step (d) with prior marker: v003 marker-replaced carrying first=1.

    Fixture sets up v001/PRUNED_HISTORY.json (carrying
    `{"pruned_range": [1, 1]}`), v002, v003, v004 (N=4). The (ii)
    no-op short-circuit does NOT fire — v001 IS the oldest
    surviving v-dir and DOES carry the marker, so `_oldest_below_
    has_pruned_marker` returns True. To genuinely exercise the
    prior-marker prune path we therefore use a different fixture:
    v001/, v002/PRUNED_HISTORY.json, v003/, v004/. Here v002 is
    the v(N-1)=v003-1 marker location? No — v(N-1)=v003 with
    N=4. Let me use a cleaner setup: place the marker at v(N-1)
    location directly.

    Actual setup: v001 (no marker), v002 (no marker),
    v003/PRUNED_HISTORY.json (`{"pruned_range": [1, 3]}`),
    v004, v005. Here N=5, v(N-1)=v004 has no marker, so
    (ii) does not fire (oldest below max is v001, no marker).
    The `_resolve_first` reads v(N-1)=v004 marker — but v004
    has none. So this would still take the marker-absent branch.

    For the prior-marker branch to fire, we need v(N-1) to
    carry the marker. With N=4, v(N-1)=v003. Set up
    v001 (no marker), v002 (no marker), v003/PRUNED_HISTORY.json
    `{"pruned_range": [1, 3]}`, v004. (ii) fires because v001 is
    oldest and lacks marker; FALSE. Wait: (ii) checks whether
    OLDEST below max has the marker, not whether v(N-1) does.
    With max=4 and v001 oldest below, (ii) fires only if v001
    has the marker. Here v001 doesn't, so (ii) does NOT fire.
    Then `_resolve_first_via_marker_or_children` reads v003's
    marker, gets `pruned_range[0] = 1`, so first=1. Step (c)
    deletes v001 + v002. Step (d) replaces v003 contents with
    `{"pruned_range": [1, 3]}`. Step (e) leaves v004 intact.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v002").mkdir()
    (spec_root / "history" / "v003").mkdir()
    _ = (spec_root / "history" / "v003" / "PRUNED_HISTORY.json").write_text(
        '{"pruned_range": [1, 3]}',
        encoding="utf-8",
    )
    # Also include some content alongside the marker to confirm
    # rmtree clears it before the new marker is written.
    _ = (spec_root / "history" / "v003" / "spec.md").write_text(
        "# v003 stale\n",
        encoding="utf-8",
    )
    (spec_root / "history" / "v004").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    assert not (spec_root / "history" / "v001").exists()
    assert not (spec_root / "history" / "v002").exists()
    marker_path = spec_root / "history" / "v003" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    # `first` carries forward from the prior marker (which read
    # `[1, 3]`); v(N-1)=v003 last is N-1=3. The new marker is a
    # rewrite carrying the same payload — but stale sibling
    # content (spec.md) is gone.
    assert marker_payload == {"pruned_range": [1, 3]}
    assert sorted((spec_root / "history" / "v003").iterdir()) == [marker_path]
    assert (spec_root / "history" / "v004").is_dir()


def test_prune_history_main_writes_marker_when_history_starts_at_v005(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md step (d): non-1-based history → marker first reflects smallest v-dir.

    Fixture sets up v005/v006/v007 (history begins at v005, no
    prior marker, max=7, max-1=6). The (ii) no-op short-circuit
    does NOT fire (v005 is oldest below max=7 and has no marker).
    The `_resolve_first` falls back to smallest v-dir → first=5.
    Step (c) deletes v005 (K=5<6). Step (d) replaces v006 with
    `PRUNED_HISTORY.json` carrying `{"pruned_range": [5, 6]}`.
    Step (e) leaves v007 intact. Confirms the marker-first
    field is NOT hard-coded to 1.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v005").mkdir(parents=True)
    (spec_root / "history" / "v006").mkdir()
    (spec_root / "history" / "v007").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-pruned"
    assert payload["findings"][0]["status"] == "pass"
    assert not (spec_root / "history" / "v005").exists()
    assert (spec_root / "history" / "v006").is_dir()
    assert (spec_root / "history" / "v007").is_dir()
    marker_path = spec_root / "history" / "v006" / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker_payload == {"pruned_range": [5, 6]}


def test_prune_history_build_pruned_history_marker_with_first_one_last_three(
    *,
    tmp_path: Path,  # noqa: ARG001
) -> None:
    """`_build_pruned_history_marker` returns the canonical JSON shape.

    Per v012 spec.md prune-history paragraph step (d): the marker
    contains exactly `{"pruned_range": [first, N-1]}` with no
    timestamps, git SHAs, or identity fields (no-metadata
    invariant). Drives the pure helper with first=1, last=3.
    """
    text = prune_history._build_pruned_history_marker(  # noqa: SLF001
        first=1,
        last=3,
    )
    assert json.loads(text) == {"pruned_range": [1, 3]}


def test_prune_history_build_pruned_history_marker_with_carry_forward_first(
    *,
    tmp_path: Path,  # noqa: ARG001
) -> None:
    """`_build_pruned_history_marker` carries forward an arbitrary `first` value.

    Drives the pure helper with first=5, last=6 — the
    non-1-based history scenario where `first` was resolved from
    the smallest surviving v-dir (and NOT hard-coded to 1).
    """
    text = prune_history._build_pruned_history_marker(  # noqa: SLF001
        first=5,
        last=6,
    )
    assert json.loads(text) == {"pruned_range": [5, 6]}


def test_prune_history_replace_v_n_minus_one_with_marker_replaces_existing_contents(
    *,
    tmp_path: Path,
) -> None:
    """`_replace_v_n_minus_one_with_marker` rmtree's v(N-1) and writes the marker.

    Drives the impure helper end-to-end via the real filesystem.
    Fixture sets up `<history>/v002/spec.md` + `v002/sub/dir/`;
    after the helper runs, the only file under v002 MUST be
    `PRUNED_HISTORY.json` with the canonical content.
    """
    history = tmp_path / "history"
    v_n_minus_one = history / "v002"
    v_n_minus_one.mkdir(parents=True)
    _ = (v_n_minus_one / "spec.md").write_text("# stale\n", encoding="utf-8")
    (v_n_minus_one / "sub").mkdir()
    _ = (v_n_minus_one / "sub" / "leftover.md").write_text(
        "## leftover\n",
        encoding="utf-8",
    )
    result = prune_history._replace_v_n_minus_one_with_marker(  # noqa: SLF001
        history_root=history,
        max_version=3,
        first=1,
    )
    from returns.unsafe import unsafe_perform_io

    unwrapped = unsafe_perform_io(result)
    from returns.result import Success

    assert isinstance(unwrapped, Success)
    marker_path = v_n_minus_one / "PRUNED_HISTORY.json"
    assert marker_path.is_file()
    assert json.loads(marker_path.read_text(encoding="utf-8")) == {
        "pruned_range": [1, 2],
    }
    assert sorted(v_n_minus_one.iterdir()) == [marker_path]


def test_prune_history_replace_v_n_minus_one_with_marker_propagates_rmtree_failure(
    *,
    tmp_path: Path,
) -> None:
    """`_replace_v_n_minus_one_with_marker` lifts an rmtree OSError to IOFailure.

    Fixture sets up an empty `<history>/` with NO v002/ child
    (the rmtree target is absent). `fs.rmtree` lifts the
    FileNotFoundError to PreconditionError; the helper short-
    circuits and the marker write does NOT execute.
    """
    history = tmp_path / "history"
    history.mkdir()
    result = prune_history._replace_v_n_minus_one_with_marker(  # noqa: SLF001
        history_root=history,
        max_version=3,
        first=1,
    )
    from livespec.errors import PreconditionError
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure)
    assert isinstance(unwrapped.failure(), PreconditionError)
    # Marker MUST NOT have been written: v(N-1) didn't exist, so
    # the rmtree failed and `bind` short-circuited the write.
    assert not (history / "v002" / "PRUNED_HISTORY.json").exists()


def test_prune_history_emit_pre_step_skipped_finding_writes_canonical_json(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`_emit_pre_step_skipped_finding` writes the canonical JSON document.

    Per v012 spec.md §"Pre-step skip control": when the resolved
    skip value is True, the wrapper MUST emit a single-finding
    `{"findings": [{"check_id": "pre-step-skipped", "status":
    "skipped", "message": "pre-step checks skipped by user config
    or --skip-pre-check"}]}` JSON document to stdout. This unit
    test drives the helper in isolation and asserts the exact
    payload shape.
    """
    prune_history._emit_pre_step_skipped_finding()  # noqa: SLF001
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "findings": [
            {
                "check_id": "pre-step-skipped",
                "status": "skipped",
                "message": ("pre-step checks skipped by user config " "or --skip-pre-check"),
            },
        ],
    }


def test_prune_history_main_emits_pre_step_skipped_finding_when_skip_pre_check_flag_set(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control": --skip-pre-check emits the finding.

    When the supervisor parses `--skip-pre-check`, the wrapper
    emits a single-finding `pre-step-skipped` skipped JSON
    document to stdout BEFORE running the body. The body still
    runs and emits its own prune-history finding (the
    `prune-history-no-op` skipped finding here, because the
    fixture has only v001). Stdout therefore contains TWO JSON
    lines: the `pre-step-skipped` finding first, then the
    body's `prune-history-no-op` finding. Drives the
    skip-pre-check resolution branch (1) of the spec's 4-rule
    matrix.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--skip-pre-check", "--project-root", str(project_root)],
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 2
    first_payload = json.loads(lines[0])
    assert first_payload["findings"][0]["check_id"] == "pre-step-skipped"
    assert first_payload["findings"][0]["status"] == "skipped"
    second_payload = json.loads(lines[1])
    assert second_payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert second_payload["findings"][0]["status"] == "skipped"


def test_prune_history_main_does_not_emit_pre_step_skipped_finding_when_run_pre_check_flag_set(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (2): --run-pre-check forces skip=False.

    When the supervisor parses `--run-pre-check`, the resolved
    skip value is False (the override-config half of the
    mutually-exclusive flag pair). The wrapper does NOT emit
    the `pre-step-skipped` finding. The body still runs and
    emits its own prune-history finding. Stdout therefore
    contains exactly ONE JSON line — the body's
    `prune-history-no-op` finding.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_does_not_emit_pre_step_skipped_finding_when_neither_flag_set(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (3): neither flag falls through.

    When neither `--skip-pre-check` nor `--run-pre-check` is
    passed, the resolved skip value defers to the
    `.livespec.jsonc` `pre_step_skip_static_checks` config key
    (default False). At cycle 6.c.8 the config-key fallback is
    not yet wired (6.c.9 scope), so the resolved value defaults
    to False and the `pre-step-skipped` finding is NOT emitted.
    Stdout contains exactly ONE JSON line — the body's
    `prune-history-no-op` finding.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_run_pre_check_overrides_config_key_true(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (2): --run-pre-check overrides config.

    Fixture sets `pre_step_skip_static_checks: true` in
    `.livespec.jsonc` AND passes `--run-pre-check` on the CLI.
    Per rule (2), `--run-pre-check` overrides the config key, so
    the resolved skip value is False and the `pre-step-skipped`
    finding is NOT emitted. Stdout contains exactly ONE JSON line
    — the body's `prune-history-no-op` finding. Drives the
    flag-overrides-config branch of `_resolve_skip`.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": true}',
        encoding="utf-8",
    )
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_emits_skipped_finding_when_config_key_true_and_no_flags(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (3): config key true → skip = true.

    Fixture sets `pre_step_skip_static_checks: true` in
    `.livespec.jsonc` and passes neither flag. Per rule (3), the
    resolved skip value defers to the config key, which is True.
    The `pre-step-skipped` finding IS emitted before the body
    runs. Stdout contains TWO JSON lines: the
    `pre-step-skipped` finding first, then the body's
    `prune-history-no-op` finding.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": true}',
        encoding="utf-8",
    )
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 2
    first_payload = json.loads(lines[0])
    assert first_payload["findings"][0]["check_id"] == "pre-step-skipped"
    second_payload = json.loads(lines[1])
    assert second_payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_does_not_emit_skipped_finding_when_config_key_false_and_no_flags(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (3): config key false → skip = false.

    Fixture sets `pre_step_skip_static_checks: false` explicitly
    in `.livespec.jsonc` and passes neither flag. Per rule (3),
    the resolved skip value defers to the config key, which is
    False. The `pre-step-skipped` finding is NOT emitted. Stdout
    contains exactly ONE JSON line — the body's
    `prune-history-no-op` finding. Distinct from the
    config-key-absent test below: this drives the present-and-
    false branch of the JSONC parse.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": false}',
        encoding="utf-8",
    )
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_does_not_emit_skipped_finding_when_config_key_absent(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (3): config key absent → skip = false default.

    Fixture writes `.livespec.jsonc` WITHOUT the
    `pre_step_skip_static_checks` key (an unrelated key only) and
    passes neither flag. Per rule (3) default, the resolved skip
    value is False. The `pre-step-skipped` finding is NOT
    emitted. Stdout contains exactly ONE JSON line — the body's
    `prune-history-no-op` finding. Drives the
    `dict.get(..., False)` default-branch of the resolver.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"some_other_key": "ignored"}',
        encoding="utf-8",
    )
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_does_not_emit_skipped_finding_when_jsonc_file_missing(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control" rule (3): missing `.livespec.jsonc` → skip = false default.

    Fixture has NO `.livespec.jsonc` at the project root and
    passes neither flag. Per spec rule (3) the default skip
    value is False; the resolver must defensively treat a missing
    config file as the default-False case (do NOT raise). The
    `pre-step-skipped` finding is NOT emitted. Stdout contains
    exactly ONE JSON line — the body's `prune-history-no-op`
    finding. Drives the file-missing branch of the resolver.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    # Sanity check — fixture has no .livespec.jsonc.
    assert not (project_root / ".livespec.jsonc").exists()
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_treats_malformed_jsonc_as_default_false(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Spec is silent on malformed `.livespec.jsonc`; resolver defaults to skip=false defensively.

    Fixture writes a syntactically broken `.livespec.jsonc` (not
    valid JSON nor JSONC). The spec §"Pre-step skip control" is
    silent on malformed-config behavior; the resolver MUST
    defensively default to skip=false rather than crash, on the
    principle that a malformed config should not make the
    `prune-history` wrapper unrunnable. The `livespec_jsonc_valid`
    doctor static check is the dedicated mechanism for surfacing
    malformed configs to the user; the prune-history wrapper's
    body-level concern is only the boolean skip resolution.
    Stdout contains exactly ONE JSON line — the body's
    `prune-history-no-op` finding.
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text(
        "this is not jsonc at all { broken",
        encoding="utf-8",
    )
    exit_code = prune_history.main(argv=["--project-root", str(project_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "pre-step-skipped" not in captured.out
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_resolve_skip_returns_true_when_skip_pre_check_flag_set(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_skip` returns IOSuccess(True) when `--skip-pre-check` is set.

    Drives rule (1) of the resolution matrix directly: when
    `namespace.skip_pre_check` is True, the resolver short-
    circuits with True regardless of any config-key value. The
    fixture sets the config key to False to confirm the flag
    overrides it.
    """
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": false}',
        encoding="utf-8",
    )
    namespace = prune_history.build_parser().parse_args(["--skip-pre-check"])
    result = prune_history._resolve_skip(  # noqa: SLF001
        namespace=namespace,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success)
    assert unwrapped.unwrap() is True


def test_prune_history_resolve_skip_returns_false_when_run_pre_check_flag_set(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_skip` returns IOSuccess(False) when `--run-pre-check` is set.

    Drives rule (2) of the resolution matrix directly: when
    `namespace.run_pre_check` is True (and skip_pre_check is
    False), the resolver short-circuits with False regardless of
    config. The fixture sets the config key to True to confirm
    the flag overrides it.
    """
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": true}',
        encoding="utf-8",
    )
    namespace = prune_history.build_parser().parse_args(["--run-pre-check"])
    result = prune_history._resolve_skip(  # noqa: SLF001
        namespace=namespace,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success)
    assert unwrapped.unwrap() is False


def test_prune_history_resolve_skip_returns_config_key_value_when_neither_flag_set(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_skip` reads `pre_step_skip_static_checks` when neither flag is set.

    Drives rule (3) of the resolution matrix directly: when
    neither flag is set, the resolver reads the config key from
    `.livespec.jsonc` at `project_root`. Fixture sets the key to
    True; the resolver returns IOSuccess(True).
    """
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"pre_step_skip_static_checks": true}',
        encoding="utf-8",
    )
    namespace = prune_history.build_parser().parse_args([])
    result = prune_history._resolve_skip(  # noqa: SLF001
        namespace=namespace,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success)
    assert unwrapped.unwrap() is True


def test_prune_history_resolve_skip_returns_false_when_jsonc_missing(
    *,
    tmp_path: Path,
) -> None:
    """`_resolve_skip` returns IOSuccess(False) when `.livespec.jsonc` is absent.

    Drives the file-missing defensive branch: the resolver MUST
    NOT raise when the config file does not exist — it returns
    the spec-prescribed default (False) so a freshly-cloned or
    pre-seed project doesn't crash the prune-history wrapper.
    """
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    project_root = tmp_path
    assert not (project_root / ".livespec.jsonc").exists()
    namespace = prune_history.build_parser().parse_args([])
    result = prune_history._resolve_skip(  # noqa: SLF001
        namespace=namespace,
        project_root=project_root,
    )
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success)
    assert unwrapped.unwrap() is False


def test_prune_history_main_invokes_pre_step_doctor_when_skip_resolves_false(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Sub-command lifecycle": skip=False invokes pre-step doctor.

    Cycle 6.c.10 wires the pre-step doctor static invocation. When
    `--run-pre-check` forces `skip=false`, the wrapper MUST invoke
    `bin/doctor_static.py` as a subprocess BEFORE running the
    prune-history body. This test re-monkeypatches the helper
    (overriding the autouse no-op default) with a recorder stub
    that captures the `project_root` it was called with; the test
    then asserts the recorder fired exactly once with the spec'd
    `--project-root` value, and that the body STILL runs (no-op
    finding emitted because the fixture has only v001).
    """
    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    invocations: list[Path] = []

    def _recording_pre_step(*, project_root: Path) -> IOResult[None, object]:
        invocations.append(project_root)
        return IOResult.from_value(None)

    monkeypatch.setattr(
        prune_history,
        "_invoke_pre_step_doctor",
        _recording_pre_step,
        raising=True,
    )
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert invocations == [project_root]
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


def test_prune_history_main_does_not_invoke_pre_step_doctor_when_skip_pre_check_flag_set(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per v012 spec.md §"Pre-step skip control": skip=True suppresses doctor invocation.

    When `--skip-pre-check` resolves skip=True, the wrapper MUST
    emit the `pre-step-skipped` finding and proceed WITHOUT
    invoking the pre-step doctor static phase. This test re-
    monkeypatches `livespec.io.proc.run_subprocess` (the deepest
    seam the helper would call) with a recording stub; after
    `main()` returns, the test asserts the recorder was never
    called. The body still runs and emits its own
    `prune-history-no-op` finding. The recorder is also exercised
    once at the end of the test to keep its body line covered
    (otherwise the unused branch would leave dead lines per
    `[tool.coverage.report].fail_under = 100`).
    """
    from livespec.io import proc

    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)
    invocations: list[list[str]] = []

    def _recording_run_subprocess(*, argv: list[str]) -> IOResult[object, object]:
        invocations.append(argv)
        return IOResult.from_value(None)

    monkeypatch.setattr(proc, "run_subprocess", _recording_run_subprocess, raising=True)
    exit_code = prune_history.main(
        argv=["--skip-pre-check", "--project-root", str(project_root)],
    )
    assert invocations == []  # main() did NOT trigger run_subprocess
    captured = capsys.readouterr()
    assert exit_code == 0
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 2
    first_payload = json.loads(lines[0])
    assert first_payload["findings"][0]["check_id"] == "pre-step-skipped"
    second_payload = json.loads(lines[1])
    assert second_payload["findings"][0]["check_id"] == "prune-history-no-op"
    # Cover the recorder body (otherwise its def-line counts but its
    # body-lines stay uncovered since main() did not call it).
    _ = _recording_run_subprocess(argv=["sentinel"])
    assert invocations == [["sentinel"]]


def test_prune_history_main_short_circuits_with_exit_three_on_pre_step_doctor_fail_finding(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per: fail finding -> exit 3.

    "On any `status: \"fail\"` finding from pre-step, the wrapper
    aborts with exit 3 and sub-command logic does not run." This
    test re-monkeypatches the helper with a stub that returns
    IOFailure(PreconditionError) — simulating a doctor invocation
    that found one or more fail-status findings. The supervisor's
    pattern-match MUST lift this to exit 3 (PreconditionError's
    `exit_code` ClassVar). The body MUST NOT run; the test
    asserts the v001 directory is unchanged afterward (no marker
    written, no rmtree).
    """
    from livespec.errors import PreconditionError

    project_root = _make_v001_only_spec_root(tmp_path=tmp_path)

    def _failing_pre_step(*, project_root: Path) -> IOResult[None, PreconditionError]:
        del project_root
        return IOResult.from_failure(
            PreconditionError("pre-step doctor reported 1 fail-status finding(s)"),
        )

    monkeypatch.setattr(
        prune_history,
        "_invoke_pre_step_doctor",
        _failing_pre_step,
        raising=True,
    )
    exit_code = prune_history.main(
        argv=["--run-pre-check", "--project-root", str(project_root)],
    )
    assert exit_code == 3
    # Body did NOT run: v001 directory remains, no PRUNED_HISTORY.json marker.
    v001_dir = project_root / "SPECIFICATION" / "history" / "v001"
    assert v001_dir.is_dir()
    assert not (v001_dir / "PRUNED_HISTORY.json").exists()


def test_prune_history_invoke_pre_step_doctor_returns_iosuccess_when_no_fail_findings(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_invoke_pre_step_doctor` returns IOSuccess(None) when doctor reports no failures.

    Drives the helper directly, monkeypatching
    `livespec.io.proc.run_subprocess` to return a fake
    CompletedProcess whose stdout carries a `findings` payload
    with zero fail-status entries (one pass + one skipped). The
    helper MUST return IOSuccess(None) so the railway proceeds to
    the prune-history body.
    """
    import subprocess

    from livespec.io import proc
    from returns.result import Success
    from returns.unsafe import unsafe_perform_io

    captured_argv: list[list[str]] = []

    def _fake_run_subprocess(
        *, argv: list[str]
    ) -> IOResult[subprocess.CompletedProcess[str], object]:
        captured_argv.append(argv)
        completed = subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps(
                {
                    "findings": [
                        {"check_id": "x", "status": "pass", "message": "ok"},
                        {"check_id": "y", "status": "skipped", "message": "n/a"},
                    ],
                },
            )
            + "\n",
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", _fake_run_subprocess, raising=True)
    # The autouse stub replaced the helper at module scope; restore the
    # real helper so this unit test exercises the real implementation.
    monkeypatch.delattr(prune_history, "_invoke_pre_step_doctor", raising=False)
    from livespec.commands._prune_history_railway import (
        _invoke_pre_step_doctor,
    )

    result = _invoke_pre_step_doctor(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Success)
    # The fake recorded one invocation; the argv carries --project-root <tmp_path>.
    assert len(captured_argv) == 1
    assert "--project-root" in captured_argv[0]
    assert str(tmp_path) in captured_argv[0]


def test_prune_history_invoke_pre_step_doctor_returns_iofailure_when_any_fail_finding(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_invoke_pre_step_doctor` returns IOFailure when doctor reports at least one fail.

    Drives the helper directly, monkeypatching
    `livespec.io.proc.run_subprocess` to return a fake
    CompletedProcess whose stdout carries a `findings` payload
    with one fail-status entry. The helper MUST return
    IOFailure(PreconditionError) so the wrapper short-circuits
    with exit 3.
    """
    import subprocess

    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    def _fake_run_subprocess(
        *, argv: list[str]
    ) -> IOResult[subprocess.CompletedProcess[str], object]:
        completed = subprocess.CompletedProcess(
            args=argv,
            returncode=3,
            stdout=json.dumps(
                {
                    "findings": [
                        {"check_id": "x", "status": "fail", "message": "broken"},
                    ],
                },
            )
            + "\n",
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", _fake_run_subprocess, raising=True)
    monkeypatch.delattr(prune_history, "_invoke_pre_step_doctor", raising=False)
    from livespec.commands._prune_history_railway import (
        _invoke_pre_step_doctor,
    )

    result = _invoke_pre_step_doctor(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure)
    err = unwrapped.failure()
    assert isinstance(err, PreconditionError)
    assert err.exit_code == 3


def test_prune_history_invoke_pre_step_doctor_returns_iofailure_when_stdout_is_malformed_json(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_invoke_pre_step_doctor` returns IOFailure when doctor stdout is not valid JSON.

    Drives the malformed-JSON defensive branch of the fold helper.
    The doctor MUST emit `{"findings": [...]}` per its stdout
    contract; if instead the subprocess emitted garbage (e.g.,
    crash text, non-JSON), the wrapper short-circuits with
    IOFailure(PreconditionError) carrying a diagnostic message.
    """
    import subprocess

    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    def _fake_run_subprocess(
        *, argv: list[str]
    ) -> IOResult[subprocess.CompletedProcess[str], object]:
        completed = subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout="this is not JSON at all",
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", _fake_run_subprocess, raising=True)
    monkeypatch.delattr(prune_history, "_invoke_pre_step_doctor", raising=False)
    from livespec.commands._prune_history_railway import (
        _invoke_pre_step_doctor,
    )

    result = _invoke_pre_step_doctor(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure)
    err = unwrapped.failure()
    assert isinstance(err, PreconditionError)
    assert "malformed JSON" in str(err)


def test_prune_history_invoke_pre_step_doctor_returns_iofailure_when_findings_key_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_invoke_pre_step_doctor` returns IOFailure when stdout JSON lacks 'findings'.

    Drives the missing-`findings`-key defensive branch of the fold
    helper. A doctor stdout that is valid JSON but missing the
    required `findings` key (e.g., a top-level non-dict, or a
    dict without that key) MUST short-circuit with
    IOFailure(PreconditionError) per the stdout contract.
    """
    import subprocess

    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    def _fake_run_subprocess(
        *, argv: list[str]
    ) -> IOResult[subprocess.CompletedProcess[str], object]:
        completed = subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps({"some_other_key": "ignored"}) + "\n",
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", _fake_run_subprocess, raising=True)
    monkeypatch.delattr(prune_history, "_invoke_pre_step_doctor", raising=False)
    from livespec.commands._prune_history_railway import (
        _invoke_pre_step_doctor,
    )

    result = _invoke_pre_step_doctor(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure)
    err = unwrapped.failure()
    assert isinstance(err, PreconditionError)
    assert "missing 'findings' key" in str(err)


def test_prune_history_invoke_pre_step_doctor_returns_iofailure_when_findings_is_not_list(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_invoke_pre_step_doctor` returns IOFailure when 'findings' is not a list.

    Drives the `findings`-not-a-list defensive branch of the fold
    helper. A doctor stdout that is a dict with a `findings` key
    whose value is not a JSON array (e.g., a string, dict, or
    null) MUST short-circuit with IOFailure(PreconditionError).
    """
    import subprocess

    from livespec.errors import PreconditionError
    from livespec.io import proc
    from returns.result import Failure
    from returns.unsafe import unsafe_perform_io

    def _fake_run_subprocess(
        *, argv: list[str]
    ) -> IOResult[subprocess.CompletedProcess[str], object]:
        completed = subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=json.dumps({"findings": "this should be a list"}) + "\n",
            stderr="",
        )
        return IOResult.from_value(completed)

    monkeypatch.setattr(proc, "run_subprocess", _fake_run_subprocess, raising=True)
    monkeypatch.delattr(prune_history, "_invoke_pre_step_doctor", raising=False)
    from livespec.commands._prune_history_railway import (
        _invoke_pre_step_doctor,
    )

    result = _invoke_pre_step_doctor(project_root=tmp_path)
    unwrapped = unsafe_perform_io(result)
    assert isinstance(unwrapped, Failure)
    err = unwrapped.failure()
    assert isinstance(err, PreconditionError)
    assert "'findings' is not a list" in str(err)
