"""Lockstep tests for the worktree-discipline pack's two DISTRIBUTION surfaces.

The central `worktree-pack-wired` fleet row asserts the pack wiring over a
MEMBER's committed default branch, so it catches an unwired repo only once the
repo exists and is a member. Two surfaces reach repos the row never sees, and
each gets a test here (plan `plan/optimize-gates`, R4 plus the ratified adopter
deferral in research note 001 section 5):

1. **The copier template** — `templates/orchestrator-plugin/` is where a fleet
   repo is BORN wired. Rendering it and running the row's own predicate over
   the output means a template edit that drops a wiring line fails here rather
   than in whatever repo is scaffolded next.
2. **The installation prompt** — `docs/livespec-installation-prompt.md` is the
   onboarding surface for ADOPTERS, who are outside central enforcement by
   ratified rule (the adopter lane is one row wide, and the fleet's GitHub App
   is not installed on adopter repos). Their enforcement is their own
   `just check` running the same shipped package, which makes the prompt the
   thing that must NAME every artifact — so the second test derives the literal
   set from the predicate and asserts the prompt carries each one.

Both tests read the predicate rather than a hand-written copy of the wiring:
`worktree_pack_wiring_gaps` is public precisely so a sibling repo can run it
over bytes livespec-dev-tooling never sees. Adding a sixth wiring fact upstream
therefore reds the second test until the prompt documents it, with no edit
here.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from livespec_dev_tooling.fleet.worktree_pack_wiring import (
    GITIGNORE_PATH,
    JUSTFILE_PATH,
    LEFTHOOK_PATH,
    LIVESPEC_JSONC_PATH,
    WIRING_FILES,
    worktree_pack_wiring_gaps,
)

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_ROOT = _REPO_ROOT / "templates" / "orchestrator-plugin"
_INSTALLATION_PROMPT = _REPO_ROOT / "docs" / "livespec-installation-prompt.md"

# The stock answer set the sibling copier smoke test uses. Values are inert
# fixtures — the wiring under test is answer-independent, so a rendered tree
# that depends on any of them would itself be the finding.
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

# A `WiringGap.missing` is EITHER the exact line an operator adds (the import
# lines, the ignore entries, the `.livespec.jsonc` key) OR a sentence naming
# its literals in backticks (the installer recipe, the two lefthook hooks).
# Pulling the backticked spans out of the second form is what makes both forms
# reduce to "a string the prompt must contain".
_BACKTICKED = re.compile(r"`([^`]+)`")


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


def _wiring_gaps_of(*, tree: Path) -> tuple[str, ...]:
    """Every wiring gap the predicate reports for the four files under `tree`."""
    texts = {path: (tree / path).read_text(encoding="utf-8") for path in WIRING_FILES}
    gaps = worktree_pack_wiring_gaps(
        justfile_text=texts[JUSTFILE_PATH],
        gitignore_text=texts[GITIGNORE_PATH],
        lefthook_text=texts[LEFTHOOK_PATH],
        livespec_jsonc_text=texts[LIVESPEC_JSONC_PATH],
    )
    return tuple(f"{gap.severity} {gap.path}: {gap.missing}" for gap in gaps)


def _required_prompt_literals() -> tuple[str, ...]:
    """Every literal the installation prompt must name, DERIVED from the predicate.

    Four empty texts make the predicate report its whole obligation set at
    once, which is the only enumeration of the wiring that exists — asking it
    this way is what keeps the prompt's coverage in lockstep with the row
    instead of with a copy of the row written down here.
    """
    gaps = worktree_pack_wiring_gaps(
        justfile_text="",
        gitignore_text="",
        lefthook_text="",
        livespec_jsonc_text="",
    )
    literals: list[str] = []
    for gap in gaps:
        quoted: list[str] = [match.group(1) for match in _BACKTICKED.finditer(gap.missing)]
        literals.extend(quoted if quoted else [gap.missing])
    return tuple(dict.fromkeys(literals))


def _literals_missing_from(*, text: str) -> tuple[str, ...]:
    """The required literals `text` does not name, in obligation order."""
    return tuple(literal for literal in _required_prompt_literals() if literal not in text)


def test_rendered_template_carries_the_whole_pack_wiring(*, tmp_path: Path) -> None:
    """R4 — a repo scaffolded from the template is born passing the central row."""
    target = tmp_path / "rendered"
    _render_template(target=target)

    gaps = _wiring_gaps_of(tree=target)

    assert gaps == (), (
        "the rendered orchestrator-plugin template does not carry the whole "
        "worktree-pack wiring, so a repo scaffolded from it would be born as a "
        f"`worktree-pack-wired` offender; gaps: {gaps}"
    )


def test_predicate_reports_the_gap_a_stripped_template_would_ship(*, tmp_path: Path) -> None:
    """The lockstep assertion is load-bearing: strip a wiring line and it reports.

    Without this, a predicate that silently reported nothing — a renamed
    parameter, an upstream refactor that stopped reading a file — would leave
    the test above green over a template with the wiring torn out.
    """
    target = tmp_path / "rendered"
    _render_template(target=target)
    justfile = target / JUSTFILE_PATH
    stripped = "\n".join(
        line
        for line in justfile.read_text(encoding="utf-8").splitlines()
        if line != "import? 'dev-tooling/worktree.just'"
    )
    justfile.write_text(stripped, encoding="utf-8")

    gaps = _wiring_gaps_of(tree=target)

    assert "error justfile: import? 'dev-tooling/worktree.just'" in gaps, (
        "removing an `import?` line from the rendered justfile must surface as a "
        f"predicate gap; got: {gaps}"
    )


def test_installation_prompt_names_every_wiring_artifact() -> None:
    """The adopter onboarding surface names each artifact the central row asserts.

    Adopters are outside central enforcement by ratified rule, so the prompt IS
    the wiring's delivery mechanism for them; a literal the prompt never
    mentions is a line an adopter has no way to learn about.
    """
    missing = _literals_missing_from(text=_INSTALLATION_PROMPT.read_text(encoding="utf-8"))

    assert missing == (), (
        f"{_INSTALLATION_PROMPT.relative_to(_REPO_ROOT)} must name every "
        "worktree-pack wiring artifact the `worktree-pack-wired` predicate "
        f"asserts, so an adopter outside central enforcement can wire it; "
        f"unnamed: {missing}"
    )


@pytest.mark.parametrize("dropped", _required_prompt_literals())
def test_prompt_coverage_is_load_bearing_per_wiring_artifact(*, dropped: str) -> None:
    """Each artifact is present, and deleting it alone makes the check report it.

    One case per obligation. The whole-set test above proves the prompt is
    complete TODAY; this proves the assertion would notice each artifact
    individually going away, so no single line can be dropped from the prompt
    later without a red test naming it.
    """
    original = _INSTALLATION_PROMPT.read_text(encoding="utf-8")

    assert dropped in original, f"the installation prompt does not name {dropped!r}"
    assert dropped in _literals_missing_from(text=original.replace(dropped, "")), (
        f"removing {dropped!r} from the installation prompt must be reported as "
        "unnamed; the coverage check is not load-bearing for this artifact"
    )


def test_installation_prompt_is_reachable_from_the_repo() -> None:
    """Guard the path: a moved prompt must fail here, not silently pass on empty bytes."""
    assert _INSTALLATION_PROMPT.is_file(), (
        f"{_INSTALLATION_PROMPT} is the adopter onboarding surface the coverage "
        "test reads; a rename must update this module rather than leave the "
        "coverage assertion reading a file that no longer exists"
    )
