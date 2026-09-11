"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Error path — ratification review blocks
mutation" end-to-end over the shipped `effective_ratification_review`
resolver, the `awaits_ratification_review` attention predicate, and the
shipped `.livespec.jsonc` parser, so each scenario is driven through
real config text and the production resolution path:

- Blocking or invalid review evidence prevents ratification — a blocking
  verdict, an unavailable reviewer, and an unconfigured reviewer model
  each keep `awaits_ratification_review` true and refuse to mutate.
- All-defaults behavior retains manual independent review — with the
  `spec_governance` block absent the review still awaits maintainer
  evidence; with a reviewer model configured the effective mode resolves
  to the `manual-spawn` default and STILL awaits evidence.

POSITIVE CONTROL: matching `NO BLOCKERS` evidence passes the floor
(`awaits_ratification_review` false), proving the blocking pins are not
vacuously always-true.
"""

from __future__ import annotations

import pytest
from livespec.spec_governance.config import parse_config_text
from livespec.spec_governance.effective import (
    RatificationContext,
    awaits_ratification_review,
    effective_ratification_review,
)

__all__: list[str] = []

pytestmark = pytest.mark.integration

_WITH_MODEL = '{"spec_governance": {"ratification_reviewer_model": "fable"}}'


def test_no_blockers_evidence_passes_the_review_floor() -> None:
    """POSITIVE CONTROL: matching no-blockers evidence needs no maintainer."""
    config = parse_config_text(text=_WITH_MODEL).effective

    policy = effective_ratification_review(
        config=config,
        context=RatificationContext(no_blockers_evidence=True),
    )

    assert not awaits_ratification_review(policy=policy)
    assert policy.source == "hard-floor"


def test_blocking_or_invalid_evidence_prevents_ratification() -> None:
    """A blocker, an unavailable reviewer, and no model each await input."""
    config = parse_config_text(text=_WITH_MODEL).effective
    unconfigured = parse_config_text(text="{}").effective

    blocked = effective_ratification_review(
        config=config, context=RatificationContext(blockers_present=True)
    )
    reviewer_gone = effective_ratification_review(
        config=config, context=RatificationContext(reviewer_unavailable=True)
    )
    no_model = effective_ratification_review(config=unconfigured, context=RatificationContext())

    for policy in (blocked, reviewer_gone, no_model):
        assert awaits_ratification_review(policy=policy)
        assert policy.value is None


def test_all_defaults_retain_manual_independent_review() -> None:
    """Defaults await evidence; a configured model resolves to manual-spawn."""
    defaults = parse_config_text(text="{}").effective
    with_model = parse_config_text(text=_WITH_MODEL).effective

    defaults_policy = effective_ratification_review(config=defaults, context=RatificationContext())
    model_policy = effective_ratification_review(config=with_model, context=RatificationContext())

    assert awaits_ratification_review(policy=defaults_policy)
    assert with_model.ratification_review == "manual-spawn"
    assert model_policy.value == "manual-spawn"
    assert model_policy.source == "default"
    assert awaits_ratification_review(policy=model_policy)
