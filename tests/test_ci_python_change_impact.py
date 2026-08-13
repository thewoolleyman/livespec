"""Regression coverage for Python-validation change impact classification."""

from __future__ import annotations

from pathlib import Path

import pytest

_CI_WORKFLOW_PATH = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"


def _workflow_text() -> str:
    return _CI_WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("changed_path", "selector"),
    [
        (
            ".claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json",
            ".claude-plugin/scripts/_vendor/*",
        ),
        ("pyproject.toml", "pyproject.toml"),
        ("uv.lock", "uv.lock"),
        (".vendor.jsonc", ".vendor.jsonc"),
    ],
)
def test_dependency_and_vendored_runtime_inputs_require_python_validation(
    changed_path: str,
    selector: str,
) -> None:
    workflow = _workflow_text()

    assert selector in workflow, changed_path


def test_documentation_only_change_skips_python_validation() -> None:
    workflow = _workflow_text()

    assert "py_changed=false" in workflow
    assert "*.py|pyproject.toml|uv.lock|.vendor.jsonc|.claude-plugin/scripts/_vendor/*" in workflow


def test_unavailable_changeset_fails_closed() -> None:
    workflow = _workflow_text()

    assert 'if ! changeset=$(git diff --name-only "origin/${BASE_REF}...HEAD"); then' in workflow
    assert 'echo "py_changed=true" >> "$GITHUB_OUTPUT"' in workflow
