# Incident record: dockershim never talked to podman's own daemon

Written 2026-08-17, closing out the agent-side work on `livespec-s43svm.21`
(INCIDENT: `database is locked` recurred after `.11`'s WAL fix). This note is
the durable technical record; the ledger timeline on `livespec-s43svm` and
`livespec-s43svm.21` carries the incident's dated status/handoff history —
read those for the minute-by-minute sequence, this note for the mechanism.

## The finding

`ci-runner/dockershim/docker` (in `livespec-dev-tooling`) wraps the system
`/usr/bin/docker` compat script, which is a bare `exec /usr/bin/podman "$@"`
— no `--remote`, no explicit API URL. Podman only switches into its
remote/daemon client mode on the `CONTAINER_HOST` environment variable (or an
explicit `--remote` flag). `DOCKER_HOST` — the only variable the GitHub
Actions container hooks, or this shim, ever set — does **not** trigger it.

Verified live on `poweredge-xubuntu` by watching `systemctl --user status
podman.service` immediately before and after each probe call:

- `podman ps` with only `DOCKER_HOST` set: `podman.service` stayed
  `inactive (dead)` throughout. LOCAL mode — podman opened the shared libpod
  SQLite state file directly, in the calling process.
- The same call with `CONTAINER_HOST` set instead: `podman.service`
  activated immediately via its systemd socket.

So every dockershim invocation — `create`, `start`, `exec`, `rm`,
`network` — has been hitting the shared SQLite state file directly, from a
fresh process per call, the entire time this pool has existed, **including**
throughout `.11`'s WAL-mode migration and its 6-hour "zero recurrence"
observation checkpoint. `podman.socket`/`podman.service` were already
installed, enabled, and listening on the host (systemd socket-activated,
single shared instance, not per-connection) — nothing needed provisioning.
The daemon existed and was simply never being talked to.

This is the exact CLI-per-invocation SQLite contention pattern podman's own
issue tracker documents as unresolved for concurrent multi-process usage —
[containers/podman#20563](https://github.com/containers/podman/issues/20563),
[#18356](https://github.com/containers/podman/issues/18356),
[#17859](https://github.com/containers/podman/issues/17859) — matching this
plan's own prior research note
(`k3s-arc-kueue-migration.md`, "Why the current architecture exists"):
"the community-validated complete fix for that class of problem is to route
all podman operations through one long-lived `podman system service`
daemon/connection-pool instead of N independent CLI processes." That note
was written as an argument for the k3s/ARC migration; this incident shows
the SAME fix also applies, cheaply, to the interim podman pool that is still
carrying production traffic during the migration window.

## The fix

`ci-runner/dockershim/docker` now exports `CONTAINER_HOST` unconditionally,
derived from the shim's own already-repaired `XDG_RUNTIME_DIR` (never
trusted from the inbound `DOCKER_HOST`/`CONTAINER_HOST`, following the same
discipline the shim already applies to `HOME`/`PATH` — the container hooks
hand it a scrubbed, foreign environment).

Landed: [livespec-dev-tooling PR #1466](https://github.com/thewoolleyman/livespec-dev-tooling/pull/1466)
(merged). Deployed live to `poweredge-xubuntu`'s
`/usr/local/lib/ci-runner/dockershim/docker`; the pre-fix version is backed
up at `/root/dockershim-docker.pre-fix-backup-20260817` on that host for
instant rollback (a plain `cp` back, no restore procedure).

## Load-test evidence and its honest limit

Two independent synthetic load tests on `poweredge-xubuntu` (real host, real
podman, real WAL-mode SQLite, throwaway containers only — zero real CI
traffic reached the host at any point; `CI_RUNNER_LABELS` stayed forced to
`["ubuntu-latest"]` fleet-wide throughout both):

1. 150 concurrent workers × 4 lifecycles (create → start → 8× exec with real
   disk I/O → rm), `alpine:latest` — 600 lifecycles, ~6600 ops.
2. The same, but each lifecycle also does `network create` before and
   `network prune` after — the shim's own original 2026-07-14 historical bug
   shape (concurrent-removal-vs-prune race) — 600 lifecycles, ~9000 ops,
   7m26s (baseline) / 5m15s (fixed) wall-clock.

Both passes: **zero failures on either shim version**, and `podman.service`
journal/status confirms the mechanism directly — inactive the entire
baseline window, continuously active as one process for the entire fixed
window (daemon `Duration` matched test wall-clock within seconds both
times). Pass 2 also showed the fixed shim using ~3.3× less CPU time (4m41s
vs 15m32s user time) — plausibly relevant to `.11`'s original framing
(container init/teardown overhead dominating job wall-clock), worth
re-measuring once this is under real traffic.

**Neither pass reproduced `database is locked`, including the unpatched
baseline**, despite host load average reaching 56.52 (1-min) — above the
23.95 (15-min) recorded in the actual incident. Two synthetic bursts,
~1200 lifecycles / ~15000 ops total, without reproducing it once. Read this
as a limit of the test harness, not as evidence the original bug is absent:
real CI jobs run far more exec steps per container, over longer wall-clock,
with real image pulls and real Actions-runner-agent-driven timing, at up to
482 concurrent slots against my 150, sustained over hours across multiple
repos rather than a single several-minute burst. The fix's justification
rests on the **mechanistic proof** (the daemon was never used before, is now
used continuously and correctly, with no regression) — not on
failure-reproduction, which was never established as a reliable baseline to
compare against in the first place.

## What is still open

A real-traffic observation window (mirroring `.11`'s own precedent) is the
only way to close the gap the synthetic tests could not. That requires
reverting `CI_RUNNER_LABELS` on some scope — a maintainer decision, not an
agent one, given the mitigation was maintainer-directed and explicitly held
pending proof. See `livespec-s43svm.21` for the live disposition.
