"""The coverage policy measures first-party source and omits the test modules.

The fleet coverage policy excludes test scaffolding through an omit-only blocklist.
Measuring `tests/` made test modules a 100% per-file coverage subject, so an
untouched test module could refuse the gate (livespec-luesll, the fleet sweep that
followed bd-ib-hjo7lb).
"""

from pathlib import Path

from coverage import Coverage
from coverage.files import GlobMatcher, prep_patterns

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _omit_matcher(*, monkeypatch) -> GlobMatcher:
    monkeypatch.chdir(_REPO_ROOT)
    config = Coverage(config_file=str(_REPO_ROOT / "pyproject.toml")).config
    return GlobMatcher(prep_patterns(config.run_omit or []), "omit")


def test_coverage_omits_test_modules(monkeypatch) -> None:
    matcher = _omit_matcher(monkeypatch=monkeypatch)

    assert matcher.match(str(_REPO_ROOT / "tests" / "test_some_module.py"))
    assert matcher.match(str(_REPO_ROOT / "tests" / "bin" / "test_deep_module.py"))
    assert matcher.match(str(_REPO_ROOT / "tests" / "support" / "helper_module.py"))


def test_coverage_still_measures_first_party_source(monkeypatch) -> None:
    matcher = _omit_matcher(monkeypatch=monkeypatch)
    source = _REPO_ROOT / ".claude-plugin" / "scripts" / "livespec"

    assert not matcher.match(str(source / "some_module.py"))
    assert not matcher.match(str(_REPO_ROOT / "dev-tooling" / "checks" / "some_check.py"))
