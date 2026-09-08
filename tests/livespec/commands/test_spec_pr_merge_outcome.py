"""The spec-PR gate's outcome, and the effects that record and publish it.

`Decision`, `_blocked`, `_register` and `_publish` were extracted from
`spec_pr_merge_policy.py` so the supervisor drops back under the 200-LLOC soft
ceiling (livespec-n33rwg.2). They are one concern — the outcome, and what the
gate does with it — as distinct from gathering observations
(`_spec_pr_merge_gather`, the impure half) and from the pure rules
(`livespec.spec_governance.pr_merge_derivation`).

`Decision` moved WITH them because `_blocked` and `_register` construct it and
`_publish` consumes it; leaving it behind would have made this module import
from the supervisor that imports it back. It is re-exported from
`spec_pr_merge_policy`, so that module's public API is unchanged.

The rule pinned below is the one worth keeping honest: `_blocked` must fail
CLOSED. A blocked-path constructor that returned `auto` would turn every
unreadable config, failed journal append, and ungoverned edge into a silent
permission to auto-merge.
"""

from __future__ import annotations

import pytest
from livespec.commands._spec_pr_merge_outcome import Decision, _blocked

__all__: list[str] = []


def test_blocked_constructs_a_blocked_decision_not_an_auto_one() -> None:
    """The blocked-path constructor must fail CLOSED."""
    decision = _blocked(reason="config unreadable")
    assert decision.decision == "blocked", (
        "_blocked must construct a blocked verdict; returning 'auto' here would "
        "make every blocked path silently permit auto-merge"
    )


def test_blocked_carries_the_reason_and_claims_no_governing_policy() -> None:
    """A blocked decision names its reason and asserts no policy governed it."""
    decision = _blocked(reason="journal append failed")
    assert decision.reason == "journal append failed"
    assert decision.stems == ()
    assert decision.effective_policy is None
    assert decision.effective_source is None


def test_decision_is_frozen_so_a_verdict_cannot_be_rewritten() -> None:
    """The verdict is immutable once constructed."""
    decision = _blocked(reason="immutable")
    assert isinstance(decision, Decision)
    with pytest.raises((AttributeError, TypeError)):
        decision.decision = "auto"  # type: ignore[misc]
