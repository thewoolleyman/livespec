"""Rule test: CI reads a PR's body and head without the REST pulls endpoint.

`GET repos/<repo>/pulls/<n>` computes diff stats and answers a transient 422
"too many files changed" right after a force-push. The incident-ci select step
needs only the body, so it reads `issues/<n>`; the incident label workflow needs
only the head sha, so it reads GraphQL `headRefOid` and fails closed when empty.
"""

from __future__ import annotations

from pathlib import Path

__all__: list[str] = []

_ROOT = Path(__file__).resolve().parents[1]
_CI = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
_LABEL = (_ROOT / ".github/workflows/incident-label-ci.yml").read_text(encoding="utf-8")


def test_ci_select_step_reads_the_pr_body_from_the_issues_endpoint() -> None:
    assert 'gh api "repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}" --jq \'.body // ""\'' in _CI
    assert "pulls/${PR_NUMBER}" not in _CI


def test_label_workflow_reads_the_head_through_graphql_and_fails_closed() -> None:
    assert "pullRequest(number:$n){headRefOid}" in _LABEL
    assert ".data.repository.pullRequest.headRefOid // empty" in _LABEL
    assert 'test -n "$head"' in _LABEL
    assert "pulls/${PR_NUMBER}" not in _LABEL
