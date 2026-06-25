"""Outside-in test for `dev-tooling/checks/copier_template_smoke.py`.

The smoke check runs `copier copy` against `templates/impl-plugin/`
with a stock answers fixture, then verifies the generated tree
contains every expected file and that JSON files parse. The check
is the C.6 acceptance gate for Phase C of the multi-repo split per
research/workflow-processes/multi-repo-split-execution-plan.md.

Pass case: invoke the script with cwd=<livespec-core repo root>;
expect exit 0 and the structured success diagnostic.

Fail case: invoke the script with cwd=<tmp_path with no
templates/>; expect exit non-zero and the missing-template
diagnostic.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_COPIER_TEMPLATE_SMOKE = _REPO_ROOT / "dev-tooling" / "checks" / "copier_template_smoke.py"


def test_smoke_check_passes_against_real_template() -> None:
    """Pass case: invoking the script at the repo root generates a clean tree."""
    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"smoke check should exit 0 against the real templates/impl-plugin/ tree; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "copier-template-smoke-ok" in result.stderr, (
        f"expected success diagnostic 'copier-template-smoke-ok' in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_fails_when_template_missing(*, tmp_path: Path) -> None:
    """Fail case: cwd has no templates/impl-plugin/; script emits the missing-template diagnostic."""
    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject when templates/impl-plugin/copier.yml is missing; "
        f"got returncode={result.returncode}"
    )
    assert "copier-template-smoke-missing-template" in result.stderr, (
        f"expected 'copier-template-smoke-missing-template' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_fails_when_copier_copy_errors(*, tmp_path: Path) -> None:
    """Fail case: copier.yml has a syntax error; copier subprocess fails.

    The template's copier.yml is intentionally malformed YAML so the
    copier subprocess exits non-zero. The smoke check MUST surface
    the copy-failed diagnostic with returncode + stdout/stderr tails.
    """
    template_dir = tmp_path / "templates" / "impl-plugin"
    template_dir.mkdir(parents=True)
    # Malformed YAML: unclosed mapping with a tab character — copier
    # rejects this with a YAMLError, exiting non-zero before any
    # rendering happens.
    (template_dir / "copier.yml").write_text(
        "_templates_suffix: .jinja\nthis is: not\tvalid yaml: at all: [\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject when copier copy fails; " f"got returncode={result.returncode}"
    )
    assert "copier-template-smoke-copy-failed" in result.stderr, (
        f"expected 'copier-template-smoke-copy-failed' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_fails_when_expected_files_missing(*, tmp_path: Path) -> None:
    """Fail case: minimal copier.yml; copier succeeds but generates a sparse tree.

    The template carries only copier.yml (no .jinja files), so copier
    generates an empty tree. The smoke check's expected-files list
    won't be satisfied and MUST surface the missing-output diagnostic.
    """
    template_dir = tmp_path / "templates" / "impl-plugin"
    template_dir.mkdir(parents=True)
    (template_dir / "copier.yml").write_text(
        "_templates_suffix: .jinja\n_exclude:\n  - copier.yml\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject when expected files are missing; "
        f"got returncode={result.returncode}"
    )
    assert "copier-template-smoke-missing-output" in result.stderr, (
        f"expected 'copier-template-smoke-missing-output' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_emits_canonical_slug_drift_when_targets_block_mismatches(
    *,
    tmp_path: Path,
) -> None:
    """Fail case: justfile.jinja stamps a stale canonical-slug set; check emits drift diagnostic.

    The template's `justfile.jinja` is replaced with a recipe whose
    `targets=(...)` array contains a single bogus slug
    (`check-stale-slug`). When the smoke check verifies the stamped
    aggregate against `livespec_dev_tooling.canonical_checks.
    canonical_check_slugs()`, it MUST surface the
    `copier-template-smoke-canonical-slug-drift` diagnostic on stderr.

    This test only runs when `livespec_dev_tooling.canonical_checks`
    is importable (post-bump state). When the pin still points at a
    release without the module, the check's graceful-skip path is
    exercised instead and this test is skipped via pytest.importorskip
    at the top of the test body.
    """
    _ = pytest.importorskip("livespec_dev_tooling.canonical_checks")

    template_dir = tmp_path / "templates" / "impl-plugin"
    template_dir.mkdir(parents=True)
    # No `_jinja_extensions:` registered so copier copy succeeds
    # without the extension; the stamped targets list is hand-rolled
    # to a stale single-slug shape that the canonical-slug check MUST
    # reject.
    (template_dir / "copier.yml").write_text(
        "_templates_suffix: .jinja\n_exclude:\n  - copier.yml\n",
        encoding="utf-8",
    )
    # Minimal stubs for every file in _EXPECTED_FILES so the missing-
    # output branch doesn't fire and the JSON-parse branch passes.
    # The answers-file boilerplate renders to `.copier-answers.yml`
    # (copier's default `_answers_file`), mirroring the real template.
    (template_dir / "{{ _copier_conf.answers_file }}.jinja").write_text(
        "{{ _copier_answers|to_nice_yaml -}}\n", encoding="utf-8"
    )
    (template_dir / ".python-version.jinja").write_text("3.13\n", encoding="utf-8")
    (template_dir / ".mise.toml.jinja").write_text("[tools]\n", encoding="utf-8")
    (template_dir / "pyproject.toml.jinja").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    # Hand-rolled justfile with a `check:` recipe whose `targets=(...)`
    # array carries a single stale slug. The eight-space indentation
    # matches the canonical Jinja-loop output shape so the smoke
    # check's regex reliably extracts the offending list.
    (template_dir / "justfile.jinja").write_text(
        "check:\n"
        "    #!/usr/bin/env bash\n"
        "    set -uo pipefail\n"
        "    targets=(\n"
        "        check-stale-slug\n"
        "    )\n",
        encoding="utf-8",
    )
    (template_dir / "lefthook.yml.jinja").write_text(
        "pre-commit:\n  commands: {}\n", encoding="utf-8"
    )
    workflows = template_dir / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml.jinja").write_text("name: ci\n", encoding="utf-8")
    (workflows / "copier-update-drift.yml.jinja").write_text("name: drift\n", encoding="utf-8")
    plugin_dir = template_dir / ".claude-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "marketplace.json.jinja").write_text("{}\n", encoding="utf-8")
    (plugin_dir / "plugin.json.jinja").write_text("{}\n", encoding="utf-8")
    spec_dir = template_dir / "SPECIFICATION"
    spec_dir.mkdir()
    (spec_dir / "README.md.jinja").write_text("# README\n", encoding="utf-8")
    claude_dir = template_dir / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject canonical-slug drift; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "copier-template-smoke-canonical-slug-drift" in result.stderr, (
        f"expected 'copier-template-smoke-canonical-slug-drift' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_fails_when_generated_json_invalid(*, tmp_path: Path) -> None:
    """Fail case: marketplace.json.jinja renders to invalid JSON; check emits invalid-json diagnostic.

    The template carries .jinja files that match _EXPECTED_FILES but
    `marketplace.json.jinja` produces non-JSON content. All required
    output files exist (so the missing-output branch doesn't fire),
    but the JSON parse check rejects.
    """
    template_dir = tmp_path / "templates" / "impl-plugin"
    template_dir.mkdir(parents=True)
    (template_dir / "copier.yml").write_text(
        "_templates_suffix: .jinja\n_exclude:\n  - copier.yml\n",
        encoding="utf-8",
    )
    # Minimal stubs for every file in _EXPECTED_FILES so the
    # missing-output branch doesn't fire. Each file is intentionally
    # trivial; only marketplace.json is malformed. The answers-file
    # boilerplate renders to `.copier-answers.yml` (copier's default
    # `_answers_file`), mirroring the real template.
    (template_dir / "{{ _copier_conf.answers_file }}.jinja").write_text(
        "{{ _copier_answers|to_nice_yaml -}}\n", encoding="utf-8"
    )
    (template_dir / ".python-version.jinja").write_text("3.13\n", encoding="utf-8")
    (template_dir / ".mise.toml.jinja").write_text("[tools]\n", encoding="utf-8")
    (template_dir / "pyproject.toml.jinja").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    (template_dir / "justfile.jinja").write_text("default:\n    @echo ok\n", encoding="utf-8")
    (template_dir / "lefthook.yml.jinja").write_text(
        "pre-commit:\n  commands: {}\n", encoding="utf-8"
    )
    workflows = template_dir / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml.jinja").write_text("name: ci\n", encoding="utf-8")
    (workflows / "copier-update-drift.yml.jinja").write_text("name: drift\n", encoding="utf-8")
    plugin_dir = template_dir / ".claude-plugin"
    plugin_dir.mkdir()
    # Malformed JSON: opening brace with no closing.
    (plugin_dir / "marketplace.json.jinja").write_text("{ not valid json", encoding="utf-8")
    (plugin_dir / "plugin.json.jinja").write_text("{}\n", encoding="utf-8")
    spec_dir = template_dir / "SPECIFICATION"
    spec_dir.mkdir()
    (spec_dir / "README.md.jinja").write_text("# README\n", encoding="utf-8")
    claude_dir = template_dir / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject when generated JSON is invalid; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "copier-template-smoke-invalid-json" in result.stderr, (
        f"expected 'copier-template-smoke-invalid-json' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_smoke_check_fails_when_generated_justfile_does_not_parse(*, tmp_path: Path) -> None:
    """Fail case: justfile.jinja renders to an unparseable justfile; check rejects.

    All required output files exist and the JSON parses, but the
    generated `justfile` is a plain (non-shebang) recipe whose
    indented `if` body `just` rejects ("Recipe line has extra leading
    whitespace") — the exact defect that broke the template's
    `bootstrap` recipe. The text-grep assertions never invoke `just`,
    so without the parse gate this slips through; the smoke check MUST
    surface the `copier-template-smoke-justfile-parse-failed`
    diagnostic and exit non-zero.
    """
    template_dir = tmp_path / "templates" / "impl-plugin"
    template_dir.mkdir(parents=True)
    (template_dir / "copier.yml").write_text(
        "_templates_suffix: .jinja\n_exclude:\n  - copier.yml\n",
        encoding="utf-8",
    )
    # Minimal stubs for every file in _EXPECTED_FILES so the missing-
    # output branch doesn't fire and the JSON parse passes; only the
    # justfile is malformed. The answers-file boilerplate renders to
    # `.copier-answers.yml` (copier's default `_answers_file`).
    (template_dir / "{{ _copier_conf.answers_file }}.jinja").write_text(
        "{{ _copier_answers|to_nice_yaml -}}\n", encoding="utf-8"
    )
    (template_dir / ".python-version.jinja").write_text("3.13\n", encoding="utf-8")
    (template_dir / ".mise.toml.jinja").write_text("[tools]\n", encoding="utf-8")
    (template_dir / "pyproject.toml.jinja").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    # Unparseable justfile: a PLAIN recipe whose `if` body is indented.
    # `just` runs each line of a plain recipe as its own command and
    # rejects the extra-indented continuation lines at parse time.
    (template_dir / "justfile.jinja").write_text(
        "bootstrap:\n    if true; then\n        echo hi\n    fi\n",
        encoding="utf-8",
    )
    (template_dir / "lefthook.yml.jinja").write_text(
        "pre-commit:\n  commands: {}\n", encoding="utf-8"
    )
    workflows = template_dir / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml.jinja").write_text("name: ci\n", encoding="utf-8")
    (workflows / "copier-update-drift.yml.jinja").write_text("name: drift\n", encoding="utf-8")
    plugin_dir = template_dir / ".claude-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "marketplace.json.jinja").write_text("{}\n", encoding="utf-8")
    (plugin_dir / "plugin.json.jinja").write_text("{}\n", encoding="utf-8")
    spec_dir = template_dir / "SPECIFICATION"
    spec_dir.mkdir()
    (spec_dir / "README.md.jinja").write_text("# README\n", encoding="utf-8")
    claude_dir = template_dir / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_COPIER_TEMPLATE_SMOKE)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"smoke check should reject an unparseable generated justfile; "
        f"got returncode={result.returncode} stderr={result.stderr!r}"
    )
    assert "copier-template-smoke-justfile-parse-failed" in result.stderr, (
        f"expected 'copier-template-smoke-justfile-parse-failed' check_id in stderr; "
        f"got stderr={result.stderr!r}"
    )


def test_expected_files_pin_generated_copier_answers_file() -> None:
    """`.copier-answers.yml` is pinned in the smoke check's expected output set.

    Regression guard (livespec-n9f0): the template ships the copier
    answers-file boilerplate (`{{ _copier_conf.answers_file }}.jinja`),
    so every generated tree — including the smoke check's local-path
    copy — carries a `.copier-answers.yml` recording the applied
    answers (and, for git-sourced copies, the `_commit` template
    version). Pinning membership in `_EXPECTED_FILES` makes the smoke
    check fail loudly if the boilerplate template is ever dropped,
    which would re-introduce the stuck-`_commit` re-sync defect
    (consumers regenerate files on `copier update` but never record
    the template version they synced to).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "copier_template_smoke_for_expected_files_test",
        str(_COPIER_TEMPLATE_SMOKE),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert ".copier-answers.yml" in module._EXPECTED_FILES  # noqa: SLF001
