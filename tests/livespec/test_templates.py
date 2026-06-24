"""Tests for livespec.templates — the shared template-value resolver.

`resolve_template_value` is the single source of truth for the
built-in template name set (`{livespec, livespec-with-diagrams,
minimal}`) and the custom-template on-disk path rule shared by
`commands/resolve_template.py`, `doctor/static/template_exists.py`,
and `doctor/static/_template_manifest.py`. The arms under test:

- a built-in name resolves (unconditionally) to its bundled
  `specification-templates/<name>` directory;
- a project-relative directory carrying `template.json` resolves to
  that (resolved) directory;
- a value that is neither a built-in nor an existing directory fails
  with `reason="missing_dir"`;
- an existing directory lacking `template.json` fails with
  `reason="missing_manifest"`.
"""

from __future__ import annotations

from pathlib import Path

from livespec import templates
from returns.result import Failure, Success

__all__: list[str] = []


def test_builtin_template_names_are_the_three_shipped_builtins() -> None:
    """The shared built-in set is exactly the three bundled templates.

    Pins the single definition that `template_exists` formerly
    diverged from (it omitted `livespec-with-diagrams`, the
    livespec-kfjd regression).
    """
    expected = frozenset({"livespec", "livespec-with-diagrams", "minimal"})
    assert expected == templates.BUILTIN_TEMPLATE_NAMES


def test_resolve_builtin_livespec_returns_bundled_directory() -> None:
    """`livespec` resolves to `<bundle>/specification-templates/livespec`.

    Built-in names resolve unconditionally (no on-disk probe), so the
    returned path is `BUILTIN_TEMPLATES_DIR / name` regardless of
    project root.
    """
    result = templates.resolve_template_value(
        value="livespec",
        project_root=Path("/nonexistent-project-root"),
    )
    assert result == Success(templates.BUILTIN_TEMPLATES_DIR / "livespec")


def test_resolve_builtin_livespec_with_diagrams_returns_bundled_directory() -> None:
    """`livespec-with-diagrams` resolves — the arm `template_exists` dropped.

    The diagrams built-in is a first-class member of the shared set;
    its bundled directory exists on disk (this repo ships it).
    """
    result = templates.resolve_template_value(
        value="livespec-with-diagrams",
        project_root=Path("/nonexistent-project-root"),
    )
    expected = templates.BUILTIN_TEMPLATES_DIR / "livespec-with-diagrams"
    assert result == Success(expected)
    assert (expected / "template.json").is_file()


def test_resolve_custom_path_with_template_json_returns_resolved_dir(
    *,
    tmp_path: Path,
) -> None:
    """A project-relative dir carrying `template.json` resolves to itself.

    The returned path is the `.resolve()`-canonicalised directory, so
    the assertion compares against `template_dir.resolve()`.
    """
    template_dir = tmp_path / "my-template"
    template_dir.mkdir()
    _ = (template_dir / "template.json").write_text("{}", encoding="utf-8")
    result = templates.resolve_template_value(
        value="my-template",
        project_root=tmp_path,
    )
    assert result == Success(template_dir.resolve())


def test_resolve_unknown_name_fails_with_missing_dir(*, tmp_path: Path) -> None:
    """A value that is neither built-in nor an existing dir → missing_dir.

    The failure names the probed (resolved) candidate path so callers
    can surface it in a diagnostic.
    """
    result = templates.resolve_template_value(
        value="no-such-template",
        project_root=tmp_path,
    )
    expected_candidate = (tmp_path / "no-such-template").resolve()
    assert result == Failure(
        templates.TemplateResolutionFailure(
            candidate=expected_candidate,
            reason="missing_dir",
        ),
    )


def test_resolve_dir_without_template_json_fails_with_missing_manifest(
    *,
    tmp_path: Path,
) -> None:
    """An existing dir lacking `template.json` → missing_manifest.

    Distinguishes the "directory present but not a template" arm from
    the "no directory at all" arm — the discrimination
    `resolve_template`'s two exit-3 messages rely on.
    """
    bare_dir = tmp_path / "bare-template"
    bare_dir.mkdir()
    result = templates.resolve_template_value(
        value="bare-template",
        project_root=tmp_path,
    )
    assert result == Failure(
        templates.TemplateResolutionFailure(
            candidate=bare_dir.resolve(),
            reason="missing_manifest",
        ),
    )
