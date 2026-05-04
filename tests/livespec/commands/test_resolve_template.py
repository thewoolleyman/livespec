"""Tests for livespec.commands.resolve_template.

Per PROPOSAL.md §"Template resolution contract"
and Plan Phase 3 sub-step 12 (codified at v028 D1 with the
`Path(__file__).resolve().parents[3]` formula): resolve_template
emits the resolved template directory path on stdout. The path-
computation formula derives the bundle root from this file's
location: parents[0]=commands/, parents[1]=livespec/,
parents[2]=scripts/, parents[3]=.claude-plugin/.

Phase 3 minimum-viable scope (Phase 6 in-band gap-fix per
2026-05-03T01:31:03Z user gate): only the --template flow is
implemented; the default `.livespec.jsonc`-walking flow is
deferred to Phase 7 (no consumer in Phase 6's seed self-
application — the seed/SKILL.md prose uses --template livespec
pre-seed per v017 Q2). With --template required, the seed
unblocks for Phase 6.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.commands import resolve_template

__all__: list[str] = []


def test_resolve_template_main_exists_and_returns_int(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/resolve_template.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = resolve_template.main(argv=["--template", "livespec"])
    assert isinstance(exit_code, int)
    _ = capsys.readouterr()


def test_resolve_template_emits_bundle_path_for_builtin_livespec(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--template livespec → emits <bundle-root>/specification-templates/livespec on stdout, exit 0.

    Per PROPOSAL.md: the bundle root is computed
    via `Path(__file__).resolve().parents[3]` from the impl file.
    Asserts the resolved path is absolute, ends in
    `.../specification-templates/livespec`, and the directory
    exists on disk (we're running self-applied against the same
    plugin bundle that this test lives in).
    """
    exit_code = resolve_template.main(argv=["--template", "livespec"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.endswith("\n")
    line = captured.out.rstrip("\n")
    path = Path(line)
    assert path.is_absolute()
    assert path.name == "livespec"
    assert path.parent.name == "specification-templates"
    assert path.exists()
    assert path.is_dir()


def test_resolve_template_emits_bundle_path_for_builtin_minimal(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--template minimal → emits <bundle-root>/specification-templates/minimal on stdout, exit 0.

     Mirror of the `livespec` built-in test against the second v1
     built-in template name per PROPOSAL §"Custom templates"
    .
    """
    exit_code = resolve_template.main(argv=["--template", "minimal"])
    assert exit_code == 0
    captured = capsys.readouterr()
    line = captured.out.rstrip("\n")
    path = Path(line)
    assert path.is_absolute()
    assert path.name == "minimal"
    assert path.parent.name == "specification-templates"
    assert path.exists()
    assert path.is_dir()


def test_resolve_template_resolves_user_path_with_template_json(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--template <relative-path> + template.json present → emits absolute path, exit 0.

    Per PROPOSAL.md: any value other than a built-in
    name is treated as a path relative to --project-root. The
    wrapper validates (a) the directory exists and (b) it contains
    `template.json`.
    """
    template_dir = tmp_path / "my-template"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text("{}", encoding="utf-8")
    exit_code = resolve_template.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--template",
            "my-template",
        ],
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    line = captured.out.rstrip("\n")
    assert Path(line) == template_dir.resolve()


def test_resolve_template_user_path_missing_template_json_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """--template <relative-path> without template.json → exit 3 (PreconditionError).

    Per PROPOSAL.md: exit 3 on "resolved path lacks
    template.json".
    """
    template_dir = tmp_path / "bare-dir"
    template_dir.mkdir()
    exit_code = resolve_template.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--template",
            "bare-dir",
        ],
    )
    assert exit_code == 3


def test_resolve_template_user_path_does_not_exist_returns_3(
    *,
    tmp_path: Path,
) -> None:
    """--template <relative-path-does-not-exist> → exit 3.

    Per PROPOSAL.md: exit 3 on "resolved path
    missing".
    """
    exit_code = resolve_template.main(
        argv=[
            "--project-root",
            str(tmp_path),
            "--template",
            "no-such-dir",
        ],
    )
    assert exit_code == 3


def test_resolve_template_unknown_flag_returns_2() -> None:
    """Unknown CLI flag → exit 2 (UsageError).

    Per PROPOSAL.md: exit 2 on "bad CLI usage". Drives
    the parse_argv stage on the railway: an unknown flag surfaces
    as an argparse SystemExit, which io/cli's @impure_safe maps
    to UsageError; the supervisor's pattern-match lifts to
    err.exit_code = 2.
    """
    exit_code = resolve_template.main(
        argv=["--template", "livespec", "--no-such-flag"],
    )
    assert exit_code == 2


def test_resolve_template_missing_template_flag_returns_2() -> None:
    """Missing --template (Phase-3-min required flag) → exit 2 (UsageError).

    Phase 3 minimum-viable scope: --template is required (the
    default `.livespec.jsonc`-walking flow is Phase 7 work).
    PROPOSAL §"Template resolution contract" lists
    --template as OPTIONAL; this Phase-3-minimum deviates by
    making it required, captured in
    `bootstrap/decisions.md` under the Phase 6 resolve_template
    in-band gap-fix entry. The deviation is in-Phase-7-redress
    when the default flow lands.
    """
    exit_code = resolve_template.main(argv=[])
    assert exit_code == 2


def test_resolve_template_default_project_root_is_cwd(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """--project-root defaults to Path.cwd() per PROPOSAL.

    Drives the cwd-fallback branch of `_resolve_project_root`
    (the `Path.cwd() if namespace.project_root is None` path).
    `monkeypatch.chdir(tmp_path)` isolates the test from the
    runner's invocation cwd so the fallback resolves
    deterministically to a writable scratch root rather than the
    repo cwd (preventing tmp-artifact leakage into the repo
    tree per the cycle-122 lesson recorded in
    `bootstrap/decisions.md`).
    """
    template_dir = tmp_path / "tmpl"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = resolve_template.main(argv=["--template", "tmpl"])
    assert exit_code == 0
    captured = capsys.readouterr()
    line = captured.out.rstrip("\n")
    assert Path(line) == template_dir.resolve()
