"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Error path — authoring batch input requires
attention" end-to-end over the shipped authoring-mode resolvers
(`effective_propose_change_mode` / `effective_critique_mode`) and the
shipped `.livespec.jsonc` parser (`parse_config_text`), so the two
scenarios in that section are exercised against real config text and
the production resolution path rather than a hand-built stub:

- Incomplete or conflicting batch authoring does not mutate — a
  contradictory envelope and an incomplete batch envelope each escalate
  to human attention (`requires_input` true, `hard-floor` source).
- Invalid settings preserve interactive safety — malformed config text
  and a missing `spec_governance` block both resolve to the interactive
  default that requires input.

Each pin carries a POSITIVE CONTROL that makes the SAME resolver return
`requires_input=False` (a complete batch envelope proceeds unattended),
so the attention pin is proven non-vacuous rather than always-true.
"""

from __future__ import annotations

import pytest
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.effective import (
    effective_critique_mode,
    effective_propose_change_mode,
    requires_critique_input,
    requires_propose_change_input,
)

__all__: list[str] = []

pytestmark = pytest.mark.integration


def test_contradictory_batch_envelope_escalates_to_attention() -> None:
    """A contradictory envelope requires human attention before any mutation."""
    config = parse_config_text(
        text='{"spec_governance": {"propose_change_mode": "batch"}}'
    ).effective

    contradictory = effective_propose_change_mode(
        config=config,
        invocation_mode="batch",
        contradictory_envelope=True,
    )
    critique_contradictory = effective_critique_mode(
        config=parse_config_text(text='{"spec_governance": {"critique_mode": "batch"}}').effective,
        invocation_mode="batch",
        contradictory_envelope=True,
    )

    assert requires_propose_change_input(policy=contradictory)
    assert contradictory.source == "hard-floor"
    assert contradictory.value is None
    assert requires_critique_input(policy=critique_contradictory)
    assert critique_contradictory.source == "hard-floor"


def test_incomplete_batch_envelope_escalates_to_attention() -> None:
    """An incomplete batch envelope requires human attention.

    POSITIVE CONTROL: the SAME resolver with a complete batch envelope
    returns `requires_input=False`, proving the pin is not always-true.
    """
    config = parse_config_text(
        text='{"spec_governance": {"propose_change_mode": "batch"}}'
    ).effective

    incomplete = effective_propose_change_mode(
        config=config,
        invocation_mode="batch",
        batch_complete=False,
    )
    complete = effective_propose_change_mode(
        config=config,
        invocation_mode="batch",
        batch_complete=True,
    )

    assert requires_propose_change_input(policy=incomplete)
    assert incomplete.value is None
    # POSITIVE CONTROL: a complete batch envelope proceeds unattended.
    assert not requires_propose_change_input(policy=complete)
    assert complete.value == "batch"


def test_invalid_or_missing_settings_default_to_interactive_attention() -> None:
    """Malformed config and a missing block both keep interactive safety."""
    malformed = parse_config_text(text="{ this is not json ")
    missing_block = parse_config_text(text="{}")

    malformed_policy = effective_propose_change_mode(config=malformed.effective)
    missing_policy = effective_critique_mode(config=missing_block.effective)

    assert malformed.diagnostics
    assert malformed_policy.value == "interactive"
    assert requires_propose_change_input(policy=malformed_policy)
    assert missing_policy.value == "interactive"
    assert requires_critique_input(policy=missing_policy)
