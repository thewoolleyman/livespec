"""The git-environment scrub removes every repo-locating git variable and nothing else (fleet root fix).

A pytest run inside a commit hook in a linked worktree inherits the hook's GIT_DIR
and GIT_INDEX_FILE. This tests the scrub directly and in-process: no git and no
child process runs, so it asserts the environment, not the outer repository.
"""

from __future__ import annotations

import os

import pytest

from tests.conftest import GIT_ENV_PASSTHROUGH_VARS, scrub_git_env

_REPO_LOCATING = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
)


@pytest.mark.parametrize("variable", _REPO_LOCATING)
def test_every_repo_locating_git_variable_is_in_the_scrub_list(variable: str) -> None:
    assert variable in GIT_ENV_PASSTHROUGH_VARS


def test_the_scrub_removes_inherited_repo_locating_variables_and_keeps_the_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in _REPO_LOCATING:
        monkeypatch.setenv(variable, f"/outer/{variable}")
    monkeypatch.setenv("LIVESPEC_SCRUB_SENTINEL", "kept")
    scrub_git_env(monkeypatch)
    assert not [variable for variable in _REPO_LOCATING if variable in os.environ]
    assert os.environ["LIVESPEC_SCRUB_SENTINEL"] == "kept"
