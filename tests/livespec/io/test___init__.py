"""Tests for the `livespec.io` package surface.

Mirrors `.claude-plugin/scripts/livespec/io/__init__.py`.
The package's `__init__.py` is a pure-declaration module; its
importability is the load-bearing assertion. This file
additionally pins the li-xxjopf Step 3e file-level HKT-erosion
pragma contract for the three subprocess-driven `io/` modules
that compose returns-library bind chains. The pragma silences
three HKT-related categories at file scope; reportArgumentType
stays ON globally so non-HKT firings still surface.
"""

from __future__ import annotations

__all__: list[str] = []


def test_io_package_is_importable() -> None:
    """The io package imports without raising."""
    from livespec import io

    assert io.__name__ == "livespec.io"


def test_subprocess_driven_modules_declare_hkt_erosion_pragma() -> None:
    """Every subprocess-driven `io/` module declares the HKT-erosion pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains in
    `cli.py`, `gh.py`, and `git.py` lose flow-narrowing through
    pyright's strict mode. The file-level pragma suppresses the
    three HKT-related categories; reportArgumentType stays ON
    globally so non-HKT firings still surface (the HKT-related
    reportArgumentType call sites carry per-line markers). The
    pure `fs.py` and `proc.py` modules are exempt — they do not
    compose returns-library bind chains across HKT boundaries.

    This contract test pins the pragma so a future reformatter
    that drops it surfaces immediately rather than silently
    re-introducing pyright errors.
    """
    import inspect

    from livespec.io import cli, gh, git

    pragma_prefix = (
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n"
    )
    modules_to_check = (cli, gh, git)
    for module in modules_to_check:
        source = inspect.getsource(module)
        assert source.startswith(
            pragma_prefix,
        ), f"{module.__name__} must declare the HKT-erosion pragma as its first line"
