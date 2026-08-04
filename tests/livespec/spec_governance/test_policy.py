"""Tests for the shared effective-policy value."""

from livespec.spec_governance.policy import EffectivePolicy

__all__: list[str] = []


def test_effective_policy_preserves_resolution_fields() -> None:
    policy = EffectivePolicy(
        value="delegated",
        source="global",
        requires_input=False,
        reason="exact evidence",
    )

    assert policy.value == "delegated"
    assert policy.source == "global"
    assert not policy.requires_input
    assert policy.reason == "exact evidence"
