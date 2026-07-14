# Memory index

- [Revise payload format gotchas](feedback_revise_payload_format.md) — one decision per FILE, paths relative to spec-target, errors silent without IOResult tracing
- [livespec commit-prefix rules](feedback_livespec_commit_prefixes.md) — livespec + impl-plaintext enforce red-green-replay; use ci/chore/docs not feat for non-product changes
- [Heading-coverage pairing](feedback_heading_coverage_pairing.md) — new H2 in SPECIFICATION/*.md requires tests/heading-coverage.json entry in the same commit
- [Cross-repo coordination project](project_livespec_sibling_family_cross_repo_coordination.md) — 4-repo livespec family + the automation surface that pin-bumps them, owned by dev-tooling
- [livespec 1Password setup](reference_livespec_1password_setup.md) — where the livespec-pr-bot App credentials live (1P env fufpvkvatwkmqjzvilvfnemsue) + how to retrieve them around the uutils-env-`--` bug
- [Reference-discipline gap in-flight](project_reference_discipline_in_flight.md) — no invariant covers cross-spec §"…" refs or code-side §"…" citations as of 2026-05-25; propose-change filed upstream
- [No spammy bot notifications](feedback_no_spammy_bot_notifications.md) — user rejects cron-driven PR-comment / label-spam patterns; prefer on-demand surfacing in user-invoked tools (e.g., doctor)
- [L2 tenant migration runbook](project_l2_tenant_migration_runbook.md) — work-item-lifecycle L2 thin migration: cwd-selected tenant, live-only rank backfill via legacy_seed, lossless metadata merge; dev-tooling DONE (epic l2sm, PR #228)
