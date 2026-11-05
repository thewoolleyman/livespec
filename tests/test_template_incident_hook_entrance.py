"""A repo scaffolded from the orchestrator-plugin template inherits the incident entrance.

`SPECIFICATION/contracts.md` requires generated scaffolds to preserve the
incident-only exception AND the complete normal path "through the normally
released shared execution interfaces", and requires the trusted incident
context to be resolved before any hook member, evidence or delegation is
selected.

The template does not carry that resolver. It REUSES the released
`livespec_dev_tooling.install_commit_refuse_hooks` installer, whose canonical
hook body runs `livespec_dev_tooling.incident_hook_entry` before it hands the
hook to lefthook (and so before any generated `just` recipe runs). The
resolver therefore reaches a generated repo only when the template pins a
`livespec-dev-tooling` release that carries it. v1.172.0 is the first such
release. A template pinned below it scaffolds hooks with no incident
resolution, so its consumers would honour neither the exception nor the
malformed-flag refusal until a later pin bump.

These tests render the template and assert that chain end to end:

1. the rendered pin names a release that carries the entrance;
2. the rendered installer recipe delegates to the shared installer, and the
   released hook body it installs resolves incident mode before lefthook,
   continuing to the normal path only on the entrance's ordinary result;
3. that released entrance returns the ordinary result when neither flag is
   set, so a generated ordinary invocation runs its complete normal policy,
   and refuses a malformed flag instead of falling back to it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from livespec_dev_tooling.incident_execution import (
    EXPEDITED_INCIDENT_RESPONSE,
    EXPEDITED_INCIDENT_RESPONSE_REVERT,
)
from livespec_dev_tooling.incident_hook_entry import main as incident_hook_main
from livespec_dev_tooling.install_commit_refuse_hooks import CANONICAL_HOOK_BODY

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_ROOT = _REPO_ROOT / "templates" / "orchestrator-plugin"

# Inert fixture answers, the same set the copier smoke and wiring-lockstep
# tests use. Nothing asserted here depends on any of them.
_TEMPLATE_ANSWERS: tuple[str, ...] = (
    "plugin_short_name=smoketest",
    "plugin_full_name=livespec-impl-smoketest",
    "plugin_description=Smoke-test fixture plugin",
    "plugin_namespace=livespec-impl-smoketest",
    "author_name=Smoke Test",
    "author_email=smoke@example.invalid",
    "github_owner=thewoolleyman",
    "github_repo=livespec-impl-smoketest",
    "python_version=3.13",
    "livespec_release_tag=v0.1.0",
)

# The first livespec-dev-tooling release whose installed commit-refuse hook
# body resolves incident mode through `incident_hook_entry` before lefthook.
_FIRST_INCIDENT_ENTRANCE_RELEASE = (1, 172, 0)

# `incident_hook_entry` exits 75 for ordinary work and 78 for a refusal.
_ORDINARY = 75
_REFUSED = 78

_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

# The `[tool.uv.sources]` entry that resolves the shared library. Matched as a
# line rather than parsed as TOML because the supported Python floor predates
# `tomllib` and the project carries no TOML reader dependency.
_DEV_TOOLING_SOURCE = re.compile(
    r'^livespec-dev-tooling\s*=\s*\{[^}]*\btag\s*=\s*"([^"]+)"[^}]*\}\s*$', re.MULTILINE
)


def _render_template(*, target: Path) -> None:
    """Render the orchestrator-plugin template into `target` with stock answers."""
    data_args = [item for answer in _TEMPLATE_ANSWERS for item in ("--data", answer)]
    result = subprocess.run(
        [
            "uv",
            "run",
            "copier",
            "copy",
            "--defaults",
            "--trust",
            "--vcs-ref=HEAD",
            *data_args,
            str(_TEMPLATE_ROOT),
            str(target),
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        result.returncode == 0
    ), f"copier render failed: stdout={result.stdout!r} stderr={result.stderr!r}"


def _rendered_dev_tooling_tag(*, tree: Path) -> str:
    """The `livespec-dev-tooling` git tag the rendered `pyproject.toml` resolves."""
    text = (tree / "pyproject.toml").read_text(encoding="utf-8")
    sources = _DEV_TOOLING_SOURCE.findall(text)
    assert len(sources) == 1, f"expected one livespec-dev-tooling uv source, found {sources!r}"
    return sources[0]


@pytest.fixture(name="rendered")
def _rendered(*, tmp_path: Path) -> Path:
    target = tmp_path / "rendered"
    _render_template(target=target)
    return target


def test_rendered_template_pins_a_release_carrying_the_incident_entrance(*, rendered: Path) -> None:
    """A freshly scaffolded repo resolves a dev-tooling release with the entrance."""
    tag = _rendered_dev_tooling_tag(tree=rendered)
    match = _TAG.match(tag)
    assert match is not None, f"rendered livespec-dev-tooling tag {tag!r} is not vMAJOR.MINOR.PATCH"
    version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    assert version >= _FIRST_INCIDENT_ENTRANCE_RELEASE, (
        f"the template pins livespec-dev-tooling {tag}, below the first release "
        "(v1.172.0) whose installed hook resolves incident mode before lefthook"
    )


def test_rendered_hooks_resolve_incident_mode_before_any_generated_recipe(
    *, rendered: Path
) -> None:
    """The generated installer reuses the released body, which resolves first."""
    justfile = (rendered / "justfile").read_text(encoding="utf-8")
    recipe = re.search(r"^install-commit-refuse-hooks:\n((?:[ \t]+.*\n)+)", justfile, re.MULTILINE)
    assert recipe is not None, "rendered justfile lacks install-commit-refuse-hooks"
    assert "python -m livespec_dev_tooling.install_commit_refuse_hooks" in recipe.group(1)

    entrance = CANONICAL_HOOK_BODY.find("python -m livespec_dev_tooling.incident_hook_entry")
    lefthook = CANONICAL_HOOK_BODY.find("lefthook run")
    assert entrance != -1, "released hook body does not call the incident entrance"
    assert lefthook != -1, "released hook body does not delegate to lefthook"
    assert entrance < lefthook, "incident resolution must precede the lefthook delegation"
    after_entrance = CANONICAL_HOOK_BODY[entrance:lefthook]
    assert 'if [ "$incident_status" -ne 75 ]; then' in after_entrance
    assert 'exit "$incident_status"' in after_entrance


def test_released_entrance_runs_ordinary_work_normally_and_refuses_malformed_flags(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Flags absent keeps the complete normal path; a malformed flag is refused."""
    monkeypatch.delenv(EXPEDITED_INCIDENT_RESPONSE, raising=False)
    monkeypatch.delenv(EXPEDITED_INCIDENT_RESPONSE_REVERT, raising=False)
    assert incident_hook_main(argv=["pre-commit"]) == _ORDINARY

    monkeypatch.setenv(EXPEDITED_INCIDENT_RESPONSE, "maybe")
    assert incident_hook_main(argv=["pre-commit"]) == _REFUSED
    assert "malformed incident flag" in capsys.readouterr().err


# ---------------------------------------------------------------
# Direct recipe entrances. A generated `just` recipe can be invoked
# DIRECTLY, not through the installed hook, so the hook entrance above
# never sees it. livespec-dev-tooling v1.178.0 is the first release whose
# `incident_gate_entry` boundary accepts every generated recipe entrance
# (`check`, `check-pre-commit`, `check-pre-push`, `check-coverage`,
# `lint-autofix-staged`) and whose `commit_pairs_source_and_test.main`
# and `red_green_replay.main` carry `IncidentEntrance` themselves. The
# shell recipes mirror the released prelude byte for byte: a presence
# prefilter that decides nothing, then the released boundary, continuing
# only on its 75 and refusing on every other status.
# ---------------------------------------------------------------

_FIRST_RECIPE_ENTRANCE_RELEASE = (1, 178, 0)

_PREFILTER = (
    'if [ -n "${EXPEDITED_INCIDENT_RESPONSE:-}${EXPEDITED_INCIDENT_RESPONSE_REVERT:-}'
    '${LIVESPEC_INCIDENT_CONTEXT:-}${LIVESPEC_INCIDENT_AUTHORITY_QUERY:-}" ]; then'
)
_CONTINUE_ONLY_ON_ORDINARY = (
    '[ "$incident_status" -eq 75 ] || exit $((incident_status == 0 ? 78 : incident_status))'
)

# recipe -> (entrance name the released boundary accepts, first line of real work)
_SHELL_RECIPE_ENTRANCES: dict[str, tuple[str, str]] = {
    "check": ("check", "uv sync --all-groups"),
    "check-pre-commit": ("check-pre-commit", "staged=$(git diff --cached"),
    "check-pre-push": ("check-pre-push", "livespec_dev_tooling.green_token check"),
    "check-coverage": ("check-coverage", "uv run pytest"),
    "lint-autofix-staged": ("lint-autofix-staged", "staged=$(git diff --cached"),
}

# recipe -> the released module whose `main` carries `IncidentEntrance`
_MODULE_RECIPE_ENTRANCES: dict[str, str] = {
    "check-commit-pairs-source-and-test": "livespec_dev_tooling.checks.commit_pairs_source_and_test",
    "check-red-green-replay": "livespec_dev_tooling.checks.red_green_replay",
}


def _recipe_body(*, justfile: str, name: str) -> str:
    """The indented body of recipe `name` (any parameters) in a rendered justfile."""
    pattern = rf"^{re.escape(name)}(?:[ \t]+[^:\n]*)?:\n((?:[ \t]+.*\n)+)"
    recipe = re.search(pattern, justfile, re.MULTILINE)
    assert recipe is not None, f"rendered justfile lacks the {name} recipe"
    return recipe.group(1)


def test_rendered_template_pins_a_release_carrying_the_recipe_entrances(*, rendered: Path) -> None:
    """The pin names the first release whose boundary accepts every recipe entrance."""
    tag = _rendered_dev_tooling_tag(tree=rendered)
    match = _TAG.match(tag)
    assert match is not None, f"rendered livespec-dev-tooling tag {tag!r} is not vMAJOR.MINOR.PATCH"
    version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    assert version >= _FIRST_RECIPE_ENTRANCE_RELEASE, (
        f"the template pins livespec-dev-tooling {tag}, below the first release "
        "(v1.178.0) whose incident_gate_entry accepts every generated recipe entrance"
    )


@pytest.mark.parametrize(
    ("recipe", "entrance", "first_work"),
    [
        (recipe, entrance, first_work)
        for recipe, (entrance, first_work) in _SHELL_RECIPE_ENTRANCES.items()
    ],
)
def test_rendered_shell_recipes_resolve_incident_mode_before_their_first_work(
    *, rendered: Path, recipe: str, entrance: str, first_work: str
) -> None:
    """Each direct shell entrance calls the released boundary first, continuing only on 75."""
    body = _recipe_body(justfile=(rendered / "justfile").read_text(encoding="utf-8"), name=recipe)
    boundary = f"uv run --no-sync python -m livespec_dev_tooling.incident_gate_entry {entrance} || incident_status=$?"
    prefilter_at = body.find(_PREFILTER)
    boundary_at = body.find(boundary)
    continue_at = body.find(_CONTINUE_ONLY_ON_ORDINARY)
    work_at = body.find(first_work)
    assert prefilter_at != -1, f"{recipe}: no incident presence prefilter"
    assert boundary_at != -1, f"{recipe}: does not call the released boundary as {entrance!r}"
    assert continue_at != -1, f"{recipe}: does not continue only on the boundary's 75"
    assert work_at != -1, f"{recipe}: expected first real work {first_work!r} not found"
    assert (
        prefilter_at < boundary_at < continue_at < work_at
    ), f"{recipe}: incident resolution must precede the recipe's first real work"
    assert body.count("incident_gate_entry") == 1, f"{recipe}: the boundary must run exactly once"


@pytest.mark.parametrize(("recipe", "module"), sorted(_MODULE_RECIPE_ENTRANCES.items()))
def test_rendered_module_recipes_delegate_to_the_released_guarded_main(
    *, rendered: Path, recipe: str, module: str
) -> None:
    """Module-backed recipes reach the boundary through the released `IncidentEntrance` main."""
    body = _recipe_body(justfile=(rendered / "justfile").read_text(encoding="utf-8"), name=recipe)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    assert len(lines) == 1, f"{recipe}: expected a single delegation line, got {lines!r}"
    assert lines[0].startswith(
        f"uv run python -m {module}"
    ), f"{recipe}: must delegate to the released {module} main, which carries IncidentEntrance"
    assert (
        "incident_gate_entry" not in body
    ), f"{recipe}: the released main already resolves; a shell prelude would resolve twice"
