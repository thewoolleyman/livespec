"""Tests for livespec.doctor.static.wiring_completeness_cross_repo.

Per `SPECIFICATION/contracts.md` §"Shared code sync —
livespec-dev-tooling" → "Cross-repo backstop" + §"Doctor
cross-boundary invariants":

  A doctor invariant `wiring-completeness-cross-repo` MUST walk
  every registered sibling repo, read its `justfile`'s `check`
  recipe, compute the canonical-set difference, and fire `fail`
  on any aggregate lacking any canonical slug. The check MAY use
  a sibling's `local_clone` path when configured or fall back to
  a GitHub query against the sibling's default-branch
  `justfile`.

Tests cover:

  - All siblings wire the full canonical set → `pass`.
  - One sibling missing one slug → `fail` + finding lists the
    (sibling, slug) pair.
  - Multiple siblings each missing slugs → `fail` + every pair
    in the finding's message.
  - `local_clone` path resolution: justfile read from the local
    clone via `git -C <local_clone> show HEAD:justfile` (NOT a
    filesystem read — the family-wide bare-flag invariant on
    primary checkouts makes the working tree intentionally
    stale, so the git db is the canonical source).
  - `local_clone` path exists but isn't a git repository →
    graceful fall-through to GitHub Path B.
  - `local_clone` exists as a git repo but `justfile` was never
    committed at HEAD → graceful fall-through to GitHub Path B.
  - Bare clone (`git init --bare` + commit pushed from a
    working clone) → Path A reads the justfile via
    `git show HEAD:` correctly. This is the bare-flag invariant
    compatibility test.
  - GitHub-fallback path: `gh api` mocked via monkeypatching
    `livespec.io.proc.run_subprocess`.
  - Sibling has no justfile at the local clone AND GitHub
    fallback returns empty → `fail` with `:no-justfile-resolved`
    placeholder.
  - Sibling justfile has no `check:` recipe → `fail` with
    `:no-check-recipe` placeholder.
  - `cross_repo_targets` block absent → `skipped`.
  - Host repo (local_clone == project_root) auto-excluded;
    when manifest has only the host, the result is `skipped`.
  - .livespec.jsonc absent → `skipped`.
  - .livespec.jsonc malformed → `skipped`.

The tests use a real `git init`'d directory (`tmp_path`) for
the local-clone side — the Path A code reads via
`git -C <clone> show HEAD:justfile`, so the justfile MUST be
committed into the fixture repo, not just written into the
working tree. For the GitHub-fallback path, monkeypatching
`livespec.io.proc.run_subprocess` substitutes a fake that
dispatches by argv shape: a `git`-prefixed argv is forwarded
to the real subprocess (so the Path A code still drives the
real `git show HEAD:justfile` against the fixture clone), while
a `gh`-prefixed argv is matched against the `(owner, name)`
response map. Real `gh` CLI is never invoked.
"""

from __future__ import annotations

import base64
import builtins
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import wiring_completeness_cross_repo
from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    CLONES_ROOT_ENV_VAR,
    resolve_effective_local_clone,
)
from livespec.io import proc as io_proc
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOResult, IOSuccess

__all__: list[str] = []


@pytest.fixture(autouse=True)
def _scrub_clones_root_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run with no inherited `LIVESPEC_SIBLING_CLONES_ROOT`.

    The cross-repo wiring check honors the env var override at the
    helper layer; tests that want the override active opt in via
    `monkeypatch.setenv(CLONES_ROOT_ENV_VAR, ...)` explicitly. Other
    tests use the manifest's `local_clone` paths against tmp_path
    fixtures — a leaked env var would redirect those reads to
    `<env-value>/<sibling-slug>` (a nonexistent path) and silently
    fall through to Path B, breaking every fixture-driven assertion.
    """
    monkeypatch.delenv(CLONES_ROOT_ENV_VAR, raising=False)


def _write_livespec_jsonc(
    *,
    project_root: Path,
    cross_repo_targets: dict[str, Any] | None,
) -> None:
    """Write a `.livespec.jsonc` carrying the given `cross_repo_targets` block.

    A `None` value writes a config with NO `cross_repo_targets`
    key (used by the skipped-on-absence test).
    """
    config: dict[str, Any] = {
        "template": "livespec",
        "spec_root": "SPECIFICATION",
        "implementation": {"plugin": "livespec-orchestrator-git-jsonl"},
    }
    if cross_repo_targets is not None:
        config["cross_repo_targets"] = cross_repo_targets
    _ = (project_root / ".livespec.jsonc").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def _make_justfile_text(*, slugs: tuple[str, ...]) -> str:
    """Build a justfile text whose `check:` recipe wires the given slugs."""
    body_lines = "\n".join(f"        {slug}" for slug in slugs)
    return (
        "default:\n"
        "    @just --list\n"
        "\n"
        "check:\n"
        "    #!/usr/bin/env bash\n"
        "    set -uo pipefail\n"
        "    targets=(\n"
        f"{body_lines}\n"
        "    )\n"
        '    echo "all done"\n'
    )


def _setup_project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Create a project_root + spec_root pair under `tmp_path`."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    return project_root, spec_root


def _git_init_and_commit(*, clone: Path, justfile_text: str | None) -> None:
    """Initialize a git repo at `clone` and commit `justfile_text` if given.

    Required by the Path A invariant: `git -C <clone> show HEAD:justfile`
    reads from the git db, NOT from the working tree, so a fixture
    that merely `write_text`s a justfile would be invisible to the
    Path A code. This helper runs `git init`, `git add justfile`,
    and `git commit -m init` so the justfile is committed at HEAD
    and `git show HEAD:justfile` returns the expected content.

    `--quiet` suppresses git's status output so test logs stay clean.
    `-c user.name`/`user.email` are passed inline so the commit
    works without requiring any local or global git-config state on
    the test runner — and they do NOT pollute the developer's git
    config, since the `-c` form is per-invocation only.

    `justfile_text=None` initializes the repo but skips the commit
    — used for the "git repo exists but has no justfile at HEAD"
    failure-mode test.
    """
    _ = subprocess.run(["git", "init", "--quiet"], cwd=clone, check=True)
    if justfile_text is None:
        return
    _ = (clone / "justfile").write_text(justfile_text, encoding="utf-8")
    _ = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=t@t", "add", "justfile"],
        cwd=clone,
        check=True,
    )
    _ = subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=t@t",
            "commit",
            "--quiet",
            "-m",
            "init",
        ],
        cwd=clone,
        check=True,
    )


def _setup_sibling_clone(*, tmp_path: Path, slug: str, slugs: tuple[str, ...]) -> Path:
    """Create a `<tmp_path>/<slug>` sibling clone with a wired justfile committed.

    The justfile is committed at HEAD so the Path A code's
    `git -C <clone> show HEAD:justfile` returns the expected
    content — the working tree alone is invisible to Path A.
    """
    clone = tmp_path / slug
    clone.mkdir()
    _git_init_and_commit(clone=clone, justfile_text=_make_justfile_text(slugs=slugs))
    return clone


def _setup_sibling_clone_with_raw_justfile(
    *,
    tmp_path: Path,
    slug: str,
    justfile_text: str,
) -> Path:
    """Create a sibling clone and commit an arbitrary justfile text at HEAD.

    Sibling helper to `_setup_sibling_clone` for tests that need
    full control over the justfile body (malformed recipes, blank
    lines inside the targets array, missing `check:` recipe, etc.).
    """
    clone = tmp_path / slug
    clone.mkdir()
    _git_init_and_commit(clone=clone, justfile_text=justfile_text)
    return clone


def _get_canonical_slugs() -> tuple[str, ...]:
    """Read the canonical slug tuple from livespec_dev_tooling at test time."""
    from livespec_dev_tooling.canonical_checks import canonical_check_slugs

    return canonical_check_slugs()


def _completed(*, stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Build a fake CompletedProcess carrier for monkeypatched run_subprocess."""
    return subprocess.CompletedProcess(
        args=["fake"],
        returncode=returncode,
        stdout=stdout,
        stderr="",
    )


def _gh_contents_payload(*, justfile_text: str) -> str:
    """Build the stdout payload that `gh api contents/justfile` would emit.

    Returns a JSON object with a base64-encoded `content` field and
    `encoding: "base64"`, matching the live GitHub Contents API
    response shape.
    """
    encoded = base64.b64encode(justfile_text.encode("utf-8")).decode("ascii")
    return json.dumps({"content": encoded, "encoding": "base64"})


def _install_gh_fake(
    *,
    monkeypatch: pytest.MonkeyPatch,
    response_by_owner_name: dict[tuple[str, str], subprocess.CompletedProcess[str]],
) -> None:
    """Install a fake `livespec.io.proc.run_subprocess` for gh-api calls.

    The fake dispatches by argv shape:

      - argv[0] == "git": forward to the real `subprocess.run` so
        the Path A code drives the real `git -C <clone> show
        HEAD:justfile` against the fixture clone (which a sibling
        test has populated with `_git_init_and_commit`). Path A's
        non-zero exit cases (no `.git`, no `justfile` at HEAD)
        still surface through the real git binary's exit code,
        and the wiring_completeness_cross_repo code folds them
        into a Path-B fall-through correctly.
      - argv[0] == "gh": match argv[2] (the
        `repos/<owner>/<name>/contents/justfile` segment) against
        `response_by_owner_name`. Unmatched entries return exit 1
        (the "gh api errored" path).

    This shape lets a single test exercise BOTH paths — Path A
    against a real fixture clone, Path B mocked.
    """

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], Any]:
        if argv[0] == "git":
            # Forward to the real binary; the Path A code's
            # `git -C <clone> show HEAD:justfile` is exercised
            # end-to-end against the fixture clone. Non-zero
            # exits surface in `completed.returncode` and the
            # check folds them into Path B fall-through.
            completed = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            return IOResult.from_value(completed)
        # The doctor's gh fallback always carries
        # `repos/<owner>/<name>/contents/justfile` as argv[2]
        # (after `gh api`); index directly rather than scanning,
        # which would create an else-branch the tests never
        # exercise.
        contents_arg = argv[2]
        segments = contents_arg.split("/")
        owner = segments[1]
        name = segments[2]
        if (owner, name) in response_by_owner_name:
            return IOResult.from_value(response_by_owner_name[(owner, name)])
        return IOResult.from_value(_completed(stdout="", returncode=1))

    monkeypatch.setattr(io_proc, "run_subprocess", fake_run_subprocess)


def test_passes_when_every_sibling_wires_full_canonical_set(
    *,
    tmp_path: Path,
) -> None:
    """`pass` when every registered sibling wires the full canonical set."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=canonical)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
                "default_branch": "master",
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_when_one_sibling_missing_one_slug(
    *,
    tmp_path: Path,
) -> None:
    """`fail` when one sibling drops one canonical slug."""
    canonical = _get_canonical_slugs()
    # Pick the first canonical slug to drop.
    dropped = canonical[0]
    remaining = tuple(s for s in canonical if s != dropped)
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=remaining)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
                "default_branch": "master",
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert f"sibling-a→{dropped}" in finding.message
    assert "1 (sibling, missing-canonical-slug) drift pair(s)" in finding.message


def test_fails_when_multiple_siblings_missing_slugs(
    *,
    tmp_path: Path,
) -> None:
    """`fail` aggregating every (sibling, missing-slug) pair across siblings."""
    canonical = _get_canonical_slugs()
    dropped_a = canonical[0]
    dropped_b = canonical[1]
    sibling_a_slugs = tuple(s for s in canonical if s != dropped_a)
    sibling_b_slugs = tuple(s for s in canonical if s != dropped_b)
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    clone_a = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=sibling_a_slugs)
    clone_b = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-b", slugs=sibling_b_slugs)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone_a),
            },
            "sibling-b": {
                "github_url": "https://github.com/example/sibling-b",
                "local_clone": str(clone_b),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert f"sibling-a→{dropped_a}" in finding.message
    assert f"sibling-b→{dropped_b}" in finding.message
    assert "2 (sibling, missing-canonical-slug) drift pair(s)" in finding.message


def test_github_fallback_path_used_when_local_clone_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`pass` via GitHub fallback when local_clone unset, gh api returns wired set."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "default_branch": "master",
            },
        },
    )
    justfile_text = _make_justfile_text(slugs=canonical)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=_gh_contents_payload(justfile_text=justfile_text)
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_github_fallback_used_when_local_clone_path_missing_on_disk(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GitHub fallback fires when local_clone set but path doesn't exist."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    nonexistent_clone = tmp_path / "missing-clone"
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(nonexistent_clone),
                "default_branch": "master",
            },
        },
    )
    justfile_text = _make_justfile_text(slugs=canonical)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=_gh_contents_payload(justfile_text=justfile_text)
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fails_with_no_justfile_resolved_when_both_paths_fail(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` with `:no-justfile-resolved` when local missing AND gh api errors."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "default_branch": "master",
            },
        },
    )
    # No entry in the response map → fake returns exit 1
    _install_gh_fake(monkeypatch=monkeypatch, response_by_owner_name={})

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_fails_with_no_check_recipe_when_justfile_lacks_check(
    *,
    tmp_path: Path,
) -> None:
    """`fail` with `:no-check-recipe` when justfile has no `check:` recipe."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    clone = _setup_sibling_clone_with_raw_justfile(
        tmp_path=tmp_path,
        slug="sibling-a",
        justfile_text="default:\n    @just --list\n",
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-check-recipe" in finding.message


def test_skipped_when_cross_repo_targets_block_absent(
    *,
    tmp_path: Path,
) -> None:
    """`skipped` when .livespec.jsonc carries no cross_repo_targets block."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(project_root=project_root, cross_repo_targets=None)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="skipped",
        message=(
            "wiring-completeness-cross-repo: project carries no "
            "`cross_repo_targets` block; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_host_repo_self_excluded_from_walk(
    *,
    tmp_path: Path,
) -> None:
    """A target whose local_clone resolves to project_root is auto-excluded.

    When the manifest contains ONLY the host repo, the result is
    `skipped` (no siblings remain to walk).
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "host": {
                "github_url": "https://github.com/example/host",
                "local_clone": str(project_root),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="skipped",
        message=(
            "wiring-completeness-cross-repo: cross_repo_targets "
            "contains no sibling entries (only the host repo or empty); "
            "no siblings to walk"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_host_repo_with_one_sibling_walks_only_the_sibling(
    *,
    tmp_path: Path,
) -> None:
    """When manifest has host + one sibling, only the sibling is walked."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=canonical)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "host": {
                "github_url": "https://github.com/example/host",
                "local_clone": str(project_root),
            },
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_livespec_jsonc_absent(
    *,
    tmp_path: Path,
) -> None:
    """`skipped` when .livespec.jsonc doesn't exist (precondition lash)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "skipped"
    assert "precondition not met" in finding.message


def test_skipped_when_livespec_jsonc_malformed(
    *,
    tmp_path: Path,
) -> None:
    """`skipped` when .livespec.jsonc is not valid JSON."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text("{ malformed json", encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "skipped"
    assert "precondition not met" in finding.message


def test_skipped_when_livespec_jsonc_root_is_not_object(
    *,
    tmp_path: Path,
) -> None:
    """`skipped` when .livespec.jsonc root is a JSON array, not an object."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _ = (project_root / ".livespec.jsonc").write_text("[1, 2, 3]", encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "skipped"
    assert ".livespec.jsonc root is not an object" in finding.message


def test_skipped_when_cross_repo_targets_is_not_a_dict(
    *,
    tmp_path: Path,
) -> None:
    """`skipped` when cross_repo_targets exists but is not a dict (e.g., list)."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    config = {
        "template": "livespec",
        "cross_repo_targets": ["not", "a", "dict"],
    }
    _ = (project_root / ".livespec.jsonc").write_text(json.dumps(config), encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="skipped",
        message=(
            "wiring-completeness-cross-repo: project carries no "
            "`cross_repo_targets` block; check skipped"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_malformed_github_url_treated_as_unresolvable(
    *,
    tmp_path: Path,
) -> None:
    """`fail` with `:no-justfile-resolved` when github_url is malformed and no clone."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "not-a-github-url",
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_target_with_missing_github_url_treated_as_unresolvable(
    *,
    tmp_path: Path,
) -> None:
    """`fail` with `:no-justfile-resolved` when github_url is missing entirely."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {},
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_non_dict_target_is_silently_dropped(
    *,
    tmp_path: Path,
) -> None:
    """A non-dict target (e.g., string) is skipped, not crashed-on.

    With only the malformed entry and no other siblings, the result
    is `skipped` (no usable siblings to walk).
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    config = {
        "template": "livespec",
        "cross_repo_targets": {
            "sibling-a": "not-a-dict",
        },
    }
    _ = (project_root / ".livespec.jsonc").write_text(json.dumps(config), encoding="utf-8")

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="skipped",
        message=(
            "wiring-completeness-cross-repo: cross_repo_targets "
            "contains no sibling entries (only the host repo or empty); "
            "no siblings to walk"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_default_branch_falls_back_to_master_when_unset(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default branch defaults to `master` when target.default_branch is unset."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                # no default_branch
            },
        },
    )

    captured_argvs: list[list[str]] = []

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], Any]:
        _ = cwd
        captured_argvs.append(argv)
        return IOResult.from_value(
            _completed(
                stdout=_gh_contents_payload(justfile_text=_make_justfile_text(slugs=canonical))
            ),
        )

    monkeypatch.setattr(io_proc, "run_subprocess", fake_run_subprocess)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    _ = wiring_completeness_cross_repo.run(ctx=ctx)
    assert any("ref=master" in arg for argv in captured_argvs for arg in argv)


def test_gh_fallback_with_malformed_json_payload_treated_as_unresolved(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` with `:no-justfile-resolved` when gh returns invalid JSON."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
            },
        },
    )
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(stdout="<<not json>>"),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_gh_fallback_with_non_object_json_payload_treated_as_unresolved(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` when gh api stdout is valid JSON but not a dict."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
            },
        },
    )
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(stdout="[1, 2, 3]"),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_gh_fallback_with_wrong_encoding_treated_as_unresolved(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` when gh api returns encoding != 'base64'."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
            },
        },
    )
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=json.dumps({"content": "plaintext", "encoding": "utf-8"})
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_gh_fallback_with_invalid_base64_treated_as_unresolved(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` when gh api returns invalid base64 in `content`."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
            },
        },
    )
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=json.dumps({"content": "@@@not-base64@@@", "encoding": "base64"})
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_gh_fallback_with_invalid_utf8_treated_as_unresolved(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`fail` when gh api returns base64-decoded bytes that aren't valid UTF-8."""
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
            },
        },
    )
    invalid_utf8 = base64.b64encode(b"\xff\xfe\xfd").decode("ascii")
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=json.dumps({"content": invalid_utf8, "encoding": "base64"})
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert "sibling-a→:no-justfile-resolved" in finding.message


def test_default_branch_non_string_falls_back_to_master(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When default_branch is not a string (e.g., null), fall back to `master`."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "default_branch": None,
            },
        },
    )

    captured_argvs: list[list[str]] = []

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], Any]:
        _ = cwd
        captured_argvs.append(argv)
        return IOResult.from_value(
            _completed(
                stdout=_gh_contents_payload(justfile_text=_make_justfile_text(slugs=canonical))
            ),
        )

    monkeypatch.setattr(io_proc, "run_subprocess", fake_run_subprocess)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    _ = wiring_completeness_cross_repo.run(ctx=ctx)
    assert any("ref=master" in arg for argv in captured_argvs for arg in argv)


def test_local_clone_empty_string_falls_to_github(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty-string local_clone is treated as absent → GitHub fallback fires."""
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": "",
            },
        },
    )
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=_gh_contents_payload(justfile_text=_make_justfile_text(slugs=canonical))
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_blank_and_comment_lines_inside_targets_array_are_skipped(
    *,
    tmp_path: Path,
) -> None:
    """Blank lines and comment-only lines inside `targets=(...)` are tolerated.

    Covers the `stripped == ""` + `stripped.startswith("#")` branches
    in the justfile parser. The slug list reads cleanly past such
    decorative lines.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    body_lines = "\n".join(f"        {slug}" for slug in canonical)
    justfile_text = (
        "check:\n"
        "    #!/usr/bin/env bash\n"
        "    targets=(\n"
        "        # a leading comment inside the array\n"
        "\n"
        f"{body_lines}\n"
        "        \n"
        "    )\n"
    )
    clone = _setup_sibling_clone_with_raw_justfile(
        tmp_path=tmp_path, slug="sibling-a", justfile_text=justfile_text
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_non_slug_token_lines_inside_targets_array_are_skipped(
    *,
    tmp_path: Path,
) -> None:
    """Lines that don't match the slug-token pattern fall through.

    Covers the `slug_match is None` branch where a non-blank,
    non-comment line inside the targets array doesn't match the
    slug regex.
    """
    canonical = _get_canonical_slugs()
    dropped = canonical[0]
    remaining = tuple(s for s in canonical if s != dropped)
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    body_lines = "\n".join(f"        {slug}" for slug in remaining)
    justfile_text = (
        "check:\n" "    targets=(\n" "        !@$ not a slug\n" f"{body_lines}\n" "    )\n"
    )
    clone = _setup_sibling_clone_with_raw_justfile(
        tmp_path=tmp_path, slug="sibling-a", justfile_text=justfile_text
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert f"sibling-a→{dropped}" in finding.message


def test_targets_array_without_closing_paren_returns_partial_slugs(
    *,
    tmp_path: Path,
) -> None:
    """Reaching EOF inside `targets=(...)` returns the partial slug list.

    Covers the `return tuple(collected)` fallthrough after the
    for-loop ends with `in_targets_array=True` — a malformed
    justfile that never closes its targets array.
    """
    canonical = _get_canonical_slugs()
    partial = canonical[:5]
    body_lines = "\n".join(f"        {slug}" for slug in partial)
    justfile_text = "check:\n    targets=(\n" + body_lines + "\n"
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    clone = _setup_sibling_clone_with_raw_justfile(
        tmp_path=tmp_path, slug="sibling-a", justfile_text=justfile_text
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "fail"
    assert f"sibling-a→{canonical[5]}" in finding.message


def test_local_clone_with_resolve_oserror_treated_as_non_host(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An OSError on Path.resolve() falls through is_host_repo's except arm.

    Covers the `except OSError` arm of `is_host_repo`.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=canonical)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
            },
        },
    )

    original_resolve = Path.resolve
    target_path_str = str(sibling_clone)

    def fake_resolve(self: Path, *args: object, **kwargs: object) -> Path:
        if str(self) == target_path_str:
            raise OSError("simulated resolve failure")
        return original_resolve(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_host_repo_detected_via_worktree_under_primary(
    *,
    tmp_path: Path,
) -> None:
    """A target whose local_clone is an ANCESTOR of project_root is host.

    Covers the worktree-under-primary case: the doctor is invoked
    from a secondary worktree at `<primary>/.claude/worktrees/<id>`
    and the cross_repo_targets entry's local_clone points at the
    primary checkout. The check should detect the entry as the
    host repo and skip it.
    """
    canonical = _get_canonical_slugs()
    primary = tmp_path / "primary"
    primary.mkdir()
    project_root = primary / ".claude" / "worktrees" / "agent-x"
    project_root.mkdir(parents=True)
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    # Also stage a non-host sibling with the canonical set wired
    # so the manifest has at least one entry to walk after the
    # host is filtered out.
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=canonical)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "host": {
                "github_url": "https://github.com/example/host",
                "local_clone": str(primary),
            },
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_path_a_falls_through_when_local_clone_is_not_a_git_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Path A falls through to Path B when `local_clone` is not a git repo.

    Failure mode: `local_clone` exists as a directory but has no
    `.git` and is not a bare repo, so `git -C <local_clone> show
    HEAD:justfile` exits non-zero. The check must fall through to
    Path B (gh api) rather than crashing or returning a false
    `:no-justfile-resolved`.

    This is one of the three documented Path A failure modes after
    the architectural pivot from filesystem read to git db read.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    # Create a directory that is NOT a git repo. The Path A code
    # invokes `git -C <local_clone> show HEAD:justfile`, which
    # exits 128 with "fatal: not a git repository". Even if a
    # `justfile` is present in the working tree, it is invisible
    # to the git db read.
    non_git_clone = tmp_path / "not-a-git-repo"
    non_git_clone.mkdir()
    _ = (non_git_clone / "justfile").write_text(
        _make_justfile_text(slugs=canonical), encoding="utf-8"
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(non_git_clone),
            },
        },
    )
    justfile_text = _make_justfile_text(slugs=canonical)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=_gh_contents_payload(justfile_text=justfile_text)
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_path_a_falls_through_when_justfile_not_at_head(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Path A falls through to Path B when justfile is absent at HEAD.

    Failure mode: `local_clone` is a real git repo with at least
    one commit (so HEAD resolves), but `justfile` was never
    committed (or was deleted). `git -C <local_clone> show
    HEAD:justfile` exits 128 with "fatal: path 'justfile' does
    not exist in 'HEAD'". The check must fall through to Path B.

    This is one of the three documented Path A failure modes
    after the architectural pivot from filesystem read to git
    db read.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    # Create a real git repo via the `justfile_text=None` arm of
    # `_git_init_and_commit` (init only, no commit), then commit
    # an unrelated file so HEAD resolves but no `justfile` is
    # ever at HEAD. The working tree justfile (if any) is
    # invisible to `git show HEAD:justfile`.
    clone = tmp_path / "sibling-a"
    clone.mkdir()
    _git_init_and_commit(clone=clone, justfile_text=None)
    _ = (clone / "README.md").write_text("placeholder", encoding="utf-8")
    _ = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=t@t", "add", "README.md"],
        cwd=clone,
        check=True,
    )
    _ = subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=t@t",
            "commit",
            "--quiet",
            "-m",
            "init",
        ],
        cwd=clone,
        check=True,
    )
    # Write a justfile to the working tree only — Path A's git
    # show HEAD:justfile MUST NOT see it.
    _ = (clone / "justfile").write_text(_make_justfile_text(slugs=canonical), encoding="utf-8")
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )
    # Path B serves the wired canonical set; the check's "pass"
    # status proves Path A correctly fell through.
    justfile_text = _make_justfile_text(slugs=canonical)
    _install_gh_fake(
        monkeypatch=monkeypatch,
        response_by_owner_name={
            ("example", "sibling-a"): _completed(
                stdout=_gh_contents_payload(justfile_text=justfile_text)
            ),
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_skipped_when_dev_tooling_substrate_unimportable(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`skipped` (not crash) when `livespec_dev_tooling` is unimportable.

    Regression for li-rvdctr: the check's canonical-slug source,
    `livespec_dev_tooling.canonical_checks.canonical_check_slugs`, lives in
    a NON-bundled sibling package — importable under `uv`/CI but absent
    under bare `python3` (the `python3 bin/doctor_static.py` plugin flow the
    revise wrapper spawns via `sys.executable`) and in the installed-plugin
    bundle. A top-level import of it crashed the WHOLE static phase with a
    `ModuleNotFoundError` in those contexts, so `_revise_doctor` saw empty
    stdout, reported "malformed JSON", and silently bypassed every static
    check. The fix makes the import lazy + graceful: when the substrate is
    unimportable, the cross-repo backstop degrades to a `skipped` finding
    while the rest of the static phase runs normally.

    The fixture uses a `.livespec.jsonc` with a NON-host sibling so the
    walk reaches `_evaluate_manifest` (where the slug resolution happens),
    then patches `builtins.__import__` to raise `ModuleNotFoundError` for
    `livespec_dev_tooling.canonical_checks`. Both the `status == "skipped"`
    AND the `livespec_dev_tooling`-naming assertions are made so that a Red
    that happens to produce a skipped finding for some OTHER reason cannot
    pass.
    """
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(tmp_path / "sibling-a"),
                "default_branch": "master",
            },
        },
    )

    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: Any = None,
        locals_: Any = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if name == "livespec_dev_tooling.canonical_checks" or (
            name == "livespec_dev_tooling" and fromlist
        ):
            raise ModuleNotFoundError(name)
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    io_result = wiring_completeness_cross_repo.run(ctx=ctx)
    from returns.unsafe import unsafe_perform_io

    inner = unsafe_perform_io(io_result)
    from returns.result import Success

    assert isinstance(inner, Success)
    finding = inner.unwrap()
    assert finding.status == "skipped"
    assert "livespec_dev_tooling" in finding.message


def test_path_a_reads_via_git_db_on_bare_flag_clone(
    *,
    tmp_path: Path,
) -> None:
    """Path A reads the justfile via `git show HEAD:` on a bare-flag clone.

    Although the post-v095 family-wide invariant is the
    commit-refuse hook (not `core.bare = true`), bare clones
    remain valid as cross-repo siblings — a freshly-cloned
    repo carrying `core.bare = true` (e.g., a CI worker that
    only needs read access to a sibling's git db) MUST still
    resolve through Path A. A filesystem read of
    `<clone>/justfile` would return stale or empty content on
    such a clone; the git db `git show HEAD:justfile` returns
    the canonical master-tip content regardless.

    This test simulates that case by creating a working clone,
    committing a wired justfile, then flipping
    `core.bare = true` on the clone's config and overwriting
    the working-tree justfile with stale content. The Path A
    code must return the COMMITTED slug set (canonical), not
    the stale-working-tree set (empty).

    This is the CRITICAL test case — the architectural pivot
    from filesystem read to git db read was driven by exactly
    this stale-on-disk concern.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    clone = tmp_path / "bare-flag-sibling"
    clone.mkdir()
    # Init + commit the canonical wired justfile.
    _git_init_and_commit(clone=clone, justfile_text=_make_justfile_text(slugs=canonical))
    # Now simulate the bare-flag primary checkout: flip
    # core.bare = true AND overwrite the working-tree justfile
    # with stale (empty) content. A filesystem read would now
    # return the stale text; the git db read returns the
    # committed (canonical) text.
    _ = subprocess.run(
        ["git", "config", "--local", "core.bare", "true"],
        cwd=clone,
        check=True,
    )
    _ = (clone / "justfile").write_text(
        "default:\n    @just --list\n",  # stale: no `check:` recipe
        encoding="utf-8",
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    # If Path A had erroneously read from the working tree, the
    # stale justfile lacks `check:`, the parser would return
    # None (= `:no-check-recipe`), and the status would be
    # `fail`. The `pass` status here proves Path A reads the
    # git db, not the working tree.
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


# --- resolve_effective_local_clone helper tests ---


def test_resolve_effective_local_clone_returns_manifest_path_when_env_unset() -> None:
    """When LIVESPEC_SIBLING_CLONES_ROOT is unset, manifest value wins.

    The local-dev path against `/data/projects/<sibling>` is preserved
    via the manifest's `local_clone` field; the env-var override is
    the CI-only path.
    """
    result = resolve_effective_local_clone(
        sibling_slug="livespec-orchestrator-git-jsonl",
        target={"local_clone": "/data/projects/livespec-orchestrator-git-jsonl"},
        env={},
    )
    assert result == "/data/projects/livespec-orchestrator-git-jsonl"


def test_resolve_effective_local_clone_returns_none_when_no_path_available() -> None:
    """When neither env var nor manifest provides a path, return None.

    The caller treats None as "Path A unavailable, fall through to
    Path B (GitHub API)."
    """
    result = resolve_effective_local_clone(
        sibling_slug="livespec-orchestrator-git-jsonl",
        target={"github_url": "https://github.com/x/y"},
        env={},
    )
    assert result is None


def test_resolve_effective_local_clone_returns_none_when_manifest_value_empty() -> None:
    """Empty-string `local_clone` is treated as absent (None)."""
    result = resolve_effective_local_clone(
        sibling_slug="livespec-orchestrator-git-jsonl",
        target={"local_clone": ""},
        env={},
    )
    assert result is None


def test_resolve_effective_local_clone_uses_env_var_when_set(*, tmp_path: Path) -> None:
    """When the env var is set, it overrides the manifest's local_clone.

    The result is `<env-var-value>/<sibling-slug>` regardless of what
    the manifest's `local_clone` field says. This is the CI path:
    the workflow clones siblings to a fresh root and points the
    check at it via the env var.
    """
    clones_root = tmp_path / "ci-clones"
    result = resolve_effective_local_clone(
        sibling_slug="livespec-orchestrator-git-jsonl",
        target={"local_clone": "/data/projects/livespec-orchestrator-git-jsonl"},
        env={CLONES_ROOT_ENV_VAR: str(clones_root)},
    )
    assert result == str(clones_root / "livespec-orchestrator-git-jsonl")


def test_resolve_effective_local_clone_env_var_overrides_missing_manifest(
    *,
    tmp_path: Path,
) -> None:
    """The env var even applies when the manifest lacks a local_clone."""
    clones_root = tmp_path / "ci-clones"
    result = resolve_effective_local_clone(
        sibling_slug="livespec-runtime",
        target={"github_url": "https://github.com/thewoolleyman/livespec-runtime"},
        env={CLONES_ROOT_ENV_VAR: str(clones_root)},
    )
    assert result == str(clones_root / "livespec-runtime")


def test_resolve_effective_local_clone_empty_env_var_falls_back_to_manifest() -> None:
    """A set-but-empty env var is treated as unset (manifest wins)."""
    result = resolve_effective_local_clone(
        sibling_slug="livespec-orchestrator-git-jsonl",
        target={"local_clone": "/data/projects/livespec-orchestrator-git-jsonl"},
        env={CLONES_ROOT_ENV_VAR: ""},
    )
    assert result == "/data/projects/livespec-orchestrator-git-jsonl"


def test_host_repo_detected_by_slug_basename_match_when_manifest_path_mismatches(
    *,
    tmp_path: Path,
) -> None:
    """Host detection via slug-vs-basename when manifest path doesn't match cwd.

    Simulates the CI case: the manifest declares
    `cross_repo_targets.livespec.local_clone = /data/projects/livespec`
    but the actual `project_root` is
    `/home/runner/work/livespec/livespec` (GitHub Actions's clone
    location). The path-comparison tier would NOT match, but the
    slug-vs-basename tier MUST recognize the `livespec` slug as the
    host because `project_root.name == "livespec"`.

    Without this tier, the CI host repo would be walked as a sibling
    and (because the CI workflow deliberately clones only NON-host
    siblings into the env-var-pointed root) would fall through to
    Path B (GitHub fallback), which can flake. The slug-keyed
    identity check avoids the round-trip entirely.
    """
    canonical = _get_canonical_slugs()
    # Use a tmp_path subdir whose basename matches the slug —
    # simulates the CI fixture where project_root.name == sibling_slug.
    project_root = tmp_path / "livespec"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    # The manifest declares a local_clone path that does NOT match
    # the project_root (simulating /data/projects/livespec vs
    # /home/runner/work/livespec/livespec in CI).
    sibling_clone = _setup_sibling_clone(tmp_path=tmp_path, slug="sibling-a", slugs=canonical)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "livespec": {
                "github_url": "https://github.com/example/livespec",
                "local_clone": "/data/projects/livespec",
            },
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "local_clone": str(sibling_clone),
            },
        },
    )

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    # The host `livespec` target MUST be excluded; only `sibling-a`
    # is walked, and it wires the full canonical set → pass.
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_env_var_override_makes_path_a_resolve_via_env_root(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: env var redirects Path A to a fresh clones-root.

    Simulates CI: the manifest declares a bogus `local_clone` path
    that doesn't exist on the runner, BUT the env var points to a
    freshly-cloned siblings-root where the sibling DOES exist with
    a wired justfile. The check MUST pass because the env-var
    override redirects Path A to the fresh clone.
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    clones_root = tmp_path / "ci-clones"
    clones_root.mkdir()
    sibling_clone = clones_root / "livespec-orchestrator-git-jsonl"
    sibling_clone.mkdir()
    _git_init_and_commit(
        clone=sibling_clone,
        justfile_text=_make_justfile_text(slugs=canonical),
    )
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "livespec-orchestrator-git-jsonl": {
                "github_url": "https://github.com/example/sibling",
                # Bogus path that does NOT exist on the test runner —
                # without the env-var override, Path A would fall
                # through to Path B (GitHub fallback).
                "local_clone": "/nonexistent/path/to/sibling",
            },
        },
    )
    monkeypatch.setenv(CLONES_ROOT_ENV_VAR, str(clones_root))

    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)


def test_fetch_justfile_from_github_forces_explicit_get_method(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Path B's `gh api` argv MUST carry an explicit GET method pin.

    `gh api <endpoint> -f key=value` switches the default HTTP
    method from GET to POST whenever a field flag is present;
    `POST /repos/<owner>/<name>/contents/justfile` is the
    create-file endpoint and answers 404, so the fallback silently
    failed on every invocation (masked for as long as Path A's
    local clone resolved). The argv MUST pin the method with an
    adjacent `--method GET` pair, and the contents endpoint MUST
    stay at argv[2] (the position the gh fake in this suite — and
    any consumer matching on it — indexes).
    """
    canonical = _get_canonical_slugs()
    project_root, spec_root = _setup_project(tmp_path=tmp_path)
    _write_livespec_jsonc(
        project_root=project_root,
        cross_repo_targets={
            "sibling-a": {
                "github_url": "https://github.com/example/sibling-a",
                "default_branch": "master",
            },
        },
    )
    justfile_text = _make_justfile_text(slugs=canonical)
    captured: list[list[str]] = []

    def fake_run_subprocess(
        *,
        argv: list[str],
        cwd: Path | None = None,
    ) -> IOResult[subprocess.CompletedProcess[str], Any]:
        _ = cwd
        captured.append(argv)
        return IOResult.from_value(
            _completed(stdout=_gh_contents_payload(justfile_text=justfile_text)),
        )

    monkeypatch.setattr(io_proc, "run_subprocess", fake_run_subprocess)
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = wiring_completeness_cross_repo.run(ctx=ctx)
    assert captured, "gh api was never invoked"
    argv = captured[0]
    assert argv[0] == "gh"
    assert argv[1] == "api"
    assert argv[2] == "repos/example/sibling-a/contents/justfile"
    assert "--method" in argv, f"argv lacks an explicit method pin: {argv}"
    method_index = argv.index("--method")
    assert argv[method_index + 1] == "GET", f"method is not GET: {argv}"
    expected = Finding(
        check_id="doctor-wiring-completeness-cross-repo",
        status="pass",
        message=(
            "wiring-completeness-cross-repo: every registered sibling's "
            "`check` aggregate wires every canonical slug"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
