#!/usr/bin/env python3
"""
livespec footgun guard — Claude Code PreToolUse hook (Bash).

Blocks ONLY patterns that are NEVER legitimate in the livespec family:
  - `git ... commit/push ... --no-verify`
  - `git ... config core.bare <true>`   (set; NOT --get/--unset/--list reads)
  - a leading `LEFTHOOK=0|false` env-assignment (the --no-verify equivalent)
  - a WRITE into the Claude auto-memory store via Bash (redirect / tee / cp /
    mv / dd / sed -i / here-doc landing on `.claude/projects/<slug>/memory/`)
each with an actionable deny message naming the correct alternative.

Detection is TOKEN/SEGMENT based, not substring based. A real git footgun is the
EXECUTED leading command of a shell segment — e.g. `git config core.bare true`
or `... && LEFTHOOK=0 git commit`. The dangerous strings frequently appear as
DATA (a test fixture, an `echo`, a `git log --grep`, a here-doc body, a commit
message); those must NOT be blocked. So for each `&&`/`||`/`;`/`|`/newline
segment we strip leading env-assignments + `mise exec --` + `sudo`/`env`
wrappers, then inspect only the resulting git invocation. A segment whose
leading command is `echo`/`grep`/`python`/`cat`/etc. is never a git footgun no
matter what string it carries.

The memory-write rule is the one FAIL-CLOSED check: a write landing on a memory
path is denied unconditionally (the Write/Edit tool is already governed for
memory paths; this closes the shell bypass observed when an agent re-ran a
blocked Write via `cat >>`). It is regex-matched on the raw segment (here-doc
bodies stripped) so a quoting trick that defeats shlex cannot evade it; reads of
a memory file stay allowed.

Always exits 0; the git-footgun checks fail OPEN on any parse/tokenize error (a
guard bug must never block legitimate work — the commit-refuse hook + branch
protection are the real backstops; that part of the guard is only a fast early
warning). The memory-write rule, by contrast, fails CLOSED on detection.
"""

import json
import re
import shlex
import sys

_NO_VERIFY_REASON = (
    "NEVER use --no-verify in the livespec family. The lefthook gates "
    "(commit-msg, pre-commit, pre-push, Red-Green-Replay trailers) are "
    "load-bearing. If a hook rejects a commit, READ the rejection and fix the "
    "ROOT CAUSE, or HALT and ask the user — do not bypass. "
    "(memory feedback_sub_agent_dispatch_no_verify_ban)"
)
_CORE_BARE_REASON = (
    "NEVER set core.bare=true. Epic li-unbare eliminated the bare flag; "
    "core.bare on a primary is a REGRESSION the doctor invariant "
    "(primary-checkout-commit-refuse-hook-installed) forbids. Do edits in a "
    "secondary worktree via `git -C <repo> worktree add "
    "<repo>/.claude/worktrees/<slug> -b <branch> origin/master`. "
    "(memory feedback_bare_flag_use_git_show_not_filesystem)"
)
_LEFTHOOK_REASON = (
    "NEVER set LEFTHOOK=0/false — it disables lefthook, a --no-verify "
    "equivalent. Fix the failing hook's root cause or HALT and ask. "
    "(memory feedback_sub_agent_dispatch_no_verify_ban)"
)
_MEMORY_WRITE_REASON = (
    "NEVER write to the Claude auto-memory store via Bash. The Claude-only "
    "store (~/.claude/projects/<project>/memory/) is RETIRED: durable, "
    "cross-agent guidance now lives in the repo's AGENTS.md (Claude reads it "
    "through the .claude/CLAUDE.md symlink; Codex reads AGENTS.md natively), "
    "and trackable items are filed through capture-work-item. Do NOT recreate "
    "or append to the store with redirects / tee / cp / mv / dd / sed -i / "
    "heredocs — the Write/Edit tool is already governed for memory paths and "
    "this rule closes the shell bypass. Put durable guidance in AGENTS.md, or "
    "file a work-item via "
    "`/livespec-orchestrator-beads-fabro:capture-work-item`. "
    "(work-item bd-ib-ogh2ls)"
)

_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_GIT_GLOBAL_OPTS_WITH_ARG = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")
_SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
_HEREDOC = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")

# A path under the Claude per-project auto-memory store:
# `.claude/projects/<project-slug>/memory/...`. Generic over the slug so the
# rule is not pinned to one project. The infix matches `~/.claude/...`,
# `$HOME/.claude/...`, and absolute `/home/<user>/.claude/...` forms alike —
# only the `.claude/projects/<slug>/memory/` portion is anchored.
_MEM_PATH = r"\.claude/projects/[^/\s'\"|&;<>]+/memory/"

# Bash WRITE vectors that LAND ON a memory path. Each is matched against a
# single command SEGMENT (here-doc bodies already stripped, so a path mentioned
# inside written CONTENT is not a false positive — only the redirect TARGET on
# the introducing line is inspected). A match is an UNCONDITIONAL deny
# (fail-closed), unlike the git-footgun checks which fail open. Reads of a
# memory file (`cat mem`, `grep x mem`, `cp mem /tmp/`) are deliberately NOT
# matched — only writes INTO the store are blocked.
_MEM_WRITE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Output redirection / here-doc target: `> mem`, `>> mem`, `1> mem`,
    # `&> mem`, `>| mem` (a leading fd / `&` / `|` is not consumed — the match
    # may begin at the `>`).
    re.compile(r">>?\|?\s*[^\s|&;<>]*" + _MEM_PATH),
    # `tee [-a] mem` — tee WRITES each file operand.
    re.compile(r"\btee\b[^|&;<>]*" + _MEM_PATH),
    # `truncate ... mem` — always a write.
    re.compile(r"\btruncate\b[^|&;<>]*" + _MEM_PATH),
    # `dd ... of=mem` — the `of=` operand is the write target.
    re.compile(r"\bdd\b[^|&;<>]*\bof=[^\s|&;<>]*" + _MEM_PATH),
    # `sed -i ... mem` / `sed --in-place ... mem` — edits the file in place.
    re.compile(r"\bsed\b[^|&;<>]*(?:-i|--in-place)[^|&;<>]*" + _MEM_PATH),
    # `cp|mv|rsync|install|ln SRC ... mem` — require at least one operand BEFORE
    # the memory path so it is treated as the DESTINATION (copying a memory file
    # OUT, where mem is the first operand, is a read and stays allowed).
    re.compile(r"\b(?:cp|mv|rsync|install|ln)\b\s+[^\s|&;<>]+\s+[^|&;<>]*" + _MEM_PATH),
)


def _strip_heredoc_bodies(command: str) -> str:
    """Remove here-doc BODIES (they are file data, not executed commands).

    `cat > f <<'EOF'\n...body...\nEOF` — the body lines are data; analyzing them
    as command segments causes false positives. Keep the introducing line, drop
    everything from the next line through the terminator line.
    """
    lines = command.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        m = _HEREDOC.search(line)
        if m:
            term = m.group(1)
            i += 1
            # Skip body until a line that is exactly the terminator (optionally
            # indented for <<-).
            while i < n and lines[i].strip() != term:
                i += 1
            # `i` now points at the terminator line (or EOF); skip it too.
            if i < n:
                i += 1
            continue
        i += 1
    return "\n".join(out)


def _segments(command: str) -> list[str]:
    cleaned = _strip_heredoc_bodies(command)
    return [s.strip() for s in _SEGMENT_SPLIT.split(cleaned) if s.strip()]


def _strip_leading_noise(tokens: list[str]) -> tuple[list[str], bool]:
    """Strip leading env-assignments and `mise exec [--] ` / `sudo` / `env`.

    Returns (remaining tokens, lefthook_disabled_seen).
    """
    lefthook_off = False
    i = 0
    n = len(tokens)
    # Leading VAR=val assignments (env for the command).
    while i < n and _ENV_ASSIGN.match(tokens[i]):
        if re.match(r"^LEFTHOOK=(?:0|false|off|no)$", tokens[i], re.IGNORECASE):
            lefthook_off = True
        i += 1
    # `mise exec [flags] [--]` wrapper (possibly repeated with sudo/env).
    changed = True
    while changed and i < n:
        changed = False
        base = tokens[i].rsplit("/", 1)[-1]
        if base in ("sudo", "env"):
            i += 1
            changed = True
            while i < n and _ENV_ASSIGN.match(tokens[i]):
                i += 1
            continue
        if base == "mise":
            # Consume `exec`/`x`, any flags, and a `--` terminator. A `--`
            # token satisfies the `startswith("-")` clause, so it is swept up
            # by the same loop; `j` starts at `i + 1`, so it always advances at
            # least one token past `mise`.
            j = i + 1
            while (j < n and tokens[j] != "--" and tokens[j] in ("exec", "x")) or (
                j < n and tokens[j].startswith("-")
            ):
                j += 1
            i = j
            changed = True
            continue
    return tokens[i:], lefthook_off


def _git_subcommand(tokens: list[str]) -> tuple[str | None, list[str]]:
    """If tokens is a git invocation, return (subcommand, args_after_subcommand)."""
    if not tokens:
        return None, []
    if tokens[0].rsplit("/", 1)[-1] != "git":
        return None, []
    i = 1
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t == "--":
            i += 1
            break
        if not t.startswith("-"):
            break
        i += 1
        if t in _GIT_GLOBAL_OPTS_WITH_ARG and i < n:
            i += 1
    if i >= n:
        return None, []
    return tokens[i], tokens[i + 1 :]


def _memory_write_reason(seg: str) -> str | None:
    """Return the deny reason iff `seg` WRITES to the Claude memory store.

    Regex-based and run on the raw segment string (no shlex), so a quoting trick
    that would defeat tokenization cannot evade the rule. Fail-closed: any match
    denies.
    """
    for pattern in _MEM_WRITE_PATTERNS:
        if pattern.search(seg):
            return _MEMORY_WRITE_REASON
    return None


def _check_segment(seg: str) -> tuple[bool, str]:
    try:
        tokens = shlex.split(seg, posix=True)
    except ValueError:
        return False, ""  # unparseable → fail open
    # An empty token list (only possible for a blank segment, which `_segments`
    # already drops) falls through harmlessly: `_git_subcommand([])` returns
    # `None`, so the segment is treated as not-a-footgun.
    core, lefthook_off = _strip_leading_noise(tokens)
    if lefthook_off:
        return True, _LEFTHOOK_REASON
    sub, args = _git_subcommand(core)
    if sub is None:
        return False, ""  # leading command isn't git → not a footgun
    if sub in ("commit", "push") and "--no-verify" in args:
        return True, _NO_VERIFY_REASON
    if sub == "config":
        # Reads/removes are fine; only a SET of core.bare to a truthy value is the footgun.
        if any(a in ("--get", "--unset", "--list", "--get-all", "--unset-all") for a in args):
            return False, ""
        joined = " ".join(args)
        # The two independent word-boundary searches also catch the
        # `core.bare=true` / `core.bare=1` equals forms (`\bcore\.bare\b` and
        # the truthy word both match the joined string), so no separate
        # equals-form branch is needed.
        if re.search(r"\bcore\.bare\b", joined) and re.search(
            r"\b(?:true|1|yes|on)\b", joined, re.IGNORECASE
        ):
            return True, _CORE_BARE_REASON
    return False, ""


def _deny(reason: str, command: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED by livespec_footgun_guard.py\n\n{reason}\n\n"
                f"Command: {command}\n\n"
                "This block is NOT a transient/transport failure. Do NOT retry "
                "the same command. Use the named alternative, or stop and ask "
                "the user. If this is a FALSE positive, tighten "
                "~/.claude/hooks/livespec_footgun_guard.py."
            ),
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
        if data.get("tool_name", "") != "Bash":
            sys.exit(0)
        command = data.get("tool_input", {}).get("command", "")
        if not command:
            sys.exit(0)
        for seg in _segments(command):
            mem_reason = _memory_write_reason(seg)
            if mem_reason is not None:
                _deny(mem_reason, command)
            blocked, reason = _check_segment(seg)
            if blocked:
                _deny(reason, command)
        sys.exit(0)
    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
