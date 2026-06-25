#!/usr/bin/env bash
# branch-protection.sh — the SERVER-SIDE mirror of the worktree-only commit
# discipline. The local commit-refuse hook blocks commits on the
# primary checkout, but it is LOCALLY BYPASSABLE (`git commit --no-verify`, or
# simply never installed). GitHub branch
# protection is the server-enforced backstop: the default branch advances only
# via PR/merge, and direct/force pushes to it are rejected by GitHub itself.
#
# Generated from
# livespec/templates/impl-plugin/dev-tooling/branch-protection.sh at
# copier-copy time; re-sync via `copier update --vcs-ref=master` when livespec
# publishes a new release.
#
# The worktree concern's five conformance slots
# (research/factory-conformance/cross-repo-conformance-pattern.md), server side:
#   CONTRACT   the default branch advances only via PR/merge; direct + force
#              pushes are rejected.
#   MECHANISM  GitHub branch protection (the existing primitive — no bespoke
#              per-repo detection workflow).
#   INSTALLER  `just protect-default-branch`  -> this script's `apply` verb.
#   VERIFIER   `just check-branch-protection`  -> this script's `check` verb
#              (the "tripwire").
#   EXEMPTION  the LIVESPEC_BRANCH_PROTECTION_CHECK severity lever (below) — an
#              EXPLICIT, DECLARED opt-out; the default is fail-closed.
#
# FAIL-CLOSED, CAPABILITY-AWARE.  Reading/applying protection needs (a) the `gh`
# CLI authenticated and (b) an ADMIN-scoped token (the branch-protection API
# requires admin). Those exist in the Fleet-time conformance/orchestrator tier —
# where the authoritative bite belongs — but NOT in every `just check` context
# (local pre-push hooks and CI matrix jobs typically lack an admin token). So:
#   - protection MISSING / too weak, observed WITH admin access  -> TRIP (exit 1)
#   - genuine capability gap (no gh / no admin / non-GitHub origin) -> SKIP with a
#     NAMED notice (honest "unknown" — NOT a silent pass; the Fleet-time tier
#     with an admin token is authoritative).
# Skipping when you genuinely cannot observe is not fail-open: fail-open would be
# "protection missing but I pass." This names the gap loudly instead of crashing
# the aggregate or lying about coverage.
#
# SEVERITY LEVER (the one self-documenting carve-out, mirroring the template's
# other env-levered checks): LIVESPEC_BRANCH_PROTECTION_CHECK
#   fail (default) | warn | skip
# The conformance/orchestrator job leaves it at `fail`; an environment that
# legitimately cannot enforce sets it explicitly. This is the DECLARED
# exemption — the default is fail-closed.

set -euo pipefail

severity="${LIVESPEC_BRANCH_PROTECTION_CHECK:-fail}"

# Resolved by resolve_repo / resolve_default_branch (globals, NOT command
# substitution: skip_unknown/trip call `exit`, which only unwinds a `$(...)`
# subshell — so these resolvers must run in the script's own process, set a
# global, and be invoked directly from the verb functions).
RESOLVED_REPO=""
RESOLVED_BRANCH=""

note() { printf 'branch-protection: %s\n' "$1" >&2; }

# A capability gap — we cannot observe/act. Name it; do not fail.
skip_unknown() {
    note "SKIP (unknown) — $1"
    note "  the authoritative verdict comes from the conformance/orchestrator tier (admin token)."
    exit 0
}

# We CAN observe and the invariant is violated. Honour the severity lever.
trip() {
    note "TRIPPED — $1"
    case "$severity" in
        warn) note "(LIVESPEC_BRANCH_PROTECTION_CHECK=warn — reporting, not failing)"; exit 0 ;;
        skip) note "(LIVESPEC_BRANCH_PROTECTION_CHECK=skip — reporting, not failing)"; exit 0 ;;
        *)    exit 1 ;;
    esac
}

# Sets RESOLVED_REPO to the github.com "owner/repo" slug, or skips (unknown) if
# the remote is absent or not a GitHub remote (only GitHub remotes carry GitHub
# branch protection — a structural, named exemption). MUST be called directly
# (not in $(...)) so skip_unknown's exit unwinds the whole script.
resolve_repo() {
    command -v gh >/dev/null 2>&1 || skip_unknown "the GitHub CLI (gh) is not installed."
    local origin_url slug
    origin_url="$(git remote get-url origin 2>/dev/null || true)"
    [ -n "$origin_url" ] || skip_unknown "no 'origin' remote is configured."
    # Normalise both ssh (git@github.com:owner/repo.git) and https
    # (https://github.com/owner/repo[.git]) forms to github.com/owner/repo.
    slug="$(printf '%s\n' "$origin_url" \
        | sed -E 's#^git@github\.com:#github.com/#; s#^https?://[^/]*github\.com/#github.com/#; s#\.git$##')"
    case "$slug" in
        github.com/*/*) RESOLVED_REPO="${slug#github.com/}" ;;
        *) skip_unknown "origin ($origin_url) is not a github.com remote — GitHub branch protection does not apply." ;;
    esac
}

# Sets RESOLVED_BRANCH to the repo's default branch, or skips (unknown). Same
# direct-call requirement as resolve_repo.
resolve_default_branch() {
    RESOLVED_BRANCH="$(gh api "repos/${RESOLVED_REPO}" --jq '.default_branch' 2>/dev/null || true)"
    [ -n "$RESOLVED_BRANCH" ] || skip_unknown "could not resolve the default branch for ${RESOLVED_REPO} (gh not authenticated?)."
}

verb_check() {
    resolve_repo            # sets RESOLVED_REPO, or exits (skip)
    resolve_default_branch  # sets RESOLVED_BRANCH, or exits (skip)
    local repo="$RESOLVED_REPO" branch="$RESOLVED_BRANCH"
    local err_file
    err_file="$(mktemp)"
    # shellcheck disable=SC2064
    trap "rm -f '$err_file'" EXIT

    if ! gh api "repos/${repo}/branches/${branch}/protection" >/dev/null 2>"$err_file"; then
        if grep -qiE 'HTTP 404|not protected' "$err_file"; then
            trip "default branch '${branch}' of ${repo} has NO branch protection. Establish it with: just protect-default-branch"
        elif grep -qiE 'HTTP 403|must have admin|not accessible' "$err_file"; then
            skip_unknown "the token lacks admin access to read branch protection for ${repo}."
        elif grep -qiE 'HTTP 401|authentication|gh auth login' "$err_file"; then
            skip_unknown "gh is not authenticated."
        else
            skip_unknown "could not read branch protection for ${repo}: $(head -n1 "$err_file")"
        fi
    fi

    # Protection exists. Assert it actually blocks direct/force mutation:
    #   - force pushes disabled, AND
    #   - a PR-or-status gate is present (so a plain push cannot land).
    local allow_force has_pr_gate has_status_gate
    allow_force="$(gh api "repos/${repo}/branches/${branch}/protection" --jq '.allow_force_pushes.enabled // false' 2>/dev/null || echo "unknown")"
    has_pr_gate="$(gh api "repos/${repo}/branches/${branch}/protection" --jq 'has("required_pull_request_reviews")' 2>/dev/null || echo "false")"
    has_status_gate="$(gh api "repos/${repo}/branches/${branch}/protection" --jq 'has("required_status_checks")' 2>/dev/null || echo "false")"

    [ "$allow_force" = "true" ] && trip "${repo}@${branch} permits force pushes (allow_force_pushes=true)."
    if [ "$has_pr_gate" != "true" ] && [ "$has_status_gate" != "true" ]; then
        trip "${repo}@${branch} protection has no PR or status-check gate — direct pushes could still land."
    fi

    note "OK — ${repo}@${branch} is protected (no force pushes; a PR/status gate is present)."
}

verb_apply() {
    resolve_repo            # sets RESOLVED_REPO, or exits (skip)
    resolve_default_branch  # sets RESOLVED_BRANCH, or exits (skip)
    local repo="$RESOLVED_REPO" branch="$RESOLVED_BRANCH" force="${FORCE:-0}"

    # Non-weakening + idempotent: if protection already exists, do NOT overwrite
    # a possibly richer hand-tuned configuration with the baseline. Re-run with
    # FORCE=1 to deliberately reset to the baseline.
    if gh api "repos/${repo}/branches/${branch}/protection" >/dev/null 2>&1; then
        if [ "$force" != "1" ]; then
            note "${repo}@${branch} is already protected — leaving it untouched (FORCE=1 to reset to the baseline)."
            exit 0
        fi
        note "${repo}@${branch} is already protected — FORCE=1, resetting to the baseline."
    fi

    note "applying baseline branch protection to ${repo}@${branch} ..."
    # Baseline: PR required (0 approvals — fits the fleet's auto-merge model),
    # admins included, no direct/force push, no branch deletion, linear history.
    # required_status_checks is left null because the consumer's check names are
    # not known here; the required-PR gate already forces the PR/worktree flow.
    gh api -X PUT "repos/${repo}/branches/${branch}/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
    note "OK — ${repo}@${branch} now requires a PR and rejects direct/force pushes."
}

main() {
    local verb="${1:-}"
    case "$verb" in
        check) verb_check ;;
        apply) verb_apply ;;
        *)
            note "usage: branch-protection.sh <check|apply>"
            note "  check  verify the default branch is protected (the tripwire)"
            note "  apply  establish baseline protection (FORCE=1 to reset an existing one)"
            exit 2
            ;;
    esac
}

main "$@"
