# Dispatcher drain operations — driving a repo's ready queue through the factory

Read this when operating the Beads/Dolt + Fabro Dispatcher directly against a
fleet repo's ready work-item queue: launching `dispatcher.py loop`, authorizing
a held item, or walking a queue down to empty. These are operational facts about
the running factory that no other artifact records; the Dispatcher's own
invocation contract, its policy settings, and the post-merge acceptance lanes
live in `livespec-orchestrator-beads-fabro`'s `SPECIFICATION/contracts.md` and
`SPECIFICATION/scenarios.md`.

## Pass `--fabro-bin` explicitly — PATH resolution does not survive the wrapper

The credential wrapper that injects the tenant `BEADS_DOLT_PASSWORD` and the
GitHub App environment scrubs `PATH`. A dispatch that relies on PATH to find the
Fabro engine therefore dies with `fabro engine binary not resolvable`, which
reads like a missing install but is purely an environment artifact. Always name
the binary on the command line:

```bash
--fabro-bin /home/ubuntu/.fabro/bin/fabro
```

Treat the flag as mandatory in every real invocation, not as an override for
unusual setups.

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
