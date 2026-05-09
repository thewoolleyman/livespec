#!/usr/bin/env bash
# Idempotent bootstrap for beads on this livespec clone.
#
# Invoked by `just implementation:setup-beads`. Pattern adapted from
# Open Brain's scripts/setup-beads.sh (canonical pattern source per
# SPECIFICATION/non-functional-requirements.md §Contracts §"Implementation
# justfile namespace"). Architectural invariants live in
# §Constraints §"Beads invariants"; this script is mechanism.
#
# What it ensures:
# 1. `bd` is installed via mise per .mise.toml (`mise install` is idempotent).
# 2. `.beads/embeddeddolt/` exists. If `.beads/issues.jsonl` is committed but
#    `embeddeddolt/` is missing, bd init materializes the local Dolt store
#    from the JSONL. If neither exists, bd init bootstraps fresh (auto-commit
#    fires only on first-init, never on idempotent re-runs against a tree
#    that already carries committed `.beads/` files — verified empirically).
# 3. `git config core.hooksPath` points at `.beads/hooks/` (per-clone config,
#    not propagated by `git clone`, so re-asserted on every invocation).
# 4. `.beads/hooks/{pre-commit,pre-push,prepare-commit-msg,post-merge,
#    post-checkout}` are rewritten with the livespec-managed canonical
#    content (lefthook + beads + exit-code-preserving epilogue). The
#    canonical content invokes lefthook with `--no-auto-install` so a
#    `lefthook run` from anywhere does not silently clobber the file
#    back to the lefthook template (which loses the BEADS INTEGRATION
#    block AND the exit-fix epilogue, allowing `git commit` to succeed
#    even when a pre-commit hook reported failure).
# 5. Lefthook itself is NOT installed via npm. It's mise-pinned per
#    .mise.toml (`lefthook = "1.13.6"`). The npm package's postinstall
#    runs `lefthook install -f` on every install, which unconditionally
#    rewrites `core.hooksPath` and would clobber this hook integration.
#    See research/beads-problems.md § Problem 8 for the full diagnosis.
#    NFR §Contracts "Lefthook installation source" codifies this rule.
#
# Non-fatal if mise is absent: prints guidance and exits 0 so CI in
# minimal contexts does not break.

set -euo pipefail

# Worktree skip — bd state is shared via the main checkout's .beads/.
# In a worktree, .beads/embeddeddolt/ doesn't exist locally (gitignored),
# but bd resolves the project root via git rev-parse --git-common-dir
# which points back to the main .git/. So bd correctly finds the existing
# Dolt store and refuses to re-init. Re-running setup-beads from inside a
# worktree would produce a confusing failure message ("Found existing
# Dolt database") despite nothing being wrong. Detect worktree and exit 0
# silently.
if [[ "$(git rev-parse --git-common-dir 2>/dev/null)" != "$(git rev-parse --git-dir 2>/dev/null)" ]]; then
  echo "setup-beads: skip — git worktree detected (bd state is shared via main checkout)"
  exit 0
fi

if ! command -v mise >/dev/null 2>&1; then
    echo "setup:beads: mise not on PATH — skipping beads bootstrap." >&2
    echo "  Install mise (https://mise.jdx.dev), then run 'just implementation:setup-beads'." >&2
    exit 0
fi

mise install --quiet

BD="mise exec -- bd"

# bd bootstrap auto-detects the right hydration source per the upstream
# beads architecture (docs/SYNC_SETUP.md). Priority order:
#   1. sync.remote configured → bd dolt clone from there
#   2. git origin has refs/dolt/data → bd dolt clone from origin (CANONICAL —
#      this is bd's actual cross-clone wire protocol; same git remote, but
#      the data lives under refs/dolt/data, separate from refs/heads/*)
#   3. .beads/backup/*.jsonl exists → restore from a Dolt-native backup
#   4. .beads/issues.jsonl exists → import from the JSONL export (degraded
#      fallback; loses dolt commit history — we keep this fallback only
#      because legacy clones may have a JSONL but no refs/dolt/data yet)
#   5. No source → fresh empty database
# Idempotent: when the database is already populated and consistent, bootstrap
# reports status without touching it. (See SPECIFICATION/non-functional-requirements.md
# §Constraints §"Beads invariants" for the architectural rules this enforces.)
#
# Related: research/beads-problems.md § Problems 1 + 4.
# Upstream: GH#3688 (synthesize Dolt remote at bd init), GH#3419 (bootstrap
# doesn't wire remote on fresh embedded init). Both still OPEN at time of
# writing; our `sync.remote` in .beads/config.yaml + the dolt-remote-add
# block below cover the gaps.
# Stale-lock cleanup. Embedded-mode bd holds .beads/embeddeddolt/.lock
# while the process runs. If a prior `bd` call was killed (timeout, SSH
# disconnect, ^C while waiting on prompt) the lock can persist; subsequent
# bd invocations queue up indefinitely waiting on it — see upstream
# GH#3701 (`bd prime hangs indefinitely on stale embedded-dolt lock`).
# Detect dead lock-holders and clear before doing anything else.
if [ -f .beads/embeddeddolt/.lock ]; then
    if command -v lsof >/dev/null 2>&1 && [ -z "$(lsof -t .beads/embeddeddolt/.lock 2>/dev/null)" ]; then
        echo "setup:beads: removing stale embedded-dolt lock (no live holders)" >&2
        rm -f .beads/embeddeddolt/.lock
    fi
fi

# GH#3722 guard: bd bootstrap (via bd init) can corrupt a symlinked CLAUDE.md
# by reading the symlink target string instead of the file contents, then
# writing the result back as a symlink blob containing the injected block.
# Work around by saving the symlink target before bootstrap and restoring
# the symlink after if it was corrupted. Safe no-op when CLAUDE.md is a
# regular file or does not exist.
_claude_symlink_target=""
if [ -L CLAUDE.md ]; then
    _claude_symlink_target="$(readlink CLAUDE.md)"
fi

bd_bootstrap_with_symlink_guard() {
    $BD bootstrap --yes
    # Restore CLAUDE.md symlink if corrupted (GH#3722).
    if [ -n "$_claude_symlink_target" ] && [ ! -L CLAUDE.md ]; then
        echo "setup:beads: GH#3722 guard: restoring corrupted CLAUDE.md symlink → $_claude_symlink_target" >&2
        ln -sf "$_claude_symlink_target" CLAUDE.md
    fi
}

if [ ! -d .beads/embeddeddolt ]; then
    # `bd bootstrap` requires at least one hydration source: sync.remote
    # configured, refs/dolt/data on git origin, .beads/backup/*.jsonl,
    # or .beads/issues.jsonl. If none exist (truly fresh clone with no
    # prior beads history pushed anywhere), `bd bootstrap` errors with
    # "No active beads workspace found" and refuses to act. In that
    # case we fall back to `bd init --non-interactive --prefix li`,
    # which materialises an empty embedded Dolt database with the
    # livespec issue prefix from NFR §Constraints §"Beads invariants" #1.
    has_hydration_source=0
    if git remote get-url origin >/dev/null 2>&1 \
        && git ls-remote origin 2>/dev/null | grep -q 'refs/dolt/data'; then
        has_hydration_source=1
    fi
    if [ -f .beads/issues.jsonl ]; then
        has_hydration_source=1
    fi
    if ls .beads/backup/*.jsonl >/dev/null 2>&1; then
        has_hydration_source=1
    fi
    if [ "$has_hydration_source" -eq 1 ]; then
        bd_bootstrap_with_symlink_guard
    else
        echo "setup:beads: no hydration source found — initialising fresh embedded database (prefix=li)" >&2
        # `--skip-agents` is REQUIRED. Without it, bd init appends a
        # "BEADS INTEGRATION" block to AGENTS.md/CLAUDE.md asserting
        # `do NOT use TodoWrite, TaskCreate, or markdown TODO lists`
        # and `do NOT use MEMORY.md files` — both directly conflict
        # with livespec's auto-memory and TaskCreate workflows. It
        # also writes `.claude/settings.json` with bd's own
        # opinionated wording for SessionStart/PreCompact hooks.
        # Livespec controls those layers itself: bd command guidance
        # lives in each implementation skill's SKILL.md and is loaded
        # contextually via `bd prime` at session start.
        #
        # `--skip-hooks` is REQUIRED. Without it, bd init writes its
        # own .beads/hooks/* templates AND backs up the existing
        # .git/hooks/* files into .beads/hooks/*.old, then auto-commits
        # everything — including a direct commit to master that bypasses
        # the no-commit-on-master lefthook gate (because the gate has
        # not yet been chained behind bd's hook templates at the moment
        # bd commits). Skipping hook installation lets us write our own
        # chained templates below via write_managed_hook, after which
        # the lefthook gates are honoured.
        $BD init --non-interactive --skip-agents --skip-hooks --prefix li
        # bd init --skip-hooks does NOT create .beads/hooks/. Our
        # write_managed_hook block below requires it; create it now
        # so the for-loop has somewhere to write.
        mkdir -p .beads/hooks
    fi
fi

# .beads/config.yaml is gitignored (per-clone, host-specific dolt remote
# URL). On a fresh clone bd bootstrap creates it; on an existing clone
# that just pulled a commit removing the tracked file, the file is gone
# but the dolt store still exists. Touch defensively so subsequent
# `bd config set` / `bd dolt remote add` calls have something to write to.
[ -f .beads/config.yaml ] || touch .beads/config.yaml

# Workspace identity mismatch detection + auto-recovery.
# See research/beads-problems.md § Problem 7 for the full diagnosis.
# In short: if .beads/metadata.json's project_id changes after a clone
# bootstrapped its local Dolt, every bd command errors with
# `workspace identity mismatch detected`. Our prior fix (silencing
# config-set + remote-add with `|| true`) hid the mismatch instead
# of recovering. The right thing is to detect it loudly and rebuild
# the local Dolt from origin's refs/dolt/data (the canonical state).
#
# Probe: use a bd command that ACTUALLY opens the database (and so
# triggers the identity check). `bd dolt status` only reads engine
# info — it succeeds even with a mismatch, so it's the WRONG probe
# (we shipped this bug in commit 414a9df and got bitten on macOS).
# `bd config get dolt.auto-commit` opens the DB to read the config
# row and reliably surfaces the mismatch on stderr. The config key
# itself is harmless to probe — we don't care about its value here.
# Idempotent; no-op when identities already match.
probe_err="$($BD config get dolt.auto-commit 2>&1 1>/dev/null)" || true
if [ -z "$probe_err" ]; then
    : # no error → identity matches → all good
elif echo "$probe_err" | grep -q "workspace identity mismatch"; then
    backup=".beads/embeddeddolt.corrupt.backup.$(date +%s)"
    echo "setup:beads: workspace identity mismatch detected — auto-recovering" >&2
    echo "  metadata.json's project_id differs from the local Dolt's _project_id." >&2
    echo "  Likely cause: metadata.json was rewritten upstream after this clone" >&2
    echo "  bootstrapped its local store. Backing up the stale store and" >&2
    echo "  re-bootstrapping from origin's refs/dolt/data (canonical state)." >&2
    echo "  See research/beads-problems.md § Problem 7." >&2
    echo "  Backup: $backup" >&2
    mv .beads/embeddeddolt "$backup"
    bd_bootstrap_with_symlink_guard
fi

# Per-clone: assert the dolt remote points at git origin so `bd dolt push` /
# `bd dolt pull` work natively against refs/dolt/data on the same git remote.
# bd bootstrap may have already set this when it cloned via refs/dolt/data;
# re-assertion is idempotent. We grep for `origin` in the listing to skip
# `bd dolt remote add` when it's already configured.
#
# See research/beads-problems.md § Problems 1 + 4.
# Upstream: GH#3688 (bd init should synthesize the remote), GH#3419
# (bd bootstrap doesn't wire remote on fresh embedded init). Both OPEN.
ORIGIN_URL=$(git config --get remote.origin.url 2>/dev/null || true)
if [ -n "$ORIGIN_URL" ] && ! $BD dolt remote list 2>&1 | grep -q '^origin'; then
    $BD dolt remote add origin "$ORIGIN_URL"
fi

# Per-clone: assert the two bd config keys that bd:doctor expects.
# These live in .beads/config.yaml; `bd config set` is idempotent so
# re-asserting on every prepare run is safe and silences bd:doctor
# warnings on fresh clones.
#
# - dolt.auto-commit=on: writes commit immediately to the local Dolt
#   working set (the alternative `batch` mode defers commits and is
#   incompatible with our git-hook-driven pre-commit / post-merge
#   sync flow).
# - export.auto=true: keeps `.beads/issues.jsonl` auto-refreshed as
#   the human-readable git-diffable export view alongside the
#   Dolt-native source of truth (NFR §Constraints §"Beads invariants" #3:
#   "Beads source-of-truth").
#
# These calls used to be wrapped with `>/dev/null 2>&1 || true`. That
# silenced legitimate errors (notably the workspace identity mismatch
# above), reporting `setup:beads: ok` despite zero actual progress.
# Now: identity mismatch is handled upfront; any other error here
# bubbles up via set -e. See research/beads-problems.md § Problem 7.
$BD config set dolt.auto-commit on
$BD config set export.auto true

# bd recommends 0700 on .beads/. Git can't track directory permissions
# (only the executable bit on files), so .beads/ comes out 0755 from a
# fresh clone regardless of source. Re-assert 0700 here on every run;
# chmod is idempotent. Silences `bd ready`'s permission warning.
#
# See research/beads-problems.md § Problem 6.
# Upstream: GH#3391 (issue, closed) → GH#3483 (PR, merged 2026-04-28).
# Drop this workaround once we bump past bd v1.0.3.
if [ -d .beads ]; then
    chmod 700 .beads
fi

current=$(git config core.hooksPath || true)
if [ "$current" != ".beads/hooks" ] && [ "$current" != ".beads/hooks/" ]; then
    git config core.hooksPath .beads/hooks
fi

# --- rewrite git hooks with the livespec-managed canonical content ---
# Hooks under .beads/hooks/ are owned by livespec. They invoke lefthook
# (mise-pinned per .mise.toml; see research/beads-problems.md § Problem 8
# for why lefthook is NOT installed via npm) and bd's hooks-runner,
# then re-honor lefthook's exit code so a failing pre-commit job actually
# blocks the commit (bd's integration otherwise overwrites $? and hides
# the failure). Per NFR §Constraints "Hook chaining": lefthook gates
# run FIRST, beads hooks SECOND, exit status preserved.
#
# We pass --no-auto-install to lefthook on every run as belt-and-braces
# defense: if a future operator briefly puts lefthook on PATH some other
# way, --no-auto-install prevents `lefthook run` from silently rewriting
# this file back to lefthook's own template (which would lose the BEADS
# INTEGRATION block AND the exit-fix epilogue).
write_managed_hook() {
    local hook="$1"
    # Determine whether bd's hooks-runner processes this hook. Bd
    # recognizes pre-commit, pre-push, prepare-commit-msg, post-merge,
    # post-checkout. It does NOT process commit-msg (it returns
    # `Error: unknown hook: commit-msg` with exit 1). Livespec adds
    # commit-msg to the chain anyway so the lefthook-managed
    # no-commit-on-master / Conventional Commits / Red-Green replay
    # gates keep firing after core.hooksPath flips to .beads/hooks/.
    # For hooks bd does not process, the template includes only the
    # lefthook chain + exit fix; the bd integration block is omitted
    # entirely (running it would always fail with "unknown hook").
    local bd_supports_hook=0
    case "$hook" in
        pre-commit|pre-push|prepare-commit-msg|post-merge|post-checkout)
            bd_supports_hook=1
            ;;
    esac
    {
    cat <<HOOK_HEAD
#!/bin/sh
# LIVESPEC-IMPLEMENTATION-MANAGED HOOK.
# Re-asserted on every \`just implementation:setup-beads\` invocation
# by dev-tooling/implementation/setup-beads.sh.
# Layout (per NFR §Constraints "Hook chaining"):
#   1. Lefthook (mise-pinned; invoked with --no-auto-install).
#   2. BEADS INTEGRATION (auto-export of .beads/issues.jsonl, etc.) —
#      OMITTED for hooks bd does not process (notably commit-msg).
#   3. Exit fix: re-honor lefthook's exit code so a failing pre-commit
#      job actually blocks the commit (the bd integration otherwise
#      overwrites \$? and hides the failure).

if [ "\$LEFTHOOK_VERBOSE" = "1" ] || [ "\$LEFTHOOK_VERBOSE" = "true" ]; then
  set -x
fi

if [ "\$LEFTHOOK" = "0" ]; then
  exit 0
fi

# Resolve lefthook: mise-pinned per .mise.toml. We deliberately do NOT
# install lefthook via npm (see research/beads-problems.md § Problem 8 —
# lefthook's npm postinstall runs \`lefthook install -f\` which clobbers
# core.hooksPath and bypasses this hook entirely).
call_lefthook()
{
  if test -n "\$LEFTHOOK_BIN"
  then
    "\$LEFTHOOK_BIN" "\$@"
  elif command -v mise >/dev/null 2>&1 && mise exec -- lefthook -h >/dev/null 2>&1
  then
    mise exec -- lefthook "\$@"
  elif lefthook -h >/dev/null 2>&1
  then
    lefthook "\$@"
  else
    echo >&2 "Can't find lefthook (expected via 'mise exec -- lefthook'; run 'mise install')"
    return 127
  fi
}

call_lefthook run --no-auto-install "$hook" "\$@"
_lefthook_exit=\$?
HOOK_HEAD
    if [ "$bd_supports_hook" -eq 1 ]; then
        cat <<HOOK_BD
# --- BEGIN BEADS INTEGRATION v1.0.3 ---
# This section is managed by beads. Do not remove these markers.
#
# Self-heal .beads/ permissions to 0700 BEFORE invoking bd, so a
# fresh clone (umask-created 0755) doesn't trigger bd's permission
# warning on every git operation. Git can't track directory perms
# (only the exec bit on files), so this re-assertion has to live
# in a hook that fires on every pull/checkout. chmod is idempotent
# and the 2>/dev/null || true guard prevents a chmod failure (e.g.
# read-only mount) from blocking the hook.
#
# See research/beads-problems.md § Problem 6.
# Upstream: GH#3391 → GH#3483 (merged 2026-04-28); drop this
# self-heal once we bump past bd v1.0.3.
[ -d .beads ] && chmod 700 .beads 2>/dev/null || true
#
# Resolve bd: prefer mise-pinned (.mise.toml v1.0.3) via \`mise exec
# --\` over plain PATH bd which may be a shadowed older binary
# emitting "Failed to flush bd changes to JSONL" warnings.
# Use \`mise exec --\` (NOT the absolute path returned by \`mise which
# bd\`) because bd needs the env mise sets up — the absolute path
# alone reports "no beads database found".
_BD_PREFIX=""
_BD_AVAILABLE=0
if command -v mise >/dev/null 2>&1 && mise exec -- bd --version >/dev/null 2>&1; then
  _BD_PREFIX="mise exec --"
  _BD_AVAILABLE=1
elif command -v bd >/dev/null 2>&1; then
  _BD_AVAILABLE=1
fi
if [ \$_BD_AVAILABLE -eq 1 ]; then
  export BD_GIT_HOOK=1
  _bd_timeout=\${BEADS_HOOK_TIMEOUT:-300}
  if command -v timeout >/dev/null 2>&1; then
    timeout "\$_bd_timeout" \$_BD_PREFIX bd hooks run $hook "\$@"
    _bd_exit=\$?
    if [ \$_bd_exit -eq 124 ]; then
      echo >&2 "beads: hook '$hook' timed out after \${_bd_timeout}s — continuing without beads"
      _bd_exit=0
    fi
  else
    \$_BD_PREFIX bd hooks run $hook "\$@"
    _bd_exit=\$?
  fi
  if [ \$_bd_exit -eq 3 ]; then
    echo >&2 "beads: database not initialized — skipping hook '$hook'"
    _bd_exit=0
  fi
  if [ \$_bd_exit -ne 0 ]; then exit \$_bd_exit; fi
fi
# --- END BEADS INTEGRATION v1.0.3 ---
HOOK_BD
    fi
    cat <<HOOK_TAIL

# --- BEGIN LIVESPEC HOOK EXIT FIX ---
exit \${_lefthook_exit:-0}
# --- END LIVESPEC HOOK EXIT FIX ---
HOOK_TAIL
    } > ".beads/hooks/$hook"
    chmod +x ".beads/hooks/$hook"
}

if [ -d .beads/hooks ]; then
    # Note: `commit-msg` is added on top of the Open Brain canonical
    # five (pre-commit, pre-push, prepare-commit-msg, post-merge,
    # post-checkout) because livespec runs critical commit-msg gates
    # via lefthook (v034 Red→Green replay, v056 Conventional Commits,
    # no-commit-on-master). Once core.hooksPath flips to .beads/hooks/,
    # those gates only fire if a .beads/hooks/commit-msg file exists.
    # bd's own hooks-runner doesn't process commit-msg natively (it
    # returns "database not initialized" exit 3, which the template
    # treats as a no-op) — the chained lefthook invocation is what
    # matters here. Per NFR §Constraints §"Hook chaining".
    for hook in pre-commit commit-msg pre-push prepare-commit-msg post-merge post-checkout; do
        write_managed_hook "$hook"
    done
fi

echo "setup:beads: ok (bd $(mise exec -- bd --version 2>/dev/null | awk '{print $3}'), core.hooksPath=$(git config core.hooksPath))"
