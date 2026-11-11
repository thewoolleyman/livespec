"""Purity declarations for every member of the repository check aggregate."""

from __future__ import annotations

import re
from pathlib import Path

from livespec_dev_tooling.check_purity import audit_check_purity
from returns.pipeline import is_successful
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


_ROOT = Path(__file__).resolve().parents[1]
_JUSTFILE = _ROOT / "justfile"
_INVENTORY = _ROOT / "check-targets.txt"


def _aggregate_targets(*, justfile: str) -> tuple[str, ...]:
    """Read the literal members of the root ``check`` aggregate in order."""
    matched = re.search(
        r"^check:\n(?P<body>(?:    .*\n)+?)    \)\n    failed=", justfile, re.MULTILINE
    )
    assert matched is not None, "root check aggregate no longer has its literal targets array"
    return tuple(re.findall(r"^        ([a-z0-9-]+)$", matched.group("body"), re.MULTILINE))


def test_aggregate_members_are_declared_and_refuse_undeclared_members() -> None:
    """The aggregate audits its whole set before dispatching any member."""
    justfile = _JUSTFILE.read_text(encoding="utf-8")
    targets = _aggregate_targets(justfile=justfile)
    assert _INVENTORY.is_file(), "check purity needs the repository check-targets inventory"
    audit = audit_check_purity(targets=targets, repo_root=_ROOT)
    assert is_successful(audit), f"malformed check purity declaration: {audit!r}"
    declared = unsafe_perform_io(audit.unwrap())
    assert not declared.undeclared, f"undeclared aggregate members: {declared.undeclared!r}"

    guard = 'uv run python -m livespec_dev_tooling.green_token undeclared "${targets[@]}"'
    assert guard in justfile, "the check aggregate must refuse an undeclared member"
    assert justfile.index(guard) < justfile.index(
        'for t in "${targets[@]}"; do'
    ), "the purity declaration audit must run before the aggregate dispatches members"
