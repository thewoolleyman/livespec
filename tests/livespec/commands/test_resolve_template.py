"""Tests for livespec.commands.resolve_template.

resolve_template emits the resolved template directory path on
stdout. The path-computation formula derives the bundle root
from this file's location: parents[0]=commands/,
parents[1]=livespec/, parents[2]=scripts/,
parents[3]=.claude-plugin/.

Minimum-viable scope: only the --template flow is implemented;
the default `.livespec.jsonc`-walking flow is not yet wired
(seed/SKILL.md prose uses --template livespec pre-seed). With
--template required, the seed unblocks for any consumer.
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

    Per the spec: the bundle root is computed
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
     built-in template name
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


def test_resolve_template_emits_bundle_path_for_builtin_livespec_with_diagrams(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--template livespec-with-diagrams → resolves to the bundled v2 template directory.

    The third built-in template name (alongside `livespec` and
    `minimal`). Ships the v2 spec_files manifest with the
    Mermaid-first seeded spec files plus the PlantUML
    escape-hatch source + rendered SVG pair demonstrating the
    diagram_source / diagram_rendered file kinds.
    """
    exit_code = resolve_template.main(argv=["--template", "livespec-with-diagrams"])
    assert exit_code == 0
    captured = capsys.readouterr()
    line = captured.out.rstrip("\n")
    path = Path(line)
    assert path.is_absolute()
    assert path.name == "livespec-with-diagrams"
    assert path.parent.name == "specification-templates"
    assert path.is_dir()
    assert (path / "template.json").is_file()


def test_resolve_template_resolves_user_path_with_template_json(
    *,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """--template <relative-path> + template.json present → emits absolute path, exit 0.

    Per the spec: any value other than a built-in
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

    Per the spec: exit 3 on "resolved path lacks
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

    Per the spec: exit 3 on "resolved path
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

    Per the spec: exit 2 on "bad CLI usage". Drives
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
    """Missing --template (required flag) → exit 2 (UsageError).

    Minimum-viable scope: --template is required (the default
    `.livespec.jsonc`-walking flow is not yet wired). The spec
    lists --template as OPTIONAL; this minimum-viable surface
    deviates by making it required.
    """
    exit_code = resolve_template.main(argv=[])
    assert exit_code == 2


def test_resolve_template_default_project_root_is_cwd(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """--project-root defaults to Path.cwd() per the spec.

    Drives the cwd-fallback branch of `_resolve_project_root`
    (the `Path.cwd() if namespace.project_root is None` path).
    `monkeypatch.chdir(tmp_path)` isolates the test from the
    runner's invocation cwd so the fallback resolves
    deterministically to a writable scratch root rather than the
    repo cwd (preventing tmp-artifact leakage into the repo tree).
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


def test_resolve_template_module_declares_hkt_erosion_pragma() -> None:
    """`commands/resolve_template.py` carries the file-level HKT-erosion pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains lose
    flow-narrowing through pyright strict mode. The file-level
    pragma suppresses the three HKT-related categories;
    reportArgumentType stays ON globally. This contract test
    pins the pragma so a future reformatter that drops it
    surfaces immediately rather than silently re-introducing
    the 8 pyright errors.
    """
    import inspect

    from livespec.commands import resolve_template as resolve_template_command

    source = inspect.getsource(resolve_template_command)
    assert source.startswith(
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n",
    ), "commands/resolve_template.py must declare the HKT-erosion pragma as its first line"
