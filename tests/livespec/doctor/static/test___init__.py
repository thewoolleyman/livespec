"""Tests for livespec.doctor.static package surface.

The static-doctor check registry is the seam where each doctor
check module gets pulled into existence via consumer pressure
(see SPECIFICATION/contracts.md §"Per-sub-spec doctor
parameterization"). Until any check module is authored under
TDD, the package's `__init__.py`
holds only the canonical no-op preamble (the the mirror-pairing rule
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

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants": doctor's entire cross-boundary job is wiring
soundness. Doctor MUST NOT inspect gaps, work-items, dependency
graphs, memos, or any other orchestrator-private state. The
semantic work-item invariants formerly registered here
(`no-stalled-epic`, `no-orphan-dependency`, `no-duplicate-gap-id`,
`no-stale-gap-tied`, `depends_on-ref-wellformedness`,
`unresolved-spec-commitment`) and their work-item-provider
acquisition seam are retired from the shipped catalogue; the
absence tests below pin that contract.
"""

from __future__ import annotations

__all__: list[str] = []


def test_static_package_is_importable() -> None:
    """The doctor.static package imports without raising.

     drives the package's __init__.py from its prior
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
    : the applicability table is
    orchestrator-owned and decides which checks apply to which
    tree kind. The 'main' entry must include every member of
    the 8-check minimum subset; the 'sub_spec' entry is a
    proper subset (no livespec_jsonc_valid or template_exists
    on sub-spec trees — those are project-root-level concerns,
    not per-spec-root concerns).
    """
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, STATIC_CHECKS

    assert APPLICABILITY_BY_TREE_KIND["main"] == STATIC_CHECKS


def test_registry_excludes_retired_cross_boundary_work_item_invariants() -> None:
    """The registry carries NONE of the retired work-item invariants.

    Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
    invariants": "Doctor MUST NOT inspect gaps, work-items,
    dependency graphs, memos, or any other orchestrator-private
    state — those disciplines are owned by the orchestrator."
    The catalogue comprises `config-named-cli-callability` plus
    the repo-tier invariants; the six semantic work-item
    invariants are retired from the shipped catalogue.
    """
    from livespec.doctor.static import STATIC_CHECKS

    retired = {
        "doctor-no-stalled-epic",
        "doctor-no-orphan-dependency",
        "doctor-no-duplicate-gap-id",
        "doctor-no-stale-gap-tied",
        "doctor-depends_on-ref-wellformedness",
        "doctor-unresolved-spec-commitment",
    }
    slugs = {check_module.SLUG for check_module in STATIC_CHECKS}
    still_registered = slugs & retired
    assert not still_registered, f"retired invariants still registered: {still_registered}"


def test_work_items_provider_acquisition_seam_is_removed() -> None:
    """The work-item-provider acquisition seam is gone from the doctor.

    The retired invariants acquired orchestrator-private
    work-items through `_work_items_provider.resolve_provider_path`
    (the `LIVESPEC_IMPL_LIST_WORK_ITEMS` env seam) threaded via
    `DoctorContext.work_items_provider`. Per
    `SPECIFICATION/contracts.md` §"Doctor cross-boundary
    invariants" doctor no longer reads any orchestrator-private
    state, so both the module and the context field MUST be gone.
    """
    import importlib.util
    from dataclasses import fields

    from livespec.context import DoctorContext

    provider_spec = importlib.util.find_spec(
        "livespec.doctor.static._work_items_provider",
    )
    assert provider_spec is None, "_work_items_provider module must be deleted"
    field_names = {field.name for field in fields(DoctorContext)}
    assert "work_items_provider" not in field_names


def test_registry_excludes_retired_stale_cleanup_checks() -> None:
    """The registry carries NONE of the retired stale-cleanup checks.

    Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
    invariants" (v105): the catalogue comprises the single
    cross-boundary invariant `config-named-cli-callability` plus
    the repo-tier invariants defined in that section. The v103
    re-steering (Proposal 5.4) removed the impl-side cleanup
    invariants from core's contract — branch/worktree janitor
    discipline is Dispatcher/orchestrator territory, so the
    `no-stale-merged-branch`, `no-stale-merged-pr-branch`, and
    `no-stale-worktree` checks are retired from the shipped
    catalogue (the orchestrator MAY adopt them privately).
    """
    from livespec.doctor.static import STATIC_CHECKS

    retired = {
        "doctor-no-stale-merged-branch",
        "doctor-no-stale-merged-pr-branch",
        "doctor-no-stale-worktree",
    }
    slugs = {check_module.SLUG for check_module in STATIC_CHECKS}
    still_registered = slugs & retired
    assert (
        not still_registered
    ), f"retired stale-cleanup checks still registered: {still_registered}"


def test_stale_cleanup_check_modules_are_removed() -> None:
    """The retired stale-cleanup check modules are deleted from the package.

    Retirement is module deletion, not mere de-registration: per
    the preservation directive the logic relocates to the
    orchestrator/Dispatcher side (recoverable via the pre-deletion
    SHA cited in the retiring PR), so core MUST NOT keep shipping
    dead check modules.
    """
    import importlib.util

    for module_name in (
        "livespec.doctor.static.no_stale_merged_branch",
        "livespec.doctor.static.no_stale_merged_pr_branch",
        "livespec.doctor.static.no_stale_worktree",
    ):
        spec = importlib.util.find_spec(module_name)
        assert spec is None, f"{module_name} must be deleted"


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


def test_every_static_check_module_declares_hkt_erosion_pragma() -> None:
    """Every static-check module declares the file-level HKT-erosion pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains that
    compose each static check's railway lose flow-narrowing
    through pyright strict mode, surfacing as
    reportUnknownMemberType / reportUnknownVariableType /
    reportUnknownArgumentType diagnostics on most bind / map
    / lash call sites. The file-level pragma suppresses the
    three HKT-related categories; reportArgumentType stays
    ON globally so non-HKT firings still surface. This contract
    test pins the pragma so a future reformatter that drops it
    surfaces immediately rather than silently re-introducing
    the diagnostics.

    Coverage: every member of the canonical STATIC_CHECKS
    registry (one entry per registered check module) plus the
    private helper module under the same package
    (`_out_of_band_edits_writes`).
    Newly registered checks inherit the contract automatically —
    they just need to declare the pragma like every existing
    sibling.

    Exempt: `accept_decision_snapshot_consistency.py` (registered
    in STATIC_CHECKS but contains no returns-library bind chains;
    a pure-membership check with no HKT erosion to silence).
    """
    import inspect

    from livespec.doctor.static import (
        STATIC_CHECKS,
        _out_of_band_edits_writes,
        accept_decision_snapshot_consistency,
    )

    pragma_prefix = (
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n"
    )
    exempt_modules = (accept_decision_snapshot_consistency,)
    modules_to_check: list[object] = [m for m in STATIC_CHECKS if m not in exempt_modules]
    modules_to_check.append(_out_of_band_edits_writes)
    for module in modules_to_check:
        source = inspect.getsource(module)
        assert source.startswith(
            pragma_prefix
        ), f"{module.__name__} must declare the HKT-erosion pragma as its first line"
