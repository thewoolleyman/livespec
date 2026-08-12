"""Effective spec pull-request merge policy resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.result import Failure

from livespec.parse.front_matter import parse_front_matter
from livespec.spec_governance.config import SpecGovernanceConfig
from livespec.spec_governance.policy import EffectivePolicy, Source

__all__: list[str] = [
    "SPEC_ROOT",
    "awaits_manual_spec_pr_merge",
    "effective_spec_pr_merge",
]

# The spec root this resolver folds over. Public because the spec pull-request
# merge gate must derive its stems from the SAME root the fold reads them
# under; two copies of the literal would drift into a gate that resolves
# proposals it never derived.
SPEC_ROOT = "SPECIFICATION"
_OVERRIDE_KEY = "spec_pr_merge_policy"
_AUTO = "auto-on-green"
_MANUAL = "manual"
_ALLOWED = {_AUTO, _MANUAL}


def effective_spec_pr_merge(
    *,
    project_root: Path,
    config: SpecGovernanceConfig,
    proposal_stems: tuple[str, ...],
) -> EffectivePolicy:
    """Resolve the pull-request conservative fold for caller-supplied stems."""
    if proposal_stems == ():
        return _manual(source="default", reason="empty proposal-stem set resolves safely to manual")
    policies = [
        _single_proposal_policy(
            spec_root=project_root / SPEC_ROOT,
            config=config,
            proposal_stem=stem,
        )
        for stem in proposal_stems
    ]
    if any(policy.value == _MANUAL for policy in policies):
        return _manual(
            source=_manual_source(policies=tuple(policies)),
            reason="one or more proposal policies resolve to manual",
        )
    return EffectivePolicy(
        value=_AUTO,
        source=_auto_source(policies=tuple(policies)),
        requires_input=False,
        reason="every proposal policy resolves to auto-on-green",
    )


def awaits_manual_spec_pr_merge(*, policy: EffectivePolicy) -> bool:
    """Return true while the pull-request merge policy requires manual handling."""
    return policy.value == _MANUAL or policy.requires_input


def _single_proposal_policy(
    *,
    spec_root: Path,
    config: SpecGovernanceConfig,
    proposal_stem: str,
) -> EffectivePolicy:
    matches = tuple(sorted(spec_root.glob(f"history/*/proposed_changes/{proposal_stem}.md")))
    if matches == ():
        return _manual(source="default", reason="proposal stem matched no history files")
    policies = tuple(_proposal_file_policy(path=path, config=config) for path in matches)
    if any(policy.value == _MANUAL for policy in policies):
        return _manual(
            source=_manual_source(policies=policies),
            reason="one or more matching history files resolve to manual",
        )
    return EffectivePolicy(
        value=_AUTO,
        source=_auto_source(policies=policies),
        requires_input=False,
        reason="every matching history file resolves to auto-on-green",
    )


def _proposal_file_policy(*, path: Path, config: SpecGovernanceConfig) -> EffectivePolicy:
    parsed = parse_front_matter(text=path.read_text(encoding="utf-8"))
    if isinstance(parsed, Failure):
        return _manual(source="proposal", reason="proposal front matter is malformed")
    front_matter = parsed.unwrap()
    override = front_matter.get(_OVERRIDE_KEY)
    if override is not None:
        return _override_policy(value=override)
    source: Source = "global" if config.spec_pr_merge != _MANUAL else "default"
    return EffectivePolicy(
        value=config.spec_pr_merge,
        source=source,
        requires_input=config.spec_pr_merge == _MANUAL,
        reason="resolved from global policy or safe default",
    )


def _override_policy(*, value: Any) -> EffectivePolicy:
    if not isinstance(value, str) or value not in _ALLOWED:
        return _manual(
            source="proposal", reason="invalid proposal override resolves safely to manual"
        )
    return EffectivePolicy(
        value=value,
        source="proposal",
        requires_input=value == _MANUAL,
        reason="resolved from proposal front matter",
    )


def _manual(*, source: Source, reason: str) -> EffectivePolicy:
    return EffectivePolicy(value=_MANUAL, source=source, requires_input=True, reason=reason)


def _manual_source(*, policies: tuple[EffectivePolicy, ...]) -> Source:
    for source in ("proposal", "global"):
        if any(policy.value == _MANUAL and policy.source == source for policy in policies):
            return source
    return "default"


def _auto_source(*, policies: tuple[EffectivePolicy, ...]) -> Source:
    if any(policy.source == "proposal" for policy in policies):
        return "proposal"
    return "global"
