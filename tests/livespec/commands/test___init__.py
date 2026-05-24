"""Tests for the `livespec.commands` package surface.

Mirrors `.claude-plugin/scripts/livespec/commands/__init__.py`.
The package's `__init__.py` is a pure-declaration module
(docstring + `__all__: list[str] = []`); its importability is
the load-bearing assertion. This file additionally pins the
li-xxjopf Step 3e file-level HKT-erosion pragma contract for
the seven private helper modules under `commands/` that
compose returns-library bind chains. The pragma silences three
HKT-related categories at file scope; reportArgumentType stays
ON globally so non-HKT firings still surface. The contract test
pins the pragma so a future reformatter that drops it surfaces
immediately rather than silently re-introducing the diagnostics.
"""

from __future__ import annotations

__all__: list[str] = []


def test_commands_package_is_importable() -> None:
    """The commands package imports without raising."""
    from livespec import commands

    assert commands.__name__ == "livespec.commands"


def test_private_helper_modules_declare_hkt_erosion_pragma() -> None:
    """Every private helper module under `commands/` declares the HKT-erosion pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains that
    compose each helper's railway lose flow-narrowing through
    pyright's strict mode, surfacing as reportUnknownMemberType /
    reportUnknownVariableType / reportUnknownArgumentType
    diagnostics on most bind / map / lash call sites. The
    file-level pragma suppresses the three HKT-related categories;
    reportArgumentType stays ON globally so non-HKT firings still
    surface. This contract test pins the pragma so a future
    reformatter that drops it surfaces immediately rather than
    silently re-introducing the diagnostics.

    Coverage: the seven `commands/_*.py` helper modules. Newly
    added private helpers under `commands/` should declare the
    pragma like every existing sibling and add themselves to
    the explicit tuple below.
    """
    import inspect

    from livespec.commands import (
        _prune_history_railway,
        _revise_helpers,
        _revise_railway_emits,
        _revise_validation,
        _seed_railway_emits,
        _seed_railway_emits_per_tree,
        _seed_railway_writes,
    )

    pragma_prefix = (
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n"
    )
    modules_to_check = (
        _prune_history_railway,
        _revise_helpers,
        _revise_railway_emits,
        _revise_validation,
        _seed_railway_emits,
        _seed_railway_emits_per_tree,
        _seed_railway_writes,
    )
    for module in modules_to_check:
        source = inspect.getsource(module)
        assert source.startswith(
            pragma_prefix,
        ), f"{module.__name__} must declare the HKT-erosion pragma as its first line"
