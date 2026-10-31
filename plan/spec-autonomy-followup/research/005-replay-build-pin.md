# 005 — The replay must install v0.44.3, and the fixture kit no longer does

Written 2026-10-31 by Claude Code session `spec-autonomy-followup` (plan owner, resumed while
bd-ib-r2ci3q is in its factory run). This note records a problem the independent replay will hit,
the evidence for it, and the routes out of it. Nothing here has been run as proof yet.

## The problem

The plan's recorded next action carries a typed required result: a `verified` plan Proof of Done
record naming build **v0.44.3** and covering all five Definition of Done assertions. That build name
sits in the epic's authority chain and cannot be renamed while the result is unmet.

The fixture kit (`fixture/build-and-run.sh`, note 004) installs core and the Claude Driver from the
marketplaces declared in the host's **user** settings. Both track the `release` ref. On 2026-10-31
core's `release` branch is **v0.45.0** (commit `5b7c55a0`), so a replay that runs the kit as written
now exercises v0.45.0. It could not honestly name v0.44.3, so its record could not satisfy the
required result.

The Claude Driver is unaffected: its `release` branch is still v0.12.1 (`0a3e2f78`).

## Evidence that the two core builds are the same artifact apart from the version number

`git diff --stat v0.44.3 v0.45.0 -- .claude-plugin` in thewoolleyman/livespec shows exactly two
changed lines: the `version` field of `.claude-plugin/plugin.json` and of
`.claude-plugin/.codex-plugin/plugin.json`. The revise prose, the CLIs and the templates are
byte-identical. So a replay on v0.45.0 would test the same behaviour, but under the wrong name.

## What was tested

In an isolated, throwaway `CLAUDE_CONFIG_DIR` (a scratch directory, deleted afterwards), the command
`claude plugin marketplace add 'thewoolleyman/livespec#v0.44.3'` succeeded. `marketplace list`
reported `GitHub (thewoolleyman/livespec@v0.44.3)`, the clone described itself as `v0.44.3`, and its
`plugin.json` read `"version": "0.44.3"`. So the normal installation path can pin a tag, as long as
no user-level `livespec` marketplace tracking `release` takes precedence.

What was NOT tested: authenticating the headless `claude -p` probe runs inside that isolated
directory. The host has no `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` in the environment. Its
only credential is `~/.claude/.credentials.json`, an OAuth login that caam rotates between accounts.
Copying that file into a second config directory would duplicate a refresh token. That is secret
handling the plan owner did not do without maintainer authorization.

## Measured: pinning at project scope does not work while the user scope tracks `release`

At the coordinator's request, the route that needs no new credential was tried on 2026-10-31. It used
a throwaway project directory and the DEFAULT `CLAUDE_CONFIG_DIR`, so the existing login was used in
place.

- A project `.claude/settings.json` declared marketplace `livespec` at ref `v0.44.3` and enabled
  `livespec@livespec`. Then `claude plugin install livespec@livespec -s project` ran there. The
  installation record showed version `0.45.0`, gitCommitSha `5b7c55a0`: the user-scope marketplace at
  `release` won silently.
- `claude plugin marketplace add 'thewoolleyman/livespec#v0.44.3' --scope project` was refused:
  `Cannot add marketplace "livespec": its source doesn't match its extraKnownMarketplaces entry in
  user or managed settings; add it from the source that entry lists, or change the entry.`

Afterwards the throwaway install was removed. The installation record was identical to its
pre-test snapshot, and the shared marketplace still tracked `release` at v0.45.0. So the build can
be pinned only in a config directory with no user-scope `livespec` entry, which brings back the
authentication question below.

## Routes, in recommended order

1. **Recommended: an isolated config directory with its own long-lived token.** The maintainer runs
   `claude setup-token` once, and the token is injected through the 1Password Environment wrapper.
   The replayer then runs a copy of the kit with `CLAUDE_CONFIG_DIR` pointing at a fresh scratch
   directory, after
   `claude plugin marketplace add 'thewoolleyman/livespec#v0.44.3'` and
   `claude plugin marketplace add 'thewoolleyman/livespec-driver-claude#v0.12.1'`. That is the
   released artifact installed through its normal path, at the build the required result names,
   with no change to the host's user settings and no copy of a rotating credential.
2. **Copy the OAuth credentials file into the isolated directory.** This works mechanically, but it
   risks invalidating the caam-managed login when either copy refreshes. Use it only with the
   maintainer's explicit authorization.
3. **Not available: replay on v0.45.0.** The build name in the required result is locked, and the
   evidence above only shows the two artifacts are equivalent. It does not make a v0.45.0 record
   name v0.44.3.

Assertions 1, 2 and 3 do not need the fixture. On 2026-10-31 the plan owner re-checked them against
the `release` branches: the core revise wording is present at both v0.44.3 and v0.45.0; the three
Driver bindings at v0.12.1, v0.8.4 and v0.6.2 carry the "Accept, modify, or reject" description and
the "requires maintainer input" scoping sentence, and name no reviewer model; and the
livespec-orchestrator-beads-fabro `release` branch (v0.264.6, `4f5caa8fd`) carries "its linked
proposal to ratify" in `_spec_change_tier_wall.py` (blob `a11f0a9f`) and
`_dispatcher_loop_candidates.py` (blob `af0a0f5c`). That release's
`tests/livespec_orchestrator_beads_fabro/commands/test_spec_change_tier_wall.py`, run against an
extracted copy of the release tree, passed all 10 tests, including
`test_the_wall_refuses_a_held_item_with_exit_five_naming_its_topic`.
