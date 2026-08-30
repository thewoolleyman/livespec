"""Compatibility imports for runtime-owned default-block verification.

The relocated surface is `livespec_runtime.spec_governance`; this module keeps
the old core import path that formerly housed
`livespec_runtime.spec_governance.default_block` behavior.
"""

from __future__ import annotations

from livespec_runtime.spec_governance import (
    BlockDrift,
    BlockVerification,
    UnterminatedGovernanceBlockError,
    documented_defaults,
    verify_default_block,
)

__all__: list[str] = [
    "BlockDrift",
    "BlockVerification",
    "UnterminatedGovernanceBlockError",
    "documented_defaults",
    "verify_default_block",
]
