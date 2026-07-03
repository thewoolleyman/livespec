"""Outside-in + parity test for `dev-tooling/spec_clauses.py`.

`spec_clauses.py` is the single-source-of-truth clause extractor +
gap-id primitive shared across the livespec fleet. This test
covers BOTH the extraction behavior (heading-path scoping, code
fence skipping, keyword matching) AND a frozen gap-id PARITY
vector set.

The parity vectors are the cross-repo drift guard: the SAME
golden ids are asserted by `livespec-orchestrator-beads-fabro`'s vendored-copy
parity test. If a change to the extraction rules or the gap-id
derivation moves any id, both copies' parity tests fail in
lockstep, forcing a coordinated cross-repo change rather than a
silent divergence.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "spec_clauses.py"


def _load_module() -> ModuleType:
    """Import `spec_clauses.py` as a module by file path.

    It lives at `dev-tooling/spec_clauses.py` (a top-level shared
    primitive, not an importable package member), so it is loaded
    via `importlib.util.spec_from_file_location`. Registered in
    `sys.modules` before `exec_module` so its `@dataclass`
    decorator can resolve `cls.__module__`.
    """
    spec = importlib.util.spec_from_file_location("spec_clauses", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Frozen golden parity vectors: (spec_file, heading_path, rule_text) -> gap_id.
# These ids are derived by the impl-beads detector's gap-id function
# at the relocation point and MUST stay byte-identical there.
_GOLDEN_VECTORS: list[tuple[str, str, str, str]] = [
    (
        "contracts.md",
        "Top > Section A",
        "Every reader MUST validate the input.",
        "gap-jpm575mi",
    ),
    (
        "scenarios.md",
        "(top)",
        "Implementations SHOULD prefer the typed API.",
        "gap-bvw44he4",
    ),
    (
        "spec.md",
        "A > B > C",
        "Callers MUST NOT pass null.",
        "gap-3qvhzogi",
    ),
    (
        "constraints.md",
        "Heading",
        "Plugins SHOULD NOT shell out.",
        "gap-zfrssonu",
    ),
]


def test_derive_gap_id_matches_golden_parity_vectors() -> None:
    module = _load_module()
    for spec_file, heading_path, rule_text, expected_gap_id in _GOLDEN_VECTORS:
        actual = module.derive_gap_id(
            spec_file=spec_file,
            heading_path=heading_path,
            rule_text=rule_text,
        )
        assert actual == expected_gap_id, (
            f"gap-id drift for {spec_file!r} / {heading_path!r} / "
            f"{rule_text!r}: got {actual!r}, expected {expected_gap_id!r}"
        )


def test_extract_detects_all_bcp14_keyword_forms() -> None:
    module = _load_module()
    content = (
        "# Top\n\n"
        "## Section A\n\n"
        "Every reader MUST validate the input.\n"
        "Implementations SHOULD prefer the typed API.\n"
        "Callers MUST NOT pass null.\n"
        "Plugins SHOULD NOT shell out.\n"
        "\n"
        "## Section B\n\n"
        "Just a normal paragraph with must in lowercase — no rule.\n"
    )
    rules = module.extract_rules_from_file(spec_file="spec.md", content=content)
    texts = [rule.line_text for rule in rules]
    assert "Every reader MUST validate the input." in texts
    assert "Implementations SHOULD prefer the typed API." in texts
    assert "Callers MUST NOT pass null." in texts
    assert "Plugins SHOULD NOT shell out." in texts
    # Lowercase 'must' must not match.
    assert all("lowercase" not in text for text in texts)


def test_extract_scopes_heading_path_and_skips_code_fences() -> None:
    module = _load_module()
    content = (
        "# Top\n\n"
        "## Outer\n\n"
        "### Inner\n\n"
        "Callers MUST do the thing.\n"
        "\n"
        "```\n"
        "This MUST be ignored — it is inside a fence.\n"
        "```\n"
        "\n"
        "A trailing line with no rule.\n"
    )
    rules = module.extract_rules_from_file(spec_file="spec.md", content=content)
    assert len(rules) == 1
    only = rules[0]
    assert only.heading_path == "Top > Outer > Inner"
    assert only.line_text == "Callers MUST do the thing."
    assert only.gap_id == module.derive_gap_id(
        spec_file="spec.md",
        heading_path="Top > Outer > Inner",
        rule_text="Callers MUST do the thing.",
    )


def test_extract_uses_top_sentinel_when_no_heading() -> None:
    module = _load_module()
    content = "A rule with no heading: callers MUST behave.\n"
    rules = module.extract_rules_from_file(spec_file="spec.md", content=content)
    assert len(rules) == 1
    assert rules[0].heading_path == "(top)"


def test_extract_handles_heading_level_jump() -> None:
    module = _load_module()
    # Jump from H1 straight to H3 — the intermediate H2 slot is a
    # placeholder empty string so deeper rules still scope correctly.
    content = "# Top\n\n### Deep\n\nCallers MUST handle the jump.\n"
    rules = module.extract_rules_from_file(spec_file="spec.md", content=content)
    assert len(rules) == 1
    assert rules[0].heading_path == "Top >  > Deep"
