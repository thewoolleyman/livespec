"""Authoring-mode policy resolution, extracted from `effective`.

Holds `_authoring_mode` -- the shared resolver behind both the
propose-change and critique modes -- together with `_input`, the
hard-floor constructor that every escalating branch in the effective
policy family returns.

`_input` moves here with its only structural dependant rather than
staying behind: `effective` imports both back, and nothing here imports
from `effective`, so the dependency is one-way and the two cannot form a
cycle. Both depend only on the `policy` value types, which sit outside
either module.
"""

from __future__ import annotations

from livespec.spec_governance.policy import EffectivePolicy, Source

__all__: list[str] = [
    "_authoring_mode",
    "_input",
]


def _authoring_mode(
    *,
    global_value: str,
    invocation_mode: str | None,
    contradictory_envelope: bool,
    batch_complete: bool,
) -> EffectivePolicy:
    if contradictory_envelope:
        return _input(reason="internally contradictory envelope requires escalation")
    if invocation_mode == "batch" and not batch_complete:
        return _input(reason="batch mode is incomplete")
    if invocation_mode is not None:
        return EffectivePolicy(
            value=invocation_mode,
            source="invocation",
            requires_input=invocation_mode == "interactive",
            reason="invocation mode supplied",
        )
    return EffectivePolicy(
        value=global_value,
        source="global" if global_value != "interactive" else "default",
        requires_input=global_value == "interactive",
        reason="resolved from global policy or safe default",
    )


def _input(*, reason: str, source: Source = "hard-floor") -> EffectivePolicy:
    return EffectivePolicy(value=None, source=source, requires_input=True, reason=reason)
