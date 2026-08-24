"""Mirror-paired test for the doctor static-check registry initializer.

Per SPECIFICATION/spec.md "Spec-tree path closure": this covers the
`doctor-spec-tree-manifested` registry entry this ratification adds,
so the registry membership this file's `STATIC_CHECKS`/
`APPLICABILITY_BY_TREE_KIND` declares is itself under test, not only
exercised incidentally by `test_run_static.py`.
"""

from __future__ import annotations

from livespec.doctor.static import (
    APPLICABILITY_BY_TREE_KIND,
    STATIC_CHECKS,
    spec_tree_manifested,
)

__all__: list[str] = []


def test_spec_tree_manifested_is_registered_in_static_checks() -> None:
    """The new check is a member of the explicit STATIC_CHECKS registry."""
    assert spec_tree_manifested in STATIC_CHECKS


def test_spec_tree_manifested_applies_to_the_main_tree_only() -> None:
    """The check applies to the main tree; sub-spec trees carry no manifest."""
    assert spec_tree_manifested in APPLICABILITY_BY_TREE_KIND["main"]
    assert spec_tree_manifested not in APPLICABILITY_BY_TREE_KIND["sub_spec"]
