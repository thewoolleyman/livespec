# Dispatcher drain operations — driving a repo's ready queue through the factory

Read this when operating the Beads/Dolt + Fabro Dispatcher directly against a
fleet repo's ready work-item queue: launching `dispatcher.py loop`, authorizing
a held item, or walking a queue down to empty. These are operational facts about
the running factory that no other artifact records; the Dispatcher's own
invocation contract, its policy settings, and the post-merge acceptance lanes
live in `livespec-orchestrator-beads-fabro`'s `SPECIFICATION/contracts.md` and
`SPECIFICATION/scenarios.md`.

## `--fabro-bin` is an OVERRIDE, not a requirement — corrected 2026-07-21

> **This section previously said the flag was "mandatory in every real
> invocation". That is no longer true, and following it literally blocks the
> sanctioned path — `drive` accepts no such flag.**

The underlying hazard was real: the credential wrapper that injects the tenant
`BEADS_DOLT_PASSWORD` and the GitHub App environment scrubs `PATH`, so a bare
`fabro` PATH lookup fails and the dispatch dies with `fabro engine binary not
resolvable` — which reads like a missing install but is an environment artifact.

**That bug is FIXED at the resolver.** `resolve_fabro_bin` (orchestrator
`commands/_config.py`) resolves **env > config > default**:

1. a non-empty `LIVESPEC_FABRO_BIN`;
2. else `.livespec.jsonc` `dispatcher.fabro_bin`;
3. else `_default_fabro_bin()`, which probes the ABSOLUTE `$HOME/.fabro/bin/fabro`
   FIRST (the wrapper preserves `HOME` even while scrubbing `PATH` — this is the
   fix), then falls back to a `PATH` lookup (which is what resolves inside the
   orchestrator container, where `fabro` lives at `/usr/local/bin/fabro`).

An explicit `--fabro-bin <path>` still wins outright, so passing it is harmless.
It is simply not required, and treating it as required creates a contradiction:
**the sanctioned `drive --action impl:<id>` path exposes no `--fabro-bin` flag at
all.** An operator reading the old text would conclude the sanctioned path could
not be used.

Verified by observation 2026-07-21, not by reading the resolver: `drive --action
impl:livespec-runtime-jo9` was invoked with NO `--fabro-bin` and a sandbox came
up (`fabro-run-…`, image `livespec-fabro-sandbox:python-agent-v0.51.7`).

Pass the flag when you deliberately want a non-default engine. Otherwise let the
resolver do its job.

## A backgrounded `drive` DETACHES — its exit code and log tell you nothing

`drive.py` re-invokes itself under the credential wrapper when the required
credential env is absent (`sudo` → `with-livespec-env.sh` → `op run` → python).
Run it in the background and **the parent returns almost immediately with exit 0
and a log containing one line**:

    livespec: required credential env absent; re-invoking under credential_wrapper

The real dispatch continues in the detached child. So a background-task
"completed, exit code 0" notification fires on the PARENT, minutes before the
dispatch is anywhere near done, and the tiny log looks exactly like a run that
died on startup. **Neither signal carries information about the dispatch.**

This is the same family as the recorded trap where a dispatch reported `exit 0`
while its status was `failed` — but pointed the other way: here exit 0 plus an
empty-looking log accompanies a dispatch that is running perfectly.

**Query the authoritative signals instead** — to confirm a dispatch is RUNNING,
all three agree or you do not have an answer:

```bash
pgrep -af "drive.py|dispatcher.py"          # the wrapper/op-run/python chain
docker ps --format '{{.Names}}\t{{.Image}}' # a fabro-run-* sandbox is UP
bd show <work-item-id>                      # status: active, assignee: fabro
```

### ⚠ THE SANDBOX EXITING IS NOT THE DISPATCH FINISHING

The three signals above answer "is it running", **not "is it done" — and the
container is the wrong one to wait on.** The Fabro sandbox exits when the CODING
work ends; the post-merge janitor, the acceptance pass, and the ledger close all
run **host-side afterwards**. Measured on one real dispatch:

    16:13:13Z  fabro-run            exit 0      <- container gone HERE
    16:14:51Z  janitor-checkout-add
    16:15:56Z  janitor-post-merge   green
    16:15:58Z  ledger-complete / acceptance-ai-pass
    16:16:03Z  ledger-accept / auto-disposition
    16:16:05Z  outcome                          <- actually done HERE, ~3 min later

So a watcher armed on `docker ps` fires while the janitor is still running, and the
journal at that moment ends mid-janitor with no outcome — which reads exactly like a
dispatch that died. **Do not conclude anything from a partial journal tail.**

**Wait on the dispatch PID, not the container**, and note the `pgrep` self-match
footgun: an `until ! pgrep -f "drive.py"` loop matches its own argv and never exits.
Wait on the concrete pid instead:

```bash
while kill -0 <drive-pid> 2>/dev/null; do sleep 60; done
```

**The terminal signal is the journal's `outcome` event**, which carries the verdict,
`merge_sha`, and `pr_number`. Cross-check it against GitHub and the ledger — never
trust the dispatcher's own summary alone. And filter every journal read on the `at`
field against an explicit cutoff: the file is re-opened and rewritten, so a
follow-by-name tail replays its entire history as if live.

## Factory dispatch is strictly sequential — one Fabro run at a time

Fabro sandboxes run with `--network host`, so two concurrent runs collide on the
host network namespace. There is no supported parallel drain: hold every
dispatch to `--budget 1 --parallel 1` and let each item finish before starting
the next. (The sanctioned `drive --action impl:<id>` path emits exactly this
pair; a hand-driven `dispatcher.py loop` must match it.)

## Never hand-edit a beads `admission:*` label — use the valve

An item whose effective admission policy is `manual` is held at the gate and
will not dispatch. The fix is never to write or edit the `admission:*` label on
the beads record by hand; authorize the item through the sanctioned valve, which
records the policy edit through the orchestrator's own surface:

```bash
drive --action set-admission:<work-item-id>:auto
```

Hand-writing the label bypasses that surface and leaves the authorization
unattributable — the very thing the valve exists to prevent. The valve itself is
specified in `livespec-orchestrator-beads-fabro`'s `SPECIFICATION/scenarios.md`;
what belongs here is the prohibition on going around it.

## Re-enumerate the ready queue on every iteration

A ready set is a point-in-time snapshot that goes stale the moment you act on
it: the item you just closed leaves the queue, and accepting it can unblock its
dependents, which enter. Never cache the enumeration across iterations and walk
it as a fixed list — re-run the ranked enumeration at the top of each pass and
take the top-ranked item from the fresh result.
