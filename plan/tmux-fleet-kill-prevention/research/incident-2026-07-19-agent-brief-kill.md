# Incident record — 2026-07-19 fleet kill caused by an adversarial-review agent brief

**The agent driving this thread destroyed the maintainer's tmux fleet.** This is
the third fleet kill (2026-07-03, 2026-07-18 ×2, 2026-07-19). It was caused by
the agent working ON the prevention epic, which makes it the most instructive of
the four. Record it verbatim; do not soften it.

## Timeline (CEST, 2026-07-19)

| When | What |
|---|---|
| 07:47:55 | Session spawned a **Codex** sub-agent (`codex:codex-rescue`) to adversarially pre-accept-review the 4 merged guard changes. |
| 07:59:03–07:59:05 | Fleet died. Clean-teardown signature in the user journal: a burst of `tmux-spawn-*.scope: Consumed <N> CPU time, <N>G memory peak` — identical to the 2026-07-18 signature (not a crash, not OOM). |
| 08:03:39 | Maintainer manually recreated one session. |

Corroboration: the session's own foreground `Bash` call died with **exit 137**
(SIGKILL) — its shell went down with the server it lived in.

## Root cause

The review brief instructed the agent to **"actively try to break each"** guard
and then *listed literal fleet-killing commands to craft*:

- `env TMUX_TMPDIR=/tmp tmux kill-server`
- `tmux -S /tmp/tmux-1000/default kill-server`
- `tmux -L default kill-server`
- `bash -c 'tmux kill-server'`

The author's intent was "feed these as JSON payload strings to the guard's
stdin and read its verdict." **The brief never said that**, and never said
"do not execute a tmux command." An agent told to "try" them had every reason
to run them.

## Why no guard stopped it

The only guard actually live at the time was the **host guard** — a Claude Code
`PreToolUse` (Bash) hook in `~/.claude/settings.json`. **A Codex-runtime agent
does not pass through Claude Code hooks at all.** The session pointed a
"break the tmux guard" agent at the one runtime its guard provably could not see.

### CORRECTION (2026-07-19, established by live probing)

The paragraph that stood here claimed the Codex guard was "merged but never
installed into `~/.codex/config.toml`". **That is wrong**, and the error mattered:
it sent the next session looking for a missing installation instead of a broken
one. The record is corrected rather than deleted, because the wrong diagnosis is
itself part of the lesson.

The Codex guard (work-item `livespec-omjc2t` → mirror `livespec-driver-codex-72z`)
**was installed, enabled, and trusted** — `[plugins."livespec@livespec-driver-codex"]
enabled = true` in `~/.codex/config.toml`, with `[hooks.state]` trust entries, and a
plugin cache written at **07:22:50, thirty-seven minutes before the 07:59 kill**. Its
tmux classification logic was correct and correctly wired as a `PreToolUse`/`Bash`
matcher.

**It could not start.** `livespec/hooks/livespec_footgun_guard.py` imports
`_vendor.returns` at module scope, but `_vendor/` lives at repo root, *outside* the
packaged `./livespec` subtree, so it is never shipped. In the install cache the
import raises `ModuleNotFoundError` before `main()`'s try/except is reached. The
process exits 1, Codex reports `PreToolUse Failed`, and **the tool call proceeds**.
The guard failed OPEN, silently, on every invocation.

Reproduced end-to-end on 2026-07-19 without touching tmux, using the guard's
unrelated `--no-verify` deny rule in a throwaway git repository: the guard was
invoked, `${CLAUDE_PLUGIN_ROOT}` resolved correctly, the import failed, and the
command executed unblocked. The same defect independently disabled the
`livespec-driver-claude` guard (`ModuleNotFoundError: returns`). Across both
runtimes, **8 of 12 active distributed hooks could not start** — including
`block_auto_memory.py`, which enforces the no-local-memory contract. Every one had
been inert in the install caches while CI stayed green, because the test suites run
under `uv`, where the dependency resolves, and never in the install shape.

Three structural facts established while diagnosing this, each of which defeats an
otherwise reasonable mitigation:

1. **A hook that crashes fails OPEN and is nearly invisible.** A non-zero exit
   surfaces only as a terse `PreToolUse Failed` line; the tool call proceeds
   normally. An unprotected runtime is indistinguishable from a protected one
   unless you probe it deliberately.
2. **Codex re-extracts its plugin cache on every run.** Patching a file in the
   cache is NOT a usable stopgap — it is silently reverted on the next invocation.
   A fix reaches Codex only by shipping in the released artifact.
3. **Codex silently skips UNTRUSTED hooks.** Editing a plugin's `hooks.json`
   invalidates its `trusted_hash`, after which every hook from that plugin is
   skipped with no warning at all. So `codex plugin add` alone does not confer
   protection, and any version bump can silently disarm the guard.

One piece of good news, which narrows the fix: Codex sends the **Claude-shaped**
payload (`tool_name: "Bash"`, `tool_input.command`), verified by recording live
hook input. The guards' classifiers and matchers are correct — both score 15/15 on
a hazard/benign corpus once importable. The defect was packaging, nothing else.

**The generalized lesson: a correct classifier is not a control.** "Merged" was
already known to be insufficient; this incident shows "installed" and even
"payload-verified" are also insufficient. A guard is only a control once it is
proven to FIRE and BLOCK in the runtime it defends. Verification must end with a
firing probe, not a unit test.

## Contributing cause — the reporting error that created false confidence

Before spawning the agent, the session reported the epic as "essentially built"
with a table of green rows, on the basis of **merge SHAs**. In reality **one of
five layers was live** (the host guard). The session then acted on its own false
report, believing the fleet was defended.

This violates the fleet's own standing rule (`CLAUDE.md`):

> "Done" means rolled out and exercised live — never merely merged + CI-green +
> AI-accepted.

## Hard rules this incident establishes

1. **Never put a destructive command in a sub-agent brief** — not as an example,
   not as a thing to "try", not even quoted. Describe the hazard class in prose
   and require verification by *classifier payload*, never by execution.
2. **Guard-testing is payload-only.** To prove a guard denies X, feed X as a
   string to the guard's stdin and read the verdict. Executing X to "see if it
   is blocked" risks the exact destruction the guard exists to prevent, and is
   never necessary.
3. **A hook covers exactly one runtime.** Before dispatching any agent, enumerate
   the runtime it will execute on (Claude Code / Codex / Fabro sandbox / raw
   subprocess) and confirm a guard covers *that* runtime. Coverage on one runtime
   is not coverage.
4. **Merged ≠ protected.** Never report a safety control as done, complete, or
   protecting anything until it is INSTALLED on the target runtime and
   demonstrated live with a payload.
5. **A script's internal subprocesses are invisible to a PreToolUse hook.** The
   hook sees only the top-level Bash command string. `python3 foo.py` is opaque.
   This is a structural limit of the L2 guard and is why L1 (env inversion)
   matters.
6. **Installed ≠ protected; only FIRING is protected.** Rule 4 was too weak. A
   guard can be installed, enabled, trusted, correctly wired, and classifying
   perfectly, and still defend nothing — because it crashes before it classifies.
   Verification of a safety control ends with a probe proving it BLOCKS in its own
   runtime, never with a unit test or a stdin corpus alone.
7. **Verify a control in its INSTALL shape, not its dev shape.** These guards
   passed CI for weeks because tests ran under `uv`, where the dependency
   resolves. Shipped hooks run under bare `python3` with no venv and no
   third-party packages. Any test that does not stage the packaged subtree alone
   and run it under a bare interpreter is testing something the user never runs.
8. **Prefer a firing probe whose failure mode is harmless.** A control can be
   proven live without ever risking what it protects: pick a payload the guard
   denies for an UNRELATED reason whose execution is inert (here, `git commit
   --no-verify` in a throwaway repository). If the guard fires you have your
   proof; if it does not, nothing is damaged. Never prove a tmux guard with a
   tmux command.

## Standing constraint until L1/L2 coverage is complete

Do NOT spawn a sub-agent on any runtime lacking a guard proven to FIRE (rule 6 —
installation is not sufficient evidence). If a Codex reviewer is wanted, ship,
install, and firing-verify the Codex guard FIRST (see `../handoff.md` step 1).
