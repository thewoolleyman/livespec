#!/usr/bin/env bash
# dev-tooling/implementation/bd-doctor.sh
#
# Diagnostic / sanity check for the livespec beads (bd) installation
# on this clone. Verifies the architecture-critical preconditions
# codified in SPECIFICATION/non-functional-requirements.md §Constraints
# §"Beads invariants" — in particular the canonical sync wire protocol
# is `refs/dolt/data` on the same git remote, NOT `.beads/issues.jsonl`
# (which is the human-readable export view; invariant #3 "Beads
# source-of-truth").
#
# Why this script exists: upstream `bd doctor` errors with "not yet
# supported in embedded mode" and prints no actionable checks. We
# compose the equivalent from primitives that DO work in embedded
# mode (bd version, bd where, bd dolt status, bd dolt remote list,
# bd config get, git ls-remote). See research/beads-problems.md
# § Problem 2; upstream GH#3597 (OPEN). Drop this script when
# upstream lands embedded-mode support for `bd doctor`.
#
# Run as `just implementation:beads-doctor`. Pattern adapted from
# Open Brain's scripts/bd-doctor.sh.
#
# Checks (each prints one PASS / WARN / FAIL line and a remediation
# command on FAIL):
#
#   1. mise + bd available, bd version >= 1.0.3
#   2. `bd where` returns a real database path
#   3. `bd dolt status` reports embedded mode + a populated data dir
#   4. `bd dolt remote list` shows `origin` (so push/pull work)
#   5. `git ls-remote origin | grep dolt` shows `refs/dolt/data` on
#      the remote (so cross-clone sync actually has somewhere to go)
#   6. `bd config get dolt.auto-commit` is `on` (so writes are
#      durable and don't accumulate as uncommitted working set)
#   7. `bd config get export.auto` is `true` (so the JSONL export
#      stays in sync for human-readable git history)
#   8. `git config core.hooksPath` resolves to `.beads/hooks` (so the
#      bd-managed hook chain at .beads/hooks/ actually fires on git
#      operations). When this drifts (typically when something runs
#      `lefthook install` and resets the path to `.git/hooks`), bd's
#      JSONL auto-export and refs/dolt/data sync are silently bypassed.
#      See research/beads-problems.md § Problem 8.
#   9. lefthook is resolvable via `mise exec --` per .mise.toml. The
#      bd-managed hook templates dispatch lefthook through mise; if
#      lefthook is missing or shadowed by a node_modules install
#      (which would re-introduce the postinstall race per Problem 8),
#      surface it.
#
# Exit code: 0 when every check is PASS or WARN; 1 when any FAIL.
# WARN is reserved for operator-action-required conditions (e.g.
# "no dolt remote configured" on a fresh-but-not-yet-pushed clone) —
# they signal "you should fix this" without blocking the wrapper
# that called us.

set -uo pipefail

# ---------------------------------------------------------------------
# Color output (TTY-aware)
# ---------------------------------------------------------------------

if [ -t 1 ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    RED='\033[0;31m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    GREEN=''
    YELLOW=''
    RED=''
    BOLD=''
    NC=''
fi

declare -i FAILS=0
declare -i WARNS=0

pass() {
    printf '  %bPASS%b  %s\n' "$GREEN" "$NC" "$1"
}

warn() {
    printf '  %bWARN%b  %s\n' "$YELLOW" "$NC" "$1"
    if [ -n "${2:-}" ]; then
        printf '        remediation: %s\n' "$2"
    fi
    WARNS+=1
}

fail() {
    printf '  %bFAIL%b  %s\n' "$RED" "$NC" "$1"
    if [ -n "${2:-}" ]; then
        printf '        remediation: %s\n' "$2"
    fi
    FAILS+=1
}

header() {
    printf '%b[bd:doctor]%b %s\n' "$BOLD" "$NC" "$1"
}

# ---------------------------------------------------------------------
# bd resolution
# ---------------------------------------------------------------------

# Prefer mise exec -- bd over plain PATH bd (older shadowed copies in
# ~/.local/bin/ have caused confusion before).
if command -v mise >/dev/null 2>&1; then
    BD="mise exec -- bd"
elif command -v bd >/dev/null 2>&1; then
    BD="bd"
else
    header 'bd:doctor running'
    fail "bd not on PATH (neither via mise nor as a global binary)" \
        "install mise + run 'mise install' (the .mise.toml pins bd 1.0.3)"
    exit 1
fi

header 'bd:doctor running'
echo

# ---------------------------------------------------------------------
# Check 1: bd version >= 1.0.3
# ---------------------------------------------------------------------

BD_VERSION_RAW=$($BD version 2>/dev/null | head -1 || true)
BD_VERSION=$(printf '%s\n' "$BD_VERSION_RAW" | awk '{print $3}')
if [ -z "$BD_VERSION" ]; then
    fail "could not parse bd version output" \
        "run '$BD version' manually and check the output"
else
    # Compare against 1.0.3 (sort -V handles semver ordering).
    LOWEST=$(printf '1.0.3\n%s\n' "$BD_VERSION" | sort -V | head -1)
    if [ "$LOWEST" = "1.0.3" ]; then
        pass "bd version $BD_VERSION (>= 1.0.3 required for refs/dolt/data sync)"
    else
        fail "bd version $BD_VERSION is older than 1.0.3" \
            "run 'mise install' to upgrade per .mise.toml"
    fi
fi

# ---------------------------------------------------------------------
# Check 2: bd where returns a database path
# ---------------------------------------------------------------------

BD_WHERE=$($BD where 2>&1 || true)
if printf '%s\n' "$BD_WHERE" | grep -q 'database:'; then
    DB_PATH=$(printf '%s\n' "$BD_WHERE" | awk -F': ' '/database:/ {print $2; exit}')
    pass "bd database resolved at $DB_PATH"
else
    fail "bd where did not report a database path" \
        "run 'just implementation:setup-beads' to bootstrap"
fi

# ---------------------------------------------------------------------
# Check 3: bd dolt status reports embedded engine + populated data dir
# ---------------------------------------------------------------------

BD_DOLT_STATUS=$($BD dolt status 2>&1 || true)
if printf '%s\n' "$BD_DOLT_STATUS" | grep -q 'Dolt engine:'; then
    ENGINE_LINE=$(printf '%s\n' "$BD_DOLT_STATUS" | grep 'Dolt engine:' | head -1)
    pass "bd dolt status: $ENGINE_LINE"
else
    fail "bd dolt status did not report an engine line" \
        "run '$BD dolt status' manually; possibly run 'just implementation:setup-beads'"
fi

# ---------------------------------------------------------------------
# Check 4: dolt remote configured
# ---------------------------------------------------------------------

BD_DOLT_REMOTE=$($BD dolt remote list 2>&1 || true)
if printf '%s\n' "$BD_DOLT_REMOTE" | grep -q '^origin'; then
    REMOTE_LINE=$(printf '%s\n' "$BD_DOLT_REMOTE" | grep '^origin' | head -1)
    pass "bd dolt remote 'origin' configured ($REMOTE_LINE)"
else
    ORIGIN_URL=$(git config --get remote.origin.url 2>/dev/null || true)
    if [ -n "$ORIGIN_URL" ]; then
        warn "no dolt remote configured (git origin is $ORIGIN_URL)" \
            "$BD dolt remote add origin $ORIGIN_URL"
    else
        warn "no dolt remote configured AND no git origin configured" \
            "configure git remote first, then '$BD dolt remote add origin <url>'"
    fi
fi

# ---------------------------------------------------------------------
# Check 5: refs/dolt/data exists on origin
# ---------------------------------------------------------------------

if git remote get-url origin >/dev/null 2>&1; then
    LS_REMOTE=$(git ls-remote origin 2>/dev/null | grep 'refs/dolt/data' || true)
    if [ -n "$LS_REMOTE" ]; then
        SHA=$(printf '%s\n' "$LS_REMOTE" | awk '{print $1}')
        pass "git ls-remote origin shows refs/dolt/data ($SHA)"
    else
        warn "refs/dolt/data missing on origin (cross-clone sync will not work)" \
            "$BD dolt push   # pushes the local Dolt to refs/dolt/data on origin"
    fi
else
    warn "no git origin configured — cannot probe refs/dolt/data" \
        "set 'git remote add origin <url>' first"
fi

# ---------------------------------------------------------------------
# Check 6: dolt.auto-commit is 'on'
# ---------------------------------------------------------------------

AUTO_COMMIT=$($BD config get dolt.auto-commit 2>/dev/null | tr -d '[:space:]' || true)
case "$AUTO_COMMIT" in
    on|true)
        pass "dolt.auto-commit = $AUTO_COMMIT (writes durable; no manual 'bd dolt commit' required)"
        ;;
    batch)
        warn "dolt.auto-commit = batch (writes accumulate in working set until 'bd dolt commit')" \
            "$BD config set dolt.auto-commit on   # recommended for single-operator workflow"
        ;;
    off|false|"")
        warn "dolt.auto-commit = ${AUTO_COMMIT:-<unset>} (writes will not commit automatically)" \
            "$BD config set dolt.auto-commit on"
        ;;
    *)
        warn "dolt.auto-commit = $AUTO_COMMIT (unexpected value)" \
            "$BD config set dolt.auto-commit on"
        ;;
esac

# ---------------------------------------------------------------------
# Check 7: export.auto is true
# ---------------------------------------------------------------------

EXPORT_AUTO=$($BD config get export.auto 2>/dev/null | tr -d '[:space:]' || true)
case "$EXPORT_AUTO" in
    true|on)
        pass "export.auto = $EXPORT_AUTO (.beads/issues.jsonl auto-refreshed for human-readable git history)"
        ;;
    *)
        warn "export.auto = ${EXPORT_AUTO:-<unset>} (.beads/issues.jsonl will not auto-refresh)" \
            "$BD config set export.auto true   # keep the JSONL export view current"
        ;;
esac

# ---------------------------------------------------------------------
# Check 8: core.hooksPath = .beads/hooks
# ---------------------------------------------------------------------
#
# The bd-managed hook chain (.beads/hooks/{pre-commit,pre-push,...})
# only fires when git's core.hooksPath is set to .beads/hooks. When this
# value drifts (typically because lefthook ran `install -f` from
# somewhere and reset it to git's default .git/hooks), bd's JSONL
# auto-export and refs/dolt/data sync are silently bypassed. See
# research/beads-problems.md § Problem 8.

HOOKS_PATH=$(git config core.hooksPath 2>/dev/null || true)
case "$HOOKS_PATH" in
    .beads/hooks|.beads/hooks/)
        pass "core.hooksPath = $HOOKS_PATH (bd-managed hook chain will fire on git operations)"
        ;;
    "")
        fail "core.hooksPath is unset — bd-managed hooks at .beads/hooks/ are bypassed" \
            "git config core.hooksPath .beads/hooks   # or run 'just implementation:setup-beads'"
        ;;
    *)
        fail "core.hooksPath = '$HOOKS_PATH' (expected '.beads/hooks') — bd-managed hooks are bypassed" \
            "git config core.hooksPath .beads/hooks   # or run 'just implementation:setup-beads'"
        ;;
esac

# ---------------------------------------------------------------------
# Check 9: lefthook resolves via mise (and not via node_modules)
# ---------------------------------------------------------------------
#
# Lefthook is mise-pinned per .mise.toml (`lefthook = "1.13.6"`).
# We deliberately do NOT install via npm because the npm postinstall
# runs `lefthook install -f` on every install, which clobbers
# core.hooksPath. The bd-managed hook templates dispatch lefthook via
# `mise exec -- lefthook`. See research/beads-problems.md § Problem 8;
# NFR §Contracts "Lefthook installation source" codifies this rule.

if command -v mise >/dev/null 2>&1 && mise exec -- lefthook -h >/dev/null 2>&1; then
    LEFTHOOK_VERSION=$(mise exec -- lefthook version 2>/dev/null | head -1 || true)
    pass "lefthook resolvable via 'mise exec --' (version $LEFTHOOK_VERSION)"
else
    fail "lefthook not resolvable via 'mise exec --'" \
        "run 'mise install' (.mise.toml pins lefthook 1.13.6)"
fi

# Detect the npm-package re-introduction footgun: if lefthook reappears
# in node_modules, its postinstall will fire on the next npm/pnpm
# install and reset core.hooksPath. Warn loudly. (Livespec ships no
# package.json today; this guard is defensive against future drift.)
if [ -e node_modules/lefthook/postinstall.js ]; then
    warn "lefthook reappeared in node_modules — its postinstall will reset core.hooksPath" \
        "remove from package.json dependencies; lefthook is mise-pinned (research/beads-problems.md § Problem 8)"
fi

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

echo
if [ "$FAILS" -gt 0 ]; then
    printf '%b[bd:doctor] FAIL%b  %d check(s) failed, %d warn(s)\n' "$RED" "$NC" "$FAILS" "$WARNS"
    exit 1
fi

if [ "$WARNS" -gt 0 ]; then
    printf '%b[bd:doctor] OK%b   (with %d warn(s) — operator action recommended)\n' "$YELLOW" "$NC" "$WARNS"
    exit 0
fi

printf '%b[bd:doctor] OK%b   all checks passed\n' "$GREEN" "$NC"
exit 0
