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

__all__: list[str] = []


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

    Per v012 contracts.md §"Wrapper CLI surface" prune-history row
    + the universal `--project-root <path>` baseline (PROPOSAL.md
    §"Project-root detection contract" explicitly enumerates
    `bin/prune_history.py` as a project-state wrapper that accepts
    the flag).
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
    carry-forward `first` resolution per spec.md step (b). Cycle
    6.c.5 emits the no-op-pending-prune-mechanic placeholder
    finding (acting on the resolved `first` is reserved for
    cycles 6.c.6+), so we assert the placeholder finding is on
    stdout. Subsequent cycles replace the placeholder with the
    full 5-step mechanic.
    """
    spec_root = tmp_path / "SPECIFICATION"
    (spec_root / "history" / "v001").mkdir(parents=True)
    (spec_root / "history" / "v002").mkdir()
    exit_code = prune_history.main(argv=["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"


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
    carry a marker. The resolver path runs end-to-end through
    the impure `fs.read_text` boundary, exercising the integration
    seam between `_run_prune` and `_resolve_first`. Cycle 6.c.5
    does NOT yet act on the resolved `first`; the wrapper still
    emits the no-op finding for now (acting is reserved for
    cycles 6.c.6+).
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
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert payload["findings"][0]["status"] == "skipped"


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
    resolver is called with `prior_marker_text=None`. Cycle
    6.c.5 still emits no-op (no acting yet).
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
    assert payload["findings"][0]["check_id"] == "prune-history-no-op"
    assert payload["findings"][0]["status"] == "skipped"
