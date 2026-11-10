"""Rule test for the hold-label disarm workflow and the arming workflow it pairs with.

Asserts the behaviour `SPECIFICATION/non-functional-requirements.md` states for
`disarm-on-hold-label.yml` in its copier-template workflow list, and the facts the
hold-label error-path scenario in `SPECIFICATION/scenarios.md` rests on:

- the disarm workflow triggers on `pull_request` `labeled` only, acts only on
  `do-not-merge` with a same-repository head, and only ever disarms;
- the arming workflow `auto-enable-merge.yml` re-arms on `unlabeled`, skips a
  pull request carrying `do-not-merge`, and has no `labeled` trigger;
- the orchestrator-plugin template ships the disarm workflow identical to
  livespec's own copy except for the App-token input key, which matches the
  template's own arming workflow (`app-id:`; livespec's copies use `client-id:`).
"""

from __future__ import annotations

import re
from pathlib import Path

__all__: list[str] = []

_ROOT = Path(__file__).resolve().parents[1]
_DISARM = _ROOT / ".github/workflows/disarm-on-hold-label.yml"
_ARM = _ROOT / ".github/workflows/auto-enable-merge.yml"
_TEMPLATE_DISARM = (
    _ROOT / "templates/orchestrator-plugin/.github/workflows/disarm-on-hold-label.yml.jinja"
)
_TEMPLATE_ARM = (
    _ROOT / "templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja"
)


def _pull_request_types(*, text: str) -> set[str]:
    """The activity types listed in the workflow's `on:` block (pull_request only)."""
    block = text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert block.splitlines()[0] == "  pull_request:", block
    return {line.strip()[2:] for line in block.splitlines() if line.strip().startswith("- ")}


def _render_escaped(*, text: str) -> str:
    """Render the template's escaped GitHub expressions to their literal form."""
    return text.replace("${{ '{{' }}", "${{").replace("{{ '}}' }}", "}}")


def test_disarm_workflow_triggers_on_labeled_only() -> None:
    assert _pull_request_types(text=_DISARM.read_text(encoding="utf-8")) == {"labeled"}


def test_disarm_workflow_acts_only_on_do_not_merge_with_same_repo_head() -> None:
    text = _DISARM.read_text(encoding="utf-8")
    assert "github.event.label.name == 'do-not-merge'" in text
    assert "github.event.pull_request.head.repo.full_name == github.repository" in text


def test_disarm_workflow_only_ever_disarms() -> None:
    code = "\n".join(
        line
        for line in _DISARM.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "disablePullRequestAutoMerge" in code
    assert "enablePullRequestAutoMerge" not in code
    assert re.search(r"gh pr merge\b", code) is None


def test_arming_workflow_rearms_on_unlabeled_and_has_no_labeled_trigger() -> None:
    for path in (_ARM, _TEMPLATE_ARM):
        text = _render_escaped(text=path.read_text(encoding="utf-8"))
        types = _pull_request_types(text=text)
        assert "unlabeled" in types, path
        assert "labeled" not in types, path
        assert "!contains(github.event.pull_request.labels.*.name, 'do-not-merge')" in text, path


def _token_input_key(*, text: str) -> str:
    match = re.search(r"^\s+(app-id|client-id): \$\{\{ secrets\.APP_ID \}\}$", text, re.MULTILINE)
    assert match is not None, "no App-token input reads secrets.APP_ID"
    return match.group(1)


def test_template_ships_disarm_workflow_matching_livespec_copy_and_its_arming_auth() -> None:
    rendered = _render_escaped(text=_TEMPLATE_DISARM.read_text(encoding="utf-8"))
    template_arm = _render_escaped(text=_TEMPLATE_ARM.read_text(encoding="utf-8"))
    key = _token_input_key(text=template_arm)
    assert _token_input_key(text=rendered) == key
    livespec_copy = _DISARM.read_text(encoding="utf-8")
    livespec_key = _token_input_key(text=livespec_copy)
    assert rendered == livespec_copy.replace(
        f"{livespec_key}: ${{{{ secrets.APP_ID }}}}", f"{key}: ${{{{ secrets.APP_ID }}}}"
    )
