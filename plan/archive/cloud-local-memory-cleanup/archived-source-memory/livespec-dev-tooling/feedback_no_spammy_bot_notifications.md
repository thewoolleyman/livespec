---
name: feedback-no-spammy-bot-notifications
description: User dislikes cron-driven PR-comment / Slack-ping / label-spam style notifications; prefers on-demand surfacing inside user-invoked tooling
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0c6ae44c-5d78-4af5-bfdd-887a7ea2baaa
---

Don't propose periodic-cron workflows that act on PRs/issues by posting
comments, applying labels, or pinging authors as the primary signaling
mechanism. The user views this as spam pattern, especially for solo /
small-team workflows where the same human is on both sides of the PR.

**Why**: Said directly on 2026-05-26 when reviewing the
mechanical-enforcement RCA for stale spec-revise branches. The user
specifically rejected a "Layer 3" proposal that involved a daily
stale-spec-branch-sweep.yml workflow posting comments / applying
stale-spec-branch labels / pinging authors. Quote: "That seems like
it will be spammy. … notifying users is not a good option."

**How to apply**:
- Default preference is to surface status via on-demand tooling the
  user invokes (e.g., doctor's LLM-driven phase querying `gh pr list`
  and reporting findings inside the session) rather than periodic
  cron jobs that produce side effects.
- "Notify the user" is NOT a satisfactory mechanical enforcement —
  the user wants the tooling to either (a) prevent the bad state
  (skill-level refusal), (b) clear it automatically (auto-merge once
  CI is green), or (c) surface it inside a tool the user is already
  running.
- Bot comments / labels / pings on PRs and issues are reserved for
  cases where the audience is genuinely external (e.g., reviewer
  on a multi-author PR) — not for self-directed reminders.
- The exception is the existing `release-please` and
  `auto-enable-merge.yml` machinery, which the user has accepted
  because they integrate with the release flow rather than being
  pure-notification surfaces.
