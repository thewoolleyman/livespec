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
    # trivial; only marketplace.json is malformed.
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
