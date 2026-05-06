"""Tests for livespec.doctor.static package surface.

The static-doctor check registry is the v033 D5b second-redo
seam where each Phase-3 / Phase-7 doctor check module gets pulled
into existence via consumer pressure (see PROPOSAL.md
§"`doctor` → Static-phase structure"). Until any
check module is authored under TDD, the package's `__init__.py`
holds only the canonical no-op preamble (the v033 D1
mirror-pairing-rule's `__init__.py` carve-out: a file whose body
is `from __future__ import annotations` + `__all__: list[str] = []`
is exempt from requiring a paired non-trivial test, but the
package itself MUST still be importable for downstream consumers
to see the namespace).

This test pins the importability invariant: `from livespec.doctor
import static` must succeed without raising. Subsequent cycles
that author `livespec/doctor/static/<check_name>.py` modules will
add per-check tests under `tests/livespec/doctor/static/test_
<check_name>.py` (one-to-one mirror pairing) and re-register
each new module in the registry as consumer pressure pulls it in.
"""

from __future__ import annotations

__all__: list[str] = []


def test_static_package_is_importable() -> None:
    """The doctor.static package imports without raising.

    Cycle 103 drives the package's __init__.py from its prior
    Phase-3-aspirational form (which imported eight check modules
    that haven't been re-authored yet under the v033 D5b second
    redo, plus `livespec.context` which doesn't exist) down to a
    consumer-pressure-driven minimum: `from __future__ import
    annotations` + `__all__: list[str] = []`. The smallest
    visible behavior is that the package can be imported at all —
    which the prior file cannot do because every import statement
    in it references an unauthored module.
    """
    from livespec.doctor import static

    assert static.__name__ == "livespec.doctor.static"


def test_applicability_by_tree_kind_maps_main_to_all_eight_checks() -> None:
    """APPLICABILITY_BY_TREE_KIND['main'] enumerates every Phase-3 check.

    Per Plan
    Phase 3: the applicability table is
    orchestrator-owned and decides which checks apply to which
    tree kind. The 'main' entry must include every member of
    the 8-check minimum subset; the 'sub_spec' entry is a
    proper subset (no livespec_jsonc_valid or template_exists
    on sub-spec trees — those are project-root-level concerns,
    not per-spec-root concerns).
    """
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, STATIC_CHECKS

    assert APPLICABILITY_BY_TREE_KIND["main"] == STATIC_CHECKS
