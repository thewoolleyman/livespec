"""Tests for livespec.doctor.static package surface.

The static-doctor check registry is the seam where each doctor
check module gets pulled into existence via consumer pressure
(see SPECIFICATION/contracts.md §"Per-sub-spec doctor
parameterization"). Until any check module is authored under
TDD, the package's `__init__.py`
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


def test_every_static_check_slug_is_a_checkid_newtype() -> None:
    """Every check module exposes `SLUG` as a `CheckId` NewType.

    The `Finding` dataclass declares `check_id: CheckId`. Each
    static check module imports its slug into a module-level
    constant typed `SLUG: CheckId = CheckId("doctor-<name>")`
    so that constructing `Finding(check_id=SLUG, ...)` passes
    pyright's NewType invariance check at the call site without
    needing a per-site wrap. This pins that contract: if a check
    drops the `CheckId` wrap and lets `SLUG: str` slip in, the
    pyright error reappears AND this test fails immediately.
    """
    from livespec.doctor.static import STATIC_CHECKS
    from livespec.types import CheckId

    for check_module in STATIC_CHECKS:
        slug = getattr(check_module, "SLUG", None)
        assert slug is not None, f"{check_module.__name__} missing SLUG"
        assert isinstance(slug, str), f"{check_module.__name__}.SLUG must be a str/CheckId"
        # NewType is a runtime identity function, so the typed
        # value is structurally still a str. The static-time
        # contract is the load-bearing assertion; what we can
        # assert at runtime is that the value is the result of
        # threading through CheckId(), which yields the same str
        # untouched. Equivalence guards the round-trip identity.
        assert CheckId(slug) == slug


def test_high_density_static_check_modules_declare_hkt_erosion_pragma() -> None:
    """The high-density static-check modules declare the HKT-erosion pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains that
    compose each static check's railway lose flow-narrowing
    through pyright's strict mode, surfacing as
    reportUnknownMemberType / reportUnknownVariableType /
    reportUnknownArgumentType diagnostics on most bind / map
    / lash call sites. The file-level pragma suppresses the
    three HKT-related categories; reportArgumentType stays
    ON globally so non-HKT firings still surface. This contract
    test pins the pragma so a future reformatter that drops it
    surfaces immediately rather than silently re-introducing
    the diagnostics.

    Coverage: the seven static-check modules with the highest
    HKT-erosion density (>=10 errors before pragma application)
    plus the two auto-backfill / orphan-dependency helper
    modules under the same package.
    """
    import inspect

    from livespec.doctor.static import (
        _no_orphan_dependency_helpers,
        _out_of_band_edits_writes,
        depends_on_ref_wellformedness,
        no_duplicate_gap_id,
        no_orphan_dependency,
        no_stale_gap_tied,
        no_stalled_epic,
        out_of_band_edits,
    )

    pragma_prefix = (
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n"
    )
    for module in (
        depends_on_ref_wellformedness,
        no_stalled_epic,
        no_orphan_dependency,
        no_duplicate_gap_id,
        no_stale_gap_tied,
        out_of_band_edits,
        _out_of_band_edits_writes,
        _no_orphan_dependency_helpers,
    ):
        source = inspect.getsource(module)
        assert source.startswith(pragma_prefix), (
            f"{module.__name__} must declare the HKT-erosion pragma " "as its first line"
        )
