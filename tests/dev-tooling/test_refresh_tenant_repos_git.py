"""Tests for `dev-tooling/refresh_tenant_repos_git.py` — git identity/cleanliness/currency.

Every case runs against REAL temporary git repositories: a bare repo
standing in for `origin` (so clone, fetch, and push resolve with no
network) plus real clones, linked worktrees, and nested directories.

Each clone's `origin` is set to the `https://github.com/<owner>/<repo>`
URL the identity check demands, and a per-test `GIT_CONFIG_GLOBAL`
carries a `url.<remotes>/.insteadOf = https://github.com/` rewrite so
that URL resolves to the local bare repo. That is what lets the suite
exercise the real host check — which rejects a filesystem `origin`
outright — without reaching GitHub.

Two cases need to see what git was ASKED, not only what it produced, so
they put a recording stand-in first on `PATH`: a fake `gh` that answers
`auth git-credential` with a known username and password, and a `git`
shim that logs its argv and then `exec`s the real git. Both are
deliberately installed AFTER the fixtures are built, so the only
invocations they record are the module's own.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_git.py"
_OWNER = "acme"
_REPO = "widget"
_URL = f"https://github.com/{_OWNER}/{_REPO}"
_ACCEPTED = (_URL,)
# Every marker an interrupted git operation leaves in the git directory.
# `rebase-apply` and `rebase-merge` are DIRECTORIES in a real repository
# — the two rebase backends — while the other four are files, so each
# fixture below is created in the shape git itself would leave.
_IN_PROGRESS_MARKERS = (
    "BISECT_LOG",
    "CHERRY_PICK_HEAD",
    "MERGE_HEAD",
    "REVERT_HEAD",
    "rebase-apply",
    "rebase-merge",
)
_DIRECTORY_MARKERS = frozenset({"rebase-apply", "rebase-merge"})

# A `gh` that answers the one credential request git makes of it, and
# records every argv it was handed so a test can prove it WAS consulted.
_FAKE_GH = """#!/usr/bin/env bash
set -uo pipefail
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
if [[ "${1:-} ${2:-}" == "auth git-credential" ]]; then
    cat >/dev/null
    printf 'username=fake-user\\npassword=fake-token\\n'
    exit 0
fi
exit 99
"""

# A `git` that logs its argv and then becomes the real git, so a test
# can assert the SHAPE of an invocation while the invocation still
# really runs. Arguments are separated by US (0x1f) rather than spaces,
# so an argument containing a space is still one field.
_RECORDING_GIT = """#!/usr/bin/env bash
printf '%s\\x1f' "$@" >> "$GIT_ARGV_LOG"
printf '\\n' >> "$GIT_ARGV_LOG"
exec "$REAL_GIT" "$@"
"""


def _load_module() -> ModuleType:
    """Import the git helper by file path (`dev-tooling/` is not a package)."""
    sys.path.insert(0, str(_REPO_ROOT / "dev-tooling"))
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_git", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(*, cwd: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def _route_github_locally(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every `https://github.com/` URL resolve to `<tmp>/remotes/`."""
    config = tmp_path / "gitconfig"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    remotes = tmp_path / "remotes"
    remotes.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(config),
            f"url.{remotes}/.insteadOf",
            "https://github.com/",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _origin(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repo: str = _REPO) -> Path:
    """A bare `origin` at `<tmp>/remotes/<owner>/<repo>` holding one commit."""
    _route_github_locally(tmp_path=tmp_path, monkeypatch=monkeypatch)
    origin = tmp_path / "remotes" / _OWNER / repo
    origin.parent.mkdir(parents=True, exist_ok=True)
    _git(cwd=tmp_path, args=["init", "--bare", "-q", "-b", "master", str(origin)])
    seed = tmp_path / f"seed-{repo}"
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(seed)])
    _identify(repo=seed)
    _git(cwd=seed, args=["commit", "-q", "--allow-empty", "-m", "init"])
    _git(cwd=seed, args=["push", "-q", "origin", "master"])
    return origin


def _identify(*, repo: Path) -> None:
    _git(cwd=repo, args=["config", "user.email", "t@example.com"])
    _git(cwd=repo, args=["config", "user.name", "Test"])


def _clone(*, tmp_path: Path, origin: Path, name: str, slug: str = f"{_OWNER}/{_REPO}") -> Path:
    """A clone of `origin` at `<tmp>/<name>` whose `origin` is the github.com URL."""
    dest = tmp_path / name
    _git(cwd=tmp_path, args=["clone", "-q", str(origin), str(dest)])
    _git(cwd=dest, args=["remote", "set-url", "origin", f"https://github.com/{slug}"])
    _identify(repo=dest)
    return dest


def _commit(*, repo: Path, name: str) -> None:
    (repo / name).write_text(name, encoding="utf-8")
    _git(cwd=repo, args=["add", name])
    _git(cwd=repo, args=["commit", "-q", "-m", f"add {name}"])


def _executable(*, path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _install_fake_gh(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put the recording fake `gh` first on PATH; return its argv log path."""
    _executable(path=tmp_path / "bin" / "gh", body=_FAKE_GH)
    log = tmp_path / "gh-argv.log"
    log.write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_LOG", str(log))
    return log


def _install_recording_git(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put the argv-logging `git` shim first on PATH; return its log path.

    The real git is resolved BEFORE the shim is installed, so the shim
    execs git rather than itself.
    """
    real_git = shutil.which("git")
    assert real_git is not None
    log = tmp_path / "git-argv.log"
    log.write_text("", encoding="utf-8")
    _executable(path=tmp_path / "bin" / "git", body=_RECORDING_GIT)
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("REAL_GIT", real_git)
    monkeypatch.setenv("GIT_ARGV_LOG", str(log))
    return log


def _recorded_argvs(*, log: Path) -> list[list[str]]:
    """Every invocation the `git` shim recorded, as its argument list.

    `$0` is not part of `"$@"`, so each list starts at the first argument
    after the program name — which is where the credential options sit.
    """
    lines = log.read_text(encoding="utf-8").splitlines()
    return [line.split("\x1f")[:-1] for line in lines if line]


def test_primary_checkout_resolves_the_same_path_from_a_linked_worktree(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    primary = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    worktree = tmp_path / "linked"
    _git(cwd=primary, args=["worktree", "add", "-q", str(worktree), "-b", "side"])

    assert module.primary_checkout(project_root=primary) == primary
    assert module.primary_checkout(project_root=worktree) == primary


def test_primary_checkout_is_none_outside_a_git_repository(*, tmp_path: Path) -> None:
    module = _load_module()
    plain = tmp_path / "plain"
    plain.mkdir()

    assert module.primary_checkout(project_root=plain) is None


def test_a_clean_clone_of_an_accepted_repo_has_no_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.identity_problem(dest=dest, accepted_urls=_ACCEPTED) is None
    # The same repository named with a `.git` suffix is the same repository.
    assert module.identity_problem(dest=dest, accepted_urls=(f"{_URL}.git",)) is None


def test_a_clone_carrying_the_canonical_post_transfer_url_is_accepted(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A transferred repo's clone names the CANONICAL pair, not the registered one.

    Accepting only the registered URL is what made every host preserve
    `homelab` after it moved to `mi-homelab`.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO, slug="mi-homelab/homelab")
    accepted = (_URL, "https://github.com/mi-homelab/homelab")

    assert module.identity_problem(dest=dest, accepted_urls=accepted) is None


def test_a_symlink_destination_is_an_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    real = _clone(tmp_path=tmp_path, origin=origin, name="real")
    link = tmp_path / _REPO
    link.symlink_to(real, target_is_directory=True)

    problem = module.identity_problem(dest=link, accepted_urls=_ACCEPTED)

    assert problem == "destination is a symlink"


def test_a_non_directory_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    plain_file = tmp_path / _REPO
    plain_file.write_text("not a repo", encoding="utf-8")

    problem = module.identity_problem(dest=plain_file, accepted_urls=_ACCEPTED)

    assert problem == "destination exists but is not a directory"


def test_a_non_repository_destination_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    plain_dir = tmp_path / _REPO
    plain_dir.mkdir()

    problem = module.identity_problem(dest=plain_dir, accepted_urls=_ACCEPTED)

    assert problem == "destination is not a git repository"


def test_a_directory_nested_inside_another_repository_is_an_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    outer = _clone(tmp_path=tmp_path, origin=origin, name="outer")
    nested = outer / _REPO
    nested.mkdir()

    problem = module.identity_problem(dest=nested, accepted_urls=_ACCEPTED)

    assert problem is not None
    assert problem.startswith("destination is nested inside the repository at")


def test_a_linked_worktree_destination_is_an_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    primary = _clone(tmp_path=tmp_path, origin=origin, name="primary")
    worktree = tmp_path / _REPO
    _git(cwd=primary, args=["worktree", "add", "-q", str(worktree), "-b", "side"])

    problem = module.identity_problem(dest=worktree, accepted_urls=_ACCEPTED)

    assert problem == "destination is a linked worktree, not a primary checkout"


def test_a_destination_without_an_origin_remote_is_an_identity_problem(*, tmp_path: Path) -> None:
    module = _load_module()
    standalone = tmp_path / _REPO
    standalone.mkdir()
    _git(cwd=standalone, args=["init", "-q", "-b", "master"])

    problem = module.identity_problem(dest=standalone, accepted_urls=_ACCEPTED)

    assert problem == "destination has no `origin` remote"


def test_a_clone_of_a_different_github_repo_is_an_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    problem = module.identity_problem(dest=dest, accepted_urls=("https://github.com/acme/other",))

    assert problem is not None
    assert problem.endswith("which names none of: https://github.com/acme/other")


@pytest.mark.parametrize(
    "origin_url",
    [
        # A filesystem remote whose tail matches the declared repo exactly.
        "/srv/mirrors/acme/widget",
        # Another forge.
        "https://gitlab.com/acme/widget",
        "git@gitlab.com:acme/widget.git",
        # github.com reached over a different SCHEME.
        "file://github.com/acme/widget",
        # An EXTRA path segment — the last two still read `acme/widget`.
        "https://github.com/extra/acme/widget",
        # Userinfo and a port are not forms git writes for a GitHub remote.
        "https://token@github.com/acme/widget",
        "ssh://git@github.com:22/acme/widget.git",
    ],
)
def test_an_origin_that_is_not_an_exact_github_remote_is_an_identity_problem(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, origin_url: str
) -> None:
    """Recognition is an allowlist, so each of these preserves the repository.

    Every URL here carries the `acme/widget` tail a tail-only comparison
    accepts, and every one of them names something else.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    _git(cwd=dest, args=["remote", "set-url", "origin", origin_url])

    problem = module.identity_problem(dest=dest, accepted_urls=_ACCEPTED)

    assert problem is not None
    assert problem.endswith("which is not a https://github.com/<owner>/<repo> remote")


def test_sweep_ds_store_deletes_only_untracked_regular_droppings(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    # A TRACKED .DS_Store, modified — never a candidate, because a
    # tracked file never appears in the untracked set.
    tracked = dest / "tracked"
    tracked.mkdir()
    (tracked / ".DS_Store").write_text("tracked", encoding="utf-8")
    _git(cwd=dest, args=["add", "tracked/.DS_Store"])
    _git(cwd=dest, args=["commit", "-q", "-m", "track a .DS_Store"])
    (tracked / ".DS_Store").write_text("modified", encoding="utf-8")
    # An untracked SYMLINK named .DS_Store — left in place.
    linked = dest / "linked"
    linked.mkdir()
    (linked / ".DS_Store").symlink_to(tracked / ".DS_Store")
    # An untracked file with another name — left in place.
    (dest / "notes.txt").write_text("keep me", encoding="utf-8")
    # The actual droppings.
    (dest / ".DS_Store").write_text("finder", encoding="utf-8")
    (dest / "sub").mkdir()
    (dest / "sub" / ".DS_Store").write_text("finder", encoding="utf-8")

    status = module.porcelain_status(repo=dest)
    swept = module.sweep_ds_store(repo=dest, status_lines=status.values)

    assert sorted(swept.removed) == [".DS_Store", "sub/.DS_Store"]
    assert len(swept.remaining) == 3
    assert not (dest / ".DS_Store").exists()
    assert not (dest / "sub" / ".DS_Store").exists()
    assert (linked / ".DS_Store").is_symlink()
    assert (tracked / ".DS_Store").read_text(encoding="utf-8") == "modified"
    assert (dest / "notes.txt").exists()


def test_porcelain_status_is_empty_for_a_clean_clone(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    status = module.porcelain_status(repo=dest)

    assert status.problem is None
    assert status.values == ()
    assert module.sweep_ds_store(repo=dest, status_lines=status.values).removed == ()


def test_porcelain_status_reports_an_inspection_failure_rather_than_a_clean_tree(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable index must never answer "clean" — that answer refreshes it.

    Replacing `.git/index` with a DIRECTORY is a state `git status`
    cannot read while `rev-parse` still succeeds, so the repo passes the
    placement checks and the status probe is the one that fails.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    (dest / ".git" / "index").unlink()
    (dest / ".git" / "index").mkdir()

    status = module.porcelain_status(repo=dest)

    assert status.values == ()
    assert status.problem is not None
    assert status.problem.startswith("git inspection `git status --porcelain")


@pytest.mark.parametrize("marker", _IN_PROGRESS_MARKERS)
def test_in_progress_operation_reports_an_interrupted_operation(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, marker: str
) -> None:
    """All six markers, each in a real clone and in the shape git leaves it.

    Covering only some of them would leave the rest free to be dropped
    from the probe without a single case going red, and every one of them
    means the repository holds operator state a refresh would strand.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.in_progress_operation(repo=dest).values == ()

    if marker in _DIRECTORY_MARKERS:
        (dest / ".git" / marker).mkdir()
    else:
        (dest / ".git" / marker).write_text("", encoding="utf-8")

    assert module.in_progress_operation(repo=dest).values == (marker,)


def test_in_progress_operation_reports_an_inspection_failure_not_an_all_clear(
    *, tmp_path: Path
) -> None:
    """Without a git directory the markers cannot be looked for at all."""
    module = _load_module()
    plain = tmp_path / "plain"
    plain.mkdir()

    facts = module.in_progress_operation(repo=plain)

    assert facts.values == ()
    assert facts.problem is not None
    assert facts.problem.startswith("git inspection `git rev-parse --absolute-git-dir` failed")


def test_unpushed_count_counts_commits_absent_from_every_origin_ref(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    assert module.unpushed_count(repo=dest).count == 0

    _git(cwd=dest, args=["switch", "-q", "-c", "feature"])
    _commit(repo=dest, name="local-only")

    facts = module.unpushed_count(repo=dest)

    assert facts.problem is None
    assert facts.count == 1


def test_unpushed_count_reports_an_inspection_failure_rather_than_zero(*, tmp_path: Path) -> None:
    """An unborn HEAD cannot be walked, and zero would read as "nothing unpushed"."""
    module = _load_module()
    empty = tmp_path / "empty"
    empty.mkdir()
    _git(cwd=empty, args=["init", "-q", "-b", "master"])

    facts = module.unpushed_count(repo=empty)

    assert facts.count == 0
    assert facts.problem is not None
    assert facts.problem.startswith("git inspection `git rev-list --count HEAD")


def test_default_branch_ahead_distinguishes_behind_from_ahead(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    # A local branch that does not exist is ahead of nothing.
    absent = module.default_branch_ahead(repo=dest, default_branch="absent")
    assert absent.problem is None
    assert absent.count == 0
    assert module.default_branch_ahead(repo=dest, default_branch="master").count == 0

    _commit(repo=dest, name="local-ahead")

    assert module.default_branch_ahead(repo=dest, default_branch="master").count == 1


def test_default_branch_ahead_reports_a_failed_ref_probe_as_an_inspection_failure(
    *, tmp_path: Path
) -> None:
    """Only exit 1 means "the ref is absent"; 128 means the probe could not look.

    Reading every non-zero exit as absence answers "ahead of nothing",
    which refreshes a repository the probe never managed to inspect.
    """
    module = _load_module()
    plain = tmp_path / "plain"
    plain.mkdir()

    facts = module.default_branch_ahead(repo=plain, default_branch="master")

    assert facts.count == 0
    assert facts.problem is not None
    assert facts.problem.startswith("git inspection `git rev-parse --verify --quiet")


def test_default_branch_ahead_reports_a_failed_walk_as_an_inspection_failure(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A local branch with no `origin/<branch>` counterpart cannot be compared."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    _git(cwd=dest, args=["switch", "-q", "-c", "trunk"])

    facts = module.default_branch_ahead(repo=dest, default_branch="trunk")

    assert facts.count == 0
    assert facts.problem is not None
    assert facts.problem.startswith("git inspection `git rev-list --count --left-right")


def test_the_credential_options_make_git_authenticate_through_gh(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asking git itself to fill a github.com credential really does reach `gh`.

    Every other case in this file resolves to a LOCAL bare repo, which
    never asks for a credential — so the credential options could be
    deleted outright and the whole suite would stay green. This is the one
    case that proves what they are FOR: `git credential fill` is run with
    the module's own options for protocol https and host github.com, the
    fake `gh` records that `auth git-credential` was the subcommand it was
    asked for, and the username and password git reports are the ones that
    fake answered with.
    """
    module = _load_module()

    assert "GH_CREDENTIAL_ARGS" in module.__all__

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    (tmp_path / "gitconfig").write_text("", encoding="utf-8")
    # No helper may fall back to a terminal: an unanswered prompt would
    # make this case hang rather than fail.
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    filled = subprocess.run(
        ["git", *module.GH_CREDENTIAL_ARGS, "credential", "fill"],
        input=f"protocol=https\nhost={module.GITHUB_HOST}\n\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert filled.returncode == 0, filled.stderr
    assert log.read_text(encoding="utf-8").splitlines() == ["auth git-credential get"]
    assert "username=fake-user" in filled.stdout
    assert "password=fake-token" in filled.stdout


def test_the_clone_and_the_fetch_pass_the_credential_options_before_the_subcommand(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Placement is the contract, and only the argv shows it.

    `git clone -c <key>=<value>` writes the setting into the NEW
    repository's config; `git -c <key>=<value> clone` applies it to the
    one invocation and writes nothing. Both operations therefore have to
    hand the options to GIT ITSELF — immediately before the subcommand —
    and both really run here, against the local bare repo, through a
    `git` that logs what it was asked before becoming the real one.
    """
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    log = _install_recording_git(tmp_path=tmp_path, monkeypatch=monkeypatch)

    assert module.clone_https(url=_URL, dest=tmp_path / "fresh") is None
    assert module.fetch_https(repo=dest, url=_URL) is None

    options = list(module.GH_CREDENTIAL_ARGS)
    recorded = {
        subcommand: argv
        for argv in _recorded_argvs(log=log)
        for subcommand in ("clone", "fetch")
        if subcommand in argv
    }
    assert sorted(recorded) == ["clone", "fetch"]
    for subcommand, argv in recorded.items():
        at = argv.index(subcommand)
        assert argv[at - len(options) : at] == options


def test_clone_https_clones_over_https_and_persists_no_credential_helper(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clone addresses the canonical HTTPS URL, so `origin` is already HTTPS.

    `gh repo clone <owner>/<repo>` would pick its protocol from gh's own
    `git_protocol` setting — `ssh` on the maintainer's Mac — which both
    needs separate SSH auth and leaves `origin` as an SSH URL the next
    fetch has to work around. And because the credential options are
    passed to git rather than to `clone`, the new repository's config
    carries no helper.
    """
    module = _load_module()
    _ = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = tmp_path / "fresh"

    assert module.clone_https(url=_URL, dest=dest) is None

    config = (dest / ".git" / "config").read_text(encoding="utf-8")
    assert f"url = {_URL}" in config
    assert "credential" not in config


def test_clone_https_reports_an_unreachable_url(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _route_github_locally(tmp_path=tmp_path, monkeypatch=monkeypatch)

    problem = module.clone_https(url=f"{_URL}-absent", dest=tmp_path / "nope")

    assert problem is not None
    assert problem.startswith(f"`git clone {_URL}-absent` failed:")


def test_fetch_https_updates_remote_tracking_refs_and_leaves_config_unchanged(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An SSH `origin` still fetches over HTTPS, and nothing is written to config."""
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    _git(cwd=dest, args=["remote", "set-url", "origin", f"git@github.com:{_OWNER}/{_REPO}.git"])
    before = (dest / ".git" / "config").read_text(encoding="utf-8")
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])

    assert module.fetch_https(repo=dest, url=_URL) is None

    behind = module.run_git(
        repo=dest, args=["rev-list", "--count", "master..refs/remotes/origin/master"]
    )
    assert behind.stdout.strip() == "1"
    assert (dest / ".git" / "config").read_text(encoding="utf-8") == before


def test_fetch_https_reports_an_unreachable_url(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    problem = module.fetch_https(repo=dest, url=f"{_URL}-absent")

    assert problem is not None
    assert problem.startswith(f"`git fetch --prune {_URL}-absent` failed:")


def test_fast_forward_switches_to_the_default_branch_and_advances_it(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])
    _git(cwd=dest, args=["switch", "-q", "-c", "parked"])
    assert module.fetch_https(repo=dest, url=_URL) is None

    assert module.fast_forward(repo=dest, default_branch="master") is None

    branch = module.run_git(repo=dest, args=["rev-parse", "--abbrev-ref", "HEAD"])
    assert branch.stdout.strip() == "master"
    assert (dest / "pushed").is_file()


def test_fast_forward_reports_a_branch_it_cannot_switch_to(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)

    problem = module.fast_forward(repo=dest, default_branch="no-such-branch")

    assert problem is not None
    assert problem.startswith("`git switch no-such-branch` failed:")


def test_fast_forward_refuses_a_non_fast_forward(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    origin = _origin(tmp_path=tmp_path, monkeypatch=monkeypatch)
    dest = _clone(tmp_path=tmp_path, origin=origin, name=_REPO)
    other = _clone(tmp_path=tmp_path, origin=origin, name="other")
    _commit(repo=other, name="pushed")
    _git(cwd=other, args=["push", "-q", "origin", "master"])
    _commit(repo=dest, name="diverged")
    assert module.fetch_https(repo=dest, url=_URL) is None

    problem = module.fast_forward(repo=dest, default_branch="master")

    assert problem is not None
    assert problem.startswith("`git merge --ff-only origin/master` failed:")
