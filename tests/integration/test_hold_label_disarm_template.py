"""Integration test for the hold-label disarm workflow a template-born consumer receives.

Exercises the `SPECIFICATION/scenarios.md` hold-label error-path scenario across the
real seams it names: the orchestrator-plugin copier template is rendered in-process
by copier into a fresh consumer tree under `tmp_path`, and the generated
`disarm-on-hold-label.yml` and `auto-enable-merge.yml` are read back from that tree.

- The disarm workflow triggers on `pull_request` `labeled` only, acts only on
  `do-not-merge` with a same-repository head, and only ever disarms.
- The arming workflow re-arms on `unlabeled`, skips a `do-not-merge` pull request,
  and has no `labeled` trigger.
- Both mint from the same App-token input key, so the disarm workflow authenticates
  exactly as the arming workflow it pairs with.
"""

from __future__ import annotations

import re
from pathlib import Path

import copier
import pytest

__all__: list[str] = []

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_ROOT = _REPO_ROOT / "templates" / "orchestrator-plugin"
_ANSWERS = {
    "plugin_short_name": "smoketest",
    "plugin_full_name": "livespec-impl-smoketest",
    "plugin_description": "Smoke-test fixture plugin",
    "plugin_namespace": "livespec-impl-smoketest",
    "author_name": "Smoke Test",
    "author_email": "smoke@example.invalid",
    "github_owner": "thewoolleyman",
    "github_repo": "livespec-impl-smoketest",
    "python_version": "3.13",
    "livespec_release_tag": "v0.1.0",
}


def _pull_request_types(*, text: str) -> set[str]:
    """The activity types listed in the workflow's `on:` block (pull_request only)."""
    block = text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert block.splitlines()[0] == "  pull_request:", block
    return {line.strip()[2:] for line in block.splitlines() if line.strip().startswith("- ")}


def _token_input_key(*, text: str) -> str:
    match = re.search(r"^\s+(app-id|client-id): \$\{\{ secrets\.APP_ID \}\}$", text, re.MULTILINE)
    assert match is not None, "no App-token input reads secrets.APP_ID"
    return match.group(1)


def _code_lines(*, text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def test_template_born_consumer_receives_a_disarm_only_hold_label_workflow(
    *, tmp_path: Path
) -> None:
    target = tmp_path / "rendered"
    copier.run_copy(
        str(_TEMPLATE_ROOT),
        str(target),
        data=_ANSWERS,
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
        quiet=True,
    )
    disarm = (target / ".github/workflows/disarm-on-hold-label.yml").read_text(encoding="utf-8")
    arm = (target / ".github/workflows/auto-enable-merge.yml").read_text(encoding="utf-8")

    assert _pull_request_types(text=disarm) == {"labeled"}
    assert "github.event.label.name == 'do-not-merge'" in disarm
    assert "github.event.pull_request.head.repo.full_name == github.repository" in disarm
    disarm_code = _code_lines(text=disarm)
    assert "disablePullRequestAutoMerge" in disarm_code
    assert "enablePullRequestAutoMerge" not in disarm_code
    assert re.search(r"gh pr merge\b", disarm_code) is None

    arm_types = _pull_request_types(text=arm)
    assert "unlabeled" in arm_types
    assert "labeled" not in arm_types
    assert "!contains(github.event.pull_request.labels.*.name, 'do-not-merge')" in arm

    assert _token_input_key(text=disarm) == _token_input_key(text=arm)
