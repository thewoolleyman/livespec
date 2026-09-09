# Inventory: `fabro-hosts` services estate (Ansible-migration Phase 0 sizing)

Source: `/data/projects/fabro-hosts` at `master` HEAD (clean), read 2026-09-09.
Scope: every file under `services/` plus the three root files. 65 files, 65 rows.
Serves livespec work-item `livespec-sab5gn.4`.

Hosts this repo provisions: `hp-xubuntu` (HP box, tailnet; shell is
`tailscale ssh cwoolley@hp-xubuntu`; `hostname -s` = `hp-xubuntu`) and `vps`
(Contabo, the maintainer's dev host; `hostname -s` = `vmi3006760`, tailnet label
`vps`). The hostname/label split on `vps` shapes every host guard in the repo.

Classes: (a) HOST GLUE, migrates to Ansible; (b) KUBERNETES-DECLARATIVE;
(c) DEAD; (d) REPO-SIDE, not host plumbing; (e) INTERACTIVE / OUT-OF-BAND step
or runtime secret, flagged in addition to the row's class.

Column key: `host(s)` is derived from BOTH `hosts/*.env` presence AND what
`install.sh` actually does (every installer refuses to run unless the env
file's recorded system hostname equals `hostname -s`, so an env file's presence
IS the host set). `runs as` is the user the artifact executes as on the host
(installer = who runs it; unit = `User=`; script = who invokes it).

## Cross-cutting convention every service shares (read once, applies to all `install.sh` rows)

- Every `install.sh` is run **on the host being provisioned**, as root
  (`sudo ./install.sh hosts/<host>.env`), from a git clone of this repo,
  with cwd = the service directory (env path is cwd-relative).
- Guard order is identical everywhere: `require_root` → `require_host_matches`
  (`hostname -s` must equal the env's `*_SYSTEM_HOSTNAME`; only
  `fabro-server/install.sh` also accepts the tailnet DNS label from
  `tailscale status --self --json`) → `require_inputs` → install files →
  verify (dry run / PING / web probe) → `systemctl enable` + `start`/`restart`.
- Every `render-unit.sh` sources the env file with `set -a`, strips the
  template header up to `[Unit]`, substitutes `@NAME@` placeholders, and exits
  4 if any `@[A-Z_]+@` remains. This is exactly Ansible `template:` plus
  `host_vars`; the placeholder guard becomes Jinja's `StrictUndefined`.
- Ansible mapping of the host guard: inventory targeting replaces
  `require_host_matches`; keep an `assert:` on `ansible_hostname` if the
  vps `vmi3006760` mismatch is to stay visible.

## Table

| path | one-line purpose | host(s) | what it puts on the host | runs as | class | reason |
|---|---|---|---|---|---|---|
| **root** | | | | | | |
| `.gitignore` | ignores `.idea/`, `tmp/`, `*.rendered` (rendered-unit scratch) | n/a | nothing | n/a | d | repo hygiene only |
| `AGENTS.md` | agent/operator conventions (one-rule, verify-before-change, merging-is-not-deploying, host operating rules) | n/a | nothing | n/a | d | documentation; see CONVENTION section |
| `README.md` | fleet charter, host table, service table, layout, quickstart, why-a-fleet-repo history | n/a | nothing | n/a | d | documentation; see CONVENTION section |
| **services/container-reclaim/** | | | | | | |
| `container-reclaim/README.md` | measurement, derived 48h/72h horizons, safety model, mutation record | n/a | nothing | n/a | d | documentation |
| `container-reclaim/container-reclaim.service.in` | oneshot unit template running the installed reclaimer with `--apply`; `After=/Wants=docker.service`, `Nice=10`, idle IO, 1h timeout. Placeholders: `@RECLAIM_SERVICE_USER@`, `@RECLAIM_SERVICE_GROUP@` (from `hosts/hp-xubuntu.env` AND `hosts/vps.env`, both `root`), `@RECLAIM_HOST_ENV_DEST@` (NOT in env; hardcoded by `render-unit.sh` to `/usr/local/libexec/container-reclaim.env`) | both | `/etc/systemd/system/container-reclaim.service` (0644 root) | unit runs as root (`User=root`) | a | Ansible `template:` + host_vars; identical render on both hosts today |
| `container-reclaim/container-reclaim.timer.in` | timer template. Placeholder: `@RECLAIM_ON_CALENDAR@` (both env files: `hourly`); `RandomizedDelaySec=30m`, `Persistent=true` | both | `/etc/systemd/system/container-reclaim.timer` | systemd | a | Ansible `template:` + `systemd: enabled/started` |
| `container-reclaim/container-reclaim.sh` | the reclaimer: resolves docker/containerd store root from the daemon, prunes exited containers older than N hours then images older than M hours + builder cache; dry-run by default. Reads at runtime from the installed env: `RECLAIM_CANONICAL_HOST`, `RECLAIM_SYSTEM_HOSTNAME` (re-guards `hostname -s`), `RECLAIM_CONTAINER_IDLE_HOURS`, `RECLAIM_IMAGE_IDLE_HOURS` | both | `/usr/local/libexec/container-reclaim.sh` (0755 root) | root (via unit; exits 4 if a non-root dry run cannot read the store) | a | `copy:` with mode; script body stays as-is |
| `container-reclaim/container-reclaim.test.sh` | safety-model tests with stubbed `docker`/`containerd` on PATH; mutation-checked | n/a | nothing | developer | d | test suite |
| `container-reclaim/hosts/hp-xubuntu.env` | hp values: canonical host, system hostname `hp-xubuntu`, user/group root, 48h/72h, `hourly`; long derivation comments | hp-xubuntu | copied verbatim to `/usr/local/libexec/container-reclaim.env` (0644 root) | n/a | a | becomes `host_vars/hp-xubuntu.yml`; file is ALSO shipped to the host and read by the script at runtime, so Ansible must still `template:`/`copy:` it (or rewrite the script to take vars) |
| `container-reclaim/hosts/vps.env` | vps values: same keys; system hostname `vmi3006760` (not `vps`) | vps | `/usr/local/libexec/container-reclaim.env` | n/a | a | `host_vars/vps.yml`; same shipped-env caveat |
| `container-reclaim/install.sh` | installer: root + hostname guard; requires `docker` CLI, reachable daemon, daemon-reported data-root; installs script + env + two rendered units; `daemon-reload`; dry-runs installed script; `enable`+`start` timer; exit 7 if timer not active | both | see rows above; unit `container-reclaim.timer` enabled+started | root (sudo) | a | whole body is `copy`/`template`/`systemd` tasks plus a dry-run `command:` verify |
| `container-reclaim/install.test.sh` | render + host-guard tests; asserts renderer reads the env (synthetic sentinel) | n/a | nothing | developer | d | test suite |
| **services/disk-guard/** | | | | | | |
| `disk-guard/README.md` | relocation record of the 2026-08-22 hp hotfix, five live sha256 digests, host values, mutation record | n/a | nothing | n/a | d | documentation |
| `disk-guard/disk-guard.service.in` | oneshot unit `ExecStart=/usr/local/sbin/disk-guard.sh` (no args), `After=docker.service`; **no placeholders** (`REQUIRED=()`); renders byte-identical to hp's live unit (sha256 `6e9151bb…`) | hp-xubuntu | `/etc/systemd/system/disk-guard.service` | unit runs as root (no `User=`) | a | `copy:` (nothing varies); digest fidelity test moves to a CI/molecule assert |
| `disk-guard/disk-guard.timer.in` | timer: `OnBootSec=10m`, `OnUnitActiveSec=15m`; no placeholders; live sha256 `cf32d235…` | hp-xubuntu | `/etc/systemd/system/disk-guard.timer` | systemd | a | `copy:` + `systemd:` |
| `disk-guard/docker-prune.service.in` | oneshot: three `ExecStart` lines — `docker container prune -f --filter until=24h`, `docker image prune -a -f --filter until=72h`, `docker builder prune -a -f`; `Requires=docker.service`; no placeholders; `Documentation=` still names `livespec-orchestrator-beads-fabro` (preserved live content); live sha256 `7e49c0f2…` | hp-xubuntu | `/etc/systemd/system/docker-prune.service` | root | a | `copy:`; this IS the "docker prune timer" class named in the brief |
| `disk-guard/docker-prune.timer.in` | timer: `OnCalendar=daily`, `RandomizedDelaySec=30m`, `Persistent=true`; no placeholders; live sha256 `e90c298d…` | hp-xubuntu | `/etc/systemd/system/docker-prune.timer` | systemd | a | `copy:` + `systemd:` |
| `disk-guard/disk-guard.sh` | POSIX-sh low-water guard: reads `DISK_GUARD_THRESHOLD_GB` from `/usr/local/libexec/disk-guard.env` (or a path arg); compares `df` avail of `/` vs the docker data-root fs; below threshold prunes containers/images/builder with no age filter, `journalctl --vacuum-size=200M`, `apt-get clean`, logs via `logger -t disk-guard`; `--dry-run` reports only | hp-xubuntu | `/usr/local/sbin/disk-guard.sh` (0755 root) — the LIVE hotfix path, deliberately not `libexec` | root (via unit) | a | `copy:`; note the destination is a legacy path the unit hardcodes |
| `disk-guard/disk-guard.test.sh` | guard-logic tests with stubbed `df`/`docker`/`journalctl`/`apt-get`/`logger`; runs script through `/bin/sh` | n/a | nothing | developer | d | test suite |
| `disk-guard/hosts/hp-xubuntu.env` | three keys: `DISK_GUARD_CANONICAL_HOST`, `DISK_GUARD_SYSTEM_HOSTNAME=hp-xubuntu`, `DISK_GUARD_THRESHOLD_GB=40` | hp-xubuntu | copied to `/usr/local/libexec/disk-guard.env` (0644 root) | n/a | a | `host_vars`; shipped-env caveat (script reads it at runtime) |
| `disk-guard/install.sh` | installer: root + hostname guard; requires templates, integer threshold, `docker` + reachable daemon + data-root, and `journalctl`/`apt-get`/`logger`/`df` on PATH; prints sha256 of any file it replaces; installs script (to sbin), env, four rendered units; `daemon-reload`; `--dry-run` verify; enables+starts BOTH timers | hp-xubuntu | see rows above; `disk-guard.timer` + `docker-prune.timer` enabled+started | root (sudo) | a (+e) | `copy`/`template`/`systemd`; (e) operator is expected to compare the printed pre-replacement digests against README's table |
| `disk-guard/install.test.sh` | render byte-fidelity to the five live digests, host guard both directions, installer destination == unit `ExecStart` | n/a | nothing | developer | d | test suite |
| `disk-guard/render-unit.sh` | renders any of the four unit templates by full unit name; requires `DISK_GUARD_SYSTEM_HOSTNAME` + `DISK_GUARD_THRESHOLD_GB` present even though no placeholder consumes them; hardcodes `DISK_GUARD_HOST_ENV_DEST=/usr/local/libexec/disk-guard.env` (unused by any template today) | hp-xubuntu | nothing directly (stdout consumed by `install.sh`) | root at install; developer for diffing | a | replaced entirely by Ansible `template:` |
| **services/fabro-server/** | | | | | | |
| `fabro-server/README.md` | the runbook: instance model (`fabro-server` + `fabro-server-mi-homelab` per host), launch invariants, five measured per-host axes, install/repair, verification, settings-not-installed rationale, known gaps | n/a | nothing | n/a | d | documentation |
| `fabro-server/check-settings.sh` | operator drift checker run ON the host: sources env, reads `FABRO_DEV_TOKEN` from `<FABRO_HOME_DIR>/storage/server.env`, `curl -H Authorization: Bearer … http://127.0.0.1:<port>/api/v1/settings`, compares each `key=value` line of `hosts/<host>.settings.expected` via `jq`; separately parses `[cli.target] url` out of `settings.toml` with awk (`read_cli_target_url`). Not installed by `install.sh`. Invoked by: the operator by hand (README/AGENTS.md "measure the live hosts"), and `check-settings.test.sh` (sources it for the awk function only) | both (all four env files) | nothing | the service account (must read the 0600 `server.env`) | d (+e) | not host plumbing: nothing installs it; it is a verification instrument run from the checkout. Under Ansible it maps to an optional `uri:` + `assert:` verification play, not to a deployed file. (e) reads a runtime secret (`FABRO_DEV_TOKEN`), probe-only |
| `fabro-server/check-settings.test.sh` | fixture tests for `read_cli_target_url` (sibling `url` keys, missing table/key, whitespace, dotted subtable); mutation-checked | n/a | nothing | developer | d | test suite |
| `fabro-server/fabro-server-verify-web` | readiness gate used as `ExecStartPost`: loops `FABRO_WEB_VERIFY_ATTEMPTS` (default 60) times fetching `/runs` and `/login` with `Host:` + `Accept: text/html`, requires `<title>Fabro</title>`, then fetches the first referenced `.js` bundle; env: `FABRO_BASE_URL` (default `http://127.0.0.1:32276`), `FABRO_CANONICAL_HOST` (default `vps.perch-rudd.ts.net:32276`), `FABRO_WEB_VERIFY_ATTEMPTS` | both | `/usr/local/libexec/fabro-server-verify-web` (0755 root), one shared copy per host | the unit's user at start (`ExecStartPost`); root during `install.sh`'s own verify | a | `copy:`; host-invariant because the unit supplies the env |
| `fabro-server/fabro-server.service.in` | the server unit template. `Type=simple`, `Restart=always`, `After/Wants=network-online docker tailscaled`, `EnvironmentFile=@FABRO_HOME_DIR@/storage/server.env`, `UnsetEnvironment=ANTHROPIC_API_KEY OPENAI_API_KEY`, `ExecStart=@FABRO_HOST_HOME@/.fabro/bin/fabro server start --foreground --bind 127.0.0.1:@FABRO_PORT@ --web --no-upgrade-check --storage-dir @FABRO_HOME_DIR@/storage --config @FABRO_HOME_DIR@/settings.toml`, `ExecStartPost=/usr/local/libexec/fabro-server-verify-web`. Placeholders: `@FABRO_UNIT_NAME@`, `@FABRO_HOST_USER@`, `@FABRO_HOST_GROUP@`, `@FABRO_HOST_HOME@`, `@FABRO_WEB_VERIFY_ATTEMPTS@`, `@FABRO_CANONICAL_HOST@`, `@FABRO_PORT@`, `@FABRO_HOME_DIR@`, `@FABRO_HOST_CHECKOUT@`. Supplied by all four `hosts/*.env`; `FABRO_UNIT_NAME`/`FABRO_HOME_DIR`/`FABRO_PORT` are DEFAULTED by `render-unit.sh` (`fabro-server`, `$FABRO_HOST_HOME/.fabro`, `32276`) for `vps.env`/`hp-xubuntu.env` and set explicitly in the two `*-mi-homelab.env` files | both, two instances each | `/etc/systemd/system/<FABRO_UNIT_NAME>.service` (`fabro-server.service` and `fabro-server-mi-homelab.service` on each host) | unit runs as `FABRO_HOST_USER` (`ubuntu` on vps, `cwoolley` on hp) | a | `template:` with host_vars + a per-instance loop var; defaults become role defaults |
| `fabro-server/hosts/hp-xubuntu-mi-homelab.env` | org-instance values on hp: user/group/home `cwoolley`, checkout `/home/cwoolley/repos/livespec-orchestrator-beads-fabro`, canonical host `hp-xubuntu.perch-rudd.ts.net:32277`, attempts 300, unit `fabro-server-mi-homelab`, home dir `~/.fabro-mi-homelab`, port 32277, cli target loopback:32277, max runs 5, app id 4688510 | hp-xubuntu | not shipped (consumed by renderers/installer only) | n/a | a | `host_vars` (instance entry) |
| `fabro-server/hosts/hp-xubuntu-mi-homelab.settings.expected` | expected resolved settings for that instance (`max_concurrent_runs=5`, web/api URLs on :32277, listen `127.0.0.1:32277`, app_id 4688510) | hp-xubuntu | nothing | n/a | d | fixture consumed by `check-settings.sh`; brief classes `.settings.expected` as repo-side |
| `fabro-server/hosts/hp-xubuntu.env` | fleet-instance values on hp: `cwoolley`, `/home/cwoolley`, checkout under `~/repos`, canonical `hp-xubuntu…:32276`, attempts 300, cli target loopback, max runs 15, app id 3668528 | hp-xubuntu | not shipped | n/a | a | `host_vars` |
| `fabro-server/hosts/hp-xubuntu.settings.expected` | expected resolved settings for hp fleet instance (`max_concurrent_runs=15`, :32276 URLs, app_id 3668528) | hp-xubuntu | nothing | n/a | d | fixture for `check-settings.sh` |
| `fabro-server/hosts/vps-mi-homelab.env` | org-instance values on vps: `ubuntu`, `/home/ubuntu`, checkout `/data/projects/livespec-orchestrator-beads-fabro`, canonical `vps…:32277`, unit `fabro-server-mi-homelab`, home `~/.fabro-mi-homelab`, port 32277, max runs 3, app id 4688510 | vps | not shipped | n/a | a | `host_vars` (instance entry) |
| `fabro-server/hosts/vps-mi-homelab.settings.expected` | expected resolved settings for vps org instance (`max_concurrent_runs=3`, :32277) | vps | nothing | n/a | d | fixture for `check-settings.sh` |
| `fabro-server/hosts/vps.env` | fleet-instance values on vps: `ubuntu`, `/home/ubuntu`, `/data/projects/…`, canonical `vps…:32276`, attempts 300, max runs 10, app id 3668528 | vps | not shipped | n/a | a | `host_vars` |
| `fabro-server/hosts/vps.settings.expected` | expected resolved settings for vps fleet instance (`max_concurrent_runs=10`, :32276) | vps | nothing | n/a | d | fixture for `check-settings.sh` |
| `fabro-server/install.sh` | installer: root guard; host guard accepts OS hostname OR tailnet label (`tailscale status --self --json` → `.Self.DNSName`); requires `otel.conf`, verifier, `<HOME>/.fabro/bin/fabro` executable, checkout dir, `server.env` with non-empty `SESSION_SECRET=` and `FABRO_DEV_TOKEN=` lines (grep presence only), `curl`, `jq`; refuses if the instance's `/api/v1/health` answers and `fabro --json ps` (as the service user, `FABRO_SERVER=http://127.0.0.1:<port>`) lists active runs (exit 3); stops a legacy non-systemd daemon by PID from `<HOME_DIR>/storage/server.json` only if `/proc/<pid>/exe` matches the trusted binary; installs verifier + rendered unit + `otel.conf` drop-in; deletes legacy `verify-timeout-override.conf` drop-in; `daemon-reload`; `enable` + `restart`; runs the verifier with the instance's host/port; asserts MainPID cwd == checkout (exit 7) | both, per instance (run once per env file) | `/usr/local/libexec/fabro-server-verify-web`; `/etc/systemd/system/<unit>.service`; `/etc/systemd/system/<unit>.service.d/otel.conf`; removes `…/<unit>.service.d/verify-timeout-override.conf`; unit enabled + restarted | root (sudo); `fabro ps` probe as the service user | a (+e) | `copy`/`template`/`file: state=absent`/`systemd` + pre-task assertions; (e) see the out-of-band list: binary build, `server.env` creation, `settings.toml`, GitHub App key, `tailscale serve` are all outside this installer |
| `fabro-server/install.test.sh` | sources `install.sh` with a real env, stubs `hostname` via PATH shim; positive + cross-host refusal cases; asserts no two env files on a host share a port or state dir | n/a | nothing | developer | d | test suite |
| `fabro-server/otel.conf` | systemd drop-in: `OTEL_EXPORTER_OTLP_ENDPOINT=http://172.17.0.1:4318`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`, `OTEL_SERVICE_NAME=fabro`; host-invariant (docker bridge gateway is 172.17.0.1 on both) | both per `install.sh` (installed unconditionally); README "Known gaps" records vps had NO otel.conf as of 2026-08-19, so an install on vps newly adds OTLP export | `/etc/systemd/system/<unit>.service.d/otel.conf` (0644 root) | n/a (read by systemd) | a (+e) | `copy:` drop-in; (e) README asks for a deliberate decision before installing it on vps ("a behavior change, not a transcription") |
| `fabro-server/render-settings.sh` | renders `settings.toml.in` for one host to stdout; requires `FABRO_CANONICAL_HOST`, `FABRO_CLI_TARGET_URL`, `FABRO_MAX_CONCURRENT_RUNS`, `FABRO_GITHUB_APP_ID`, `FABRO_PORT`; defaults the instance axis; exit codes 2/3/4 mirror `render-unit.sh`. NOT called by `install.sh` | both (four env files) | nothing (operator diffs stdout against `~/.fabro/settings.toml` by hand) | operator / developer | a (+e) | the renderer half of a `template:`; (e) applying its output is a documented manual step today |
| `fabro-server/render-settings.test.sh` | renderer tests (exit codes, placeholder coverage, opportunistic diff against a live `settings.toml` when readable); mutation-checked | n/a | nothing | developer | d | test suite |
| `fabro-server/render-unit.sh` | renders `fabro-server.service.in`; REQUIRED list = the nine placeholders above; defaults `FABRO_UNIT_NAME`/`FABRO_HOME_DIR`/`FABRO_PORT`; exit 2/3/4 guard rails | both | nothing directly (stdout consumed by `install.sh`) | root at install; developer for diffing | a | replaced by `template:` |
| `fabro-server/settings.toml.in` | Fabro server `settings.toml` template: `[cli.target] url=@FABRO_CLI_TARGET_URL@`, `[server.api] url=https://@FABRO_CANONICAL_HOST@/api/v1`, `[server.auth] methods=["dev-token"]`, `[server.integrations.github] strategy="app", app_id=@FABRO_GITHUB_APP_ID@`, `[server.listen] address=127.0.0.1:@FABRO_PORT@`, `[server.scheduler] max_concurrent_runs=@FABRO_MAX_CONCURRENT_RUNS@`, `[server.web] enabled=true, url=https://@FABRO_CANONICAL_HOST@`. Carries no secrets. **Rendered but never installed** by any script in the repo (deliberate; vps's live file is hand-maintained) | both (four env files) | intended destination `<FABRO_HOME_DIR>/settings.toml` (mode/owner unspecified; owned by the service user in practice) | n/a | a (+e) | it is precisely an Ansible `template:` with `--check --diff`; the README's stated precondition for wiring it ("carry a dry-run diff against the live file before it writes") is Ansible's native check mode. (e) today an operator applies the render by hand |
| **services/host-tools/** | | | | | | |
| `host-tools/README.md` | what `btop-loop` is, why no unit, provenance + cross-fleet digest pin, rollout record | n/a | nothing | n/a | d | documentation |
| `host-tools/btop-loop` | bash wrapper that reruns `btop "$@"` after abnormal exit, restoring the terminal (`tput rmcup/cnorm`, `stty sane`); sha256 `c570ef8a…768c27`, byte-identical to `livespec-dev-tooling`'s `ci-runner/k3s/phase2/host-tools/btop-loop` | hp-xubuntu (vps gets the same file from `vps-info/services/btop-loop/`) | `/usr/local/bin/btop-loop` (0755 root) | the interactive operator who types it | a | `copy:`; a cross-repo digest assert belongs in CI, not the play |
| `host-tools/hosts/hp-xubuntu.env` | two keys, both guard-only: `HOST_TOOLS_CANONICAL_HOST`, `HOST_TOOLS_SYSTEM_HOSTNAME=hp-xubuntu` | hp-xubuntu | not shipped | n/a | a | `host_vars` (collapses to inventory membership under Ansible) |
| `host-tools/install.sh` | installer with no unit: root + hostname guard; requires each tool present, executable, `bash -n` clean, AND `btop` already on PATH (refuses otherwise, suggests `apt-get install -y btop`); prints digest of any file it replaces; `install -m 0755` to `/usr/local/bin`; verifies `command -v` resolves to the just-installed digest | hp-xubuntu | `/usr/local/bin/btop-loop` | root (sudo) | a (+e) | `copy:` + `package:`; (e) `btop` install is a documented human precondition the script refuses to perform |
| `host-tools/install.test.sh` | 16 cases: guards both directions, digest pin, structural assertion that `install.sh` contains no `systemctl` call; mutation-checked | n/a | nothing | developer | d | test suite |
| **services/sccache-redis/** | | | | | | |
| `sccache-redis/README.md` | why a RAM-only redis on the docker bridge gateway, trust boundary (sandboxes are writers, no auth), LRU eviction decision, live checks, Honeycomb after-measure | n/a | nothing | n/a | d | documentation |
| `sccache-redis/hosts/hp-xubuntu.env` | hp values: `SCCACHE_REDIS_SYSTEM_HOSTNAME=hp-xubuntu`, canonical host, `SCCACHE_REDIS_CONTAINER=sccache-redis`, `SCCACHE_REDIS_BIND_ADDR=172.17.0.1`, `SCCACHE_REDIS_PORT=6379`, `SCCACHE_REDIS_IMAGE=docker.io/library/redis:8.8.2-alpine@sha256:96cb544f…`, `SCCACHE_REDIS_MAXMEMORY=4gb`, `SCCACHE_REDIS_CONTAINER_MEMORY=5g`; explicitly NOT written for vps (Python-only consumers) | hp-xubuntu | not shipped | n/a | a | `host_vars` |
| `sccache-redis/install.sh` | installer: root + hostname guard; requires `docker` CLI + daemon; asserts `docker network inspect bridge` gateway == `SCCACHE_REDIS_BIND_ADDR`; installs rendered unit; `daemon-reload`; `enable` + `restart`; polls up to 30 s for `docker exec sccache-redis redis-cli -h <bind> -p <port> ping` == PONG and prints `maxmemory` (exit 6 on failure). No dry run, not sourceable | hp-xubuntu | `/etc/systemd/system/sccache-redis.service`, enabled + restarted | root (sudo) | a | `template:` + `systemd:` + `command:` verify with `until:` |
| `sccache-redis/install.test.sh` | render carries bind/port/maxmemory/image, header stripped, host guard | n/a | nothing | developer | d | test suite |
| `sccache-redis/render-unit.sh` | renders `sccache-redis.service.in`; REQUIRED: `SCCACHE_REDIS_CONTAINER`, `SCCACHE_REDIS_BIND_ADDR`, `SCCACHE_REDIS_PORT`, `SCCACHE_REDIS_IMAGE`, `SCCACHE_REDIS_MAXMEMORY`, `SCCACHE_REDIS_CONTAINER_MEMORY` | hp-xubuntu | nothing directly | root at install | a | replaced by `template:` |
| `sccache-redis/sccache-redis.service.in` | long-running unit: `Type=simple`, `Requires=docker.service`, `ExecStartPre=-docker rm -f @SCCACHE_REDIS_CONTAINER@`, `ExecStart=docker run --rm --name … --publish @BIND@:@PORT@:6379 --memory @CONTAINER_MEMORY@ --read-only --tmpfs /data --user 999:999 --log-driver journald @IMAGE@ redis-server --bind 0.0.0.0 --protected-mode no --maxmemory @MAXMEMORY@ --maxmemory-policy allkeys-lru --save "" --appendonly no …`, `ExecStop=docker stop -t 10`, `Restart=always`. Placeholders: the six above, all from `hosts/hp-xubuntu.env` | hp-xubuntu | `/etc/systemd/system/sccache-redis.service` | systemd runs `docker run` as root; redis inside the container as uid/gid 999 | a | `template:`; the image pull happens at unit start (see DOWNLOADS) |
| **services/storage-reclaim/** | | | | | | |
| `storage-reclaim/README.md` | why (231.7 GB of worktree build artifacts on vps), two legs, derived 14d/30d horizons, safety model, mutation record, hosts table; carries a now-stale note that `fabro-server/install.sh` cannot run on vps | n/a | nothing | n/a | d | documentation |
| `storage-reclaim/hosts/hp-xubuntu.env` | hp values: canonical host, `RECLAIM_SYSTEM_HOSTNAME=hp-xubuntu`, user/group `cwoolley`, `RECLAIM_HOME=/home/cwoolley`, `RECLAIM_WORKTREE_ROOT=/home/cwoolley/.worktrees` (does not exist on hp; treated as empty inventory), `RECLAIM_CHECKOUT_ROOTS=/home/cwoolley/repos`, 14d/30d, `daily` | hp-xubuntu | copied to `/usr/local/libexec/storage-reclaim.env` (0644 root) | n/a | a | `host_vars`; shipped-env caveat |
| `storage-reclaim/hosts/vps.env` | vps values: `RECLAIM_SYSTEM_HOSTNAME=vmi3006760`, user/group `ubuntu`, home `/home/ubuntu`, worktree root `/home/ubuntu/.worktrees`, checkout roots `/data/projects`, 14d/30d, `daily` | vps | `/usr/local/libexec/storage-reclaim.env` | n/a | a | `host_vars`; shipped-env caveat |
| `storage-reclaim/install.sh` | installer: root + hostname guard; requires script, service account exists, `RECLAIM_HOME` dir; notes (does not fail) if worktree root absent; installs script + env + two rendered units; `daemon-reload`; dry-runs the installed script **as the service user** (`sudo -u … env HOME=…`); `enable` + `start` timer; exit 7 if not active | both | `/usr/local/libexec/storage-reclaim.sh` (0755 root), `/usr/local/libexec/storage-reclaim.env`, `/etc/systemd/system/storage-reclaim.{service,timer}`; timer enabled+started | root (sudo); dry-run as service user | a | `copy`/`template`/`systemd` + `become_user` dry-run verify |
| `storage-reclaim/install.test.sh` | 14 cases: render both hosts, each host's own `User=`, host guard both directions | n/a | nothing | developer | d | test suite |
| `storage-reclaim/render-unit.sh` | renders `storage-reclaim.{service,timer}.in`; hardcodes `RECLAIM_HOST_ENV_DEST=/usr/local/libexec/storage-reclaim.env`; REQUIRED service: `RECLAIM_SERVICE_USER`, `RECLAIM_SERVICE_GROUP`, `RECLAIM_HOME`, `RECLAIM_HOST_ENV_DEST`; timer: `RECLAIM_ON_CALENDAR` | both | nothing directly | root at install | a | replaced by `template:` |
| `storage-reclaim/storage-reclaim.service.in` | oneshot unit: `User=@RECLAIM_SERVICE_USER@`, `Group=@RECLAIM_SERVICE_GROUP@`, `Environment=HOME=@RECLAIM_HOME@`, `ExecStart=/usr/local/libexec/storage-reclaim.sh @RECLAIM_HOST_ENV_DEST@ --apply`, `Nice=10`, idle IO, 1h timeout; deliberately NOT ordered after fabro-server. Placeholders from both env files (`ubuntu`/`cwoolley`); `RECLAIM_HOST_ENV_DEST` is renderer-derived | both | `/etc/systemd/system/storage-reclaim.service` | unit runs as the owning user (`ubuntu` on vps, `cwoolley` on hp), never root | a | `template:` + host_vars |
| `storage-reclaim/storage-reclaim.timer.in` | timer: `OnCalendar=@RECLAIM_ON_CALENDAR@` (both: `daily`), `RandomizedDelaySec=30m`, `Persistent=true` | both | `/etc/systemd/system/storage-reclaim.timer` | systemd | a | `template:` + `systemd:` |
| `storage-reclaim/storage-reclaim.sh` | the reclaimer: leg B reports orphaned worktrees (on-disk `.git` dirs minus every clone's `git worktree list` under `RECLAIM_CHECKOUT_ROOTS`), leg A `rm -rf`s git-ignored artifact dirs (`target`, `node_modules`, `.venv`, …) in worktrees idle ≥ `RECLAIM_ARTIFACT_IDLE_DAYS` with no live process cwd inside; deny-list, realpath re-check, fail-closed `/proc` snapshot; dry-run by default. Runtime env keys: `RECLAIM_CANONICAL_HOST`, `RECLAIM_SYSTEM_HOSTNAME`, `RECLAIM_WORKTREE_ROOT`, `RECLAIM_CHECKOUT_ROOTS`, `RECLAIM_ARTIFACT_IDLE_DAYS`, `RECLAIM_ORPHAN_IDLE_DAYS` | both | `/usr/local/libexec/storage-reclaim.sh` (0755 root) | the owning user (via unit) | a | `copy:`; script body unchanged |
| `storage-reclaim/storage-reclaim.test.sh` | 41-case safety-model suite with real on-disk git fixtures; mutation-checked | n/a | nothing | developer | d | test suite |

Row totals: (a) 40, (b) 0, (c) 0, (d) 25, (e) flagged on 7 rows (all also counted in a or d). 65 rows = 65 files.

No class (b): the repo contains no Kubernetes manifests; `sccache-redis` is a
`docker run` under systemd, not a pod.

No class (c): every artifact is either installed by an `install.sh`, consumed
by one, or is a test/doc. Three stale-but-not-dead notes worth carrying into
the migration: (1) `storage-reclaim/README.md` and both `container-reclaim`
and `storage-reclaim` `hosts/vps.env` still say `fabro-server/install.sh`
cannot run on vps because it derives the label; `fabro-server/install.sh` now
also accepts the tailnet DNS label (its own comment dates the fix 2026-08-23),
so that claim has rotted. (2) `fabro-server/install.sh` deletes a legacy
hand-made drop-in `verify-timeout-override.conf` and stops a legacy
non-systemd daemon; both are migration-era cleanup that an Ansible play should
carry as `state=absent` / one-time tasks rather than drop. (3)
`disk-guard/docker-prune.service.in`'s `Documentation=` URL points at
`livespec-orchestrator-beads-fabro`, preserved for byte-fidelity to the live
unit; changing it changes the recorded digest.

## 1. SECRETS (never printed; presence probed only)

| reader | secret | where it lives | how it is read |
|---|---|---|---|
| `fabro-server/install.sh` (`require_inputs`) | `SESSION_SECRET`, `FABRO_DEV_TOKEN` | `<FABRO_HOME_DIR>/storage/server.env` (mode 0600, generated by Fabro, per instance: `~/.fabro/storage/server.env` and `~/.fabro-mi-homelab/storage/server.env`) | `grep -qE '^NAME=.+'` presence check only; installer REFUSES to create the file |
| installed `fabro-server*.service` (runtime) | same two | same file | `EnvironmentFile=` loads them into the server process |
| installed `fabro-server*.service` (runtime) | `GITHUB_APP_PRIVATE_KEY` | Fabro's own vault (set via `FABRO_SERVER=http://127.0.0.1:<port> fabro secret set GITHUB_APP_PRIVATE_KEY --value-stdin`, per README) | read by the server; not touched by any file in this repo |
| Fabro CLI on the host (runtime, out of repo) | CLI dev token | `~/.fabro/auth.json` (keyed by `cli.target.url`) | README states it; nothing in the repo reads it |
| `fabro-server/check-settings.sh` | `FABRO_DEV_TOKEN` | `<FABRO_HOME_DIR>/storage/server.env` | `grep … \| cut -d= -f2-` into a shell var, sent as `Authorization: Bearer` to loopback only; must run as the service account |
| installed `fabro-server*.service` (negative) | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | none expected | `UnsetEnvironment=` strips them deliberately (OAuth-only posture); `CLAUDE_CODE_OAUTH_TOKEN` is injected into the sandbox per dispatch by the orchestrator, not by this repo |
| `sccache-redis` (runtime) | none | n/a | redis runs with `--protected-mode no` and no AUTH by documented design; reachable only on the docker bridge gateway |
| `container-reclaim`, `disk-guard`, `storage-reclaim`, `host-tools` | none | n/a | no secret read at install or runtime |

## 2. DOWNLOADS / PACKAGES

| installer / unit | what | pin |
|---|---|---|
| `sccache-redis.service` (`ExecStart=docker run … @SCCACHE_REDIS_IMAGE@`) | pulls `docker.io/library/redis:8.8.2-alpine` at first unit start (not during `install.sh`) | **digest-pinned**: `@sha256:96cb544fa0af5aa898d160cffb7dae70c3df117190fc123831c64712cda425ff`, copied from `livespec-dev-tooling` `ci-runner/k3s/phase2/sccache/sccache-redis.yaml` (read 2026-09-06); README says "bump both places together" |
| `fabro-server/install.sh` | does NOT download or build the Fabro binary; requires `<HOME>/.fabro/bin/fabro` to already exist and be executable | pin owned elsewhere: `livespec-orchestrator-beads-fabro` `orchestrator-image/README.md` (normative in that repo's `SPECIFICATION/constraints.md`); AGENTS.md: "any build ≥ 0.256 breaks `workflow.fabro`"; `hosts/hp-xubuntu.settings.expected` cites "pinned build 8de6611". Build recipe in README: `cargo clean --release -p fabro-spa && cargo dev build --release -p fabro-cli` in the pinned `factory-integration` worktree, then atomic replace |
| `host-tools/install.sh` | installs no package; REFUSES unless `btop` is already on PATH, printing `sudo apt-get install -y btop` as the fix | unpinned (distro apt) |
| `disk-guard/install.sh` | installs no package; requires `docker`, `journalctl`, `apt-get`, `logger`, `df` present and the docker daemon answering | n/a |
| `container-reclaim/install.sh` | installs no package; requires `docker` CLI + daemon (+ `containerd` CLI optional at runtime) | n/a |
| `storage-reclaim/install.sh` | installs no package; script needs `git`, GNU `find -printf`, `realpath`, `comm` | n/a |
| `fabro-server/install.sh` | installs no package; requires `curl`, `jq`; `tailscale` optional (host guard fallback); unit orders after `docker.service` and `tailscaled.service` | n/a |

Ansible consequence: the only download the estate performs is the redis image
pull, and it is already digest-pinned. Package presence (`docker`, `jq`,
`curl`, `btop`, `tailscale`) is asserted, never installed, everywhere.

## 3. CONVENTION (how an operator applies a service, from where, as whom)

**README.md "Quickstart"** (verbatim core):

> Run **on the host being provisioned**, from a clone of this repo:
> `cd services/fabro-server` / `./install.test.sh` / `sudo ./install.sh hosts/<host>.env` / `/usr/local/libexec/fabro-server-verify-web`
> Every script here takes its host values file as a path **relative to the current directory**, and `hosts/` lives beside the scripts under `services/fabro-server/`. So `cd` there first; invoking from the repo root … exits 2 … `install.sh` refuses to apply one host's values on a different host.

So: **where** = a git clone on the target host itself (no push/ssh
mechanism in the repo; the operator reaches `hp-xubuntu` via
`tailscale ssh cwoolley@hp-xubuntu` per AGENTS.md "Operating the hosts", and
`vps` is the local dev host); **as whom** = `sudo` (root) for every
`install.sh`, with dry-run verification dropped to the service account where
the unit runs unprivileged; **what** = one `install.sh` per service per host,
run once per `hosts/<host>.env` (four times per host for `fabro-server`'s two
instances). There is no fleet-wide "apply everything" entry point.

**AGENTS.md "The one rule this repo exists to enforce"** (verbatim):

> **A change that applies to the fleet goes in the template; a change that applies to one host goes in that host's values file. Never fork the template.**
> This repo exists because forking was the old arrangement and it failed silently: `hp-xubuntu` was a hand-edited copy of `vps`'s files, so fixes landed on `vps` and never reached `hp`. Two divergences were found that way (`bd-ib-l3nptz.15`, `bd-ib-wdns6b`), and both were invisible until someone diffed the live hosts.

**README.md "Why a fleet repo rather than a per-host one"** records the same
history in more detail: `hp-xubuntu` was stood up by cloning
`vps-info/services/fabro-server/`, hand-editing the host literals, running the
installer, and discarding the edits, so hp's provisioning existed only as live
host state; `bd-ib-l3nptz.15` (hp lacked the `FABRO_WEB_VERIFY_ATTEMPTS`
crash-loop mitigation) and `bd-ib-wdns6b` (hp silently resolved
`max_concurrent_runs=5` against vps's 10 because its `settings.toml` had no
`[server.scheduler]` table) were the two divergences. This is the template +
host_vars split Ansible provides natively.

**AGENTS.md "After you merge — merging is NOT deploying"** (verbatim core):

> **Every unit here executes an INSTALLED COPY, never the checkout.** A merged fix changes nothing on any host until `install.sh` is re-run there. Re-run it on **every host running that service**, then diff the installed file against the merged one to prove it landed: `sudo ./services/<service>/install.sh hosts/<host>.env` / `sudo diff /usr/local/libexec/<service>.sh services/<service>/<service>.sh   # must be empty`

with the measured 2026-08-22 case of `vps` running a pre-fix
`container-reclaim.sh` under an active, "successful" timer. This is the
drift-detection gap Ansible's idempotent `copy:`/`template:` with `--check
--diff` closes.

**AGENTS.md "Before you change anything"** requires, per change: measure live
hosts with `check-settings.sh` rather than reasoning from files; render for
**every** host and diff against each host's live unit; run both test suites;
`shellcheck` everything. **"Adding a host"** lists the six-value env file, an
observed `.settings.expected`, README table rows, the `tailscale serve` mapping
in `tailscale-admin` (not here), and extending `install.test.sh` both
directions.

## 4. (e) INTERACTIVE / OUT-OF-BAND STEPS an installer expects a human to perform

1. **`fabro-server`: build and place the Fabro binary.** `install.sh` requires
   `<HOME>/.fabro/bin/fabro` and refuses if absent. README: `cargo clean
   --release -p fabro-spa` then `cargo dev build --release -p fabro-cli` in the
   pinned `factory-integration` worktree, then atomic replace per the
   orchestrator repo's runbook. Shared across both instances on a host.
2. **`fabro-server`: create `<FABRO_HOME_DIR>/storage/server.env`** (generated
   `FABRO_DEV_TOKEN` + `SESSION_SECRET`, mode 0600), once per instance. The
   installer header says it "REQUIRES that file and never creates it".
3. **`fabro-server`: apply `settings.toml` by hand.** `render-settings.sh
   hosts/<host>.env | diff - ~/.fabro/settings.toml`, then copy; `install.sh`
   deliberately does not (vps's live file is hand-maintained and holds its
   explicit `max_concurrent_runs = 10`).
4. **`fabro-server`: load the GitHub App private key** into the instance's
   vault: `FABRO_SERVER=http://127.0.0.1:<port> fabro secret set
   GITHUB_APP_PRIVATE_KEY --value-stdin`.
5. **`fabro-server`: add the `tailscale serve` mapping** for each port
   (32276/32277) in the `tailscale-admin` repo; `install.sh` "neither creates
   nor verifies it".
6. **`fabro-server`: decide whether vps gets `otel.conf`.** README "Known
   gaps": installing the set on vps newly adds OTLP export, "make that call
   deliberately, or install `vps` without the drop-in" (the installer has no
   switch for this).
7. **`fabro-server`: wait for a quiet server.** `require_quiet_server` exits 3
   while `fabro ps` lists active runs; the operator must retry later.
8. **`host-tools`: pre-install `btop`** (`sudo apt-get install -y btop`); the
   installer refuses without it.
9. **`disk-guard`: compare printed digests.** `note_replacement` prints the
   sha256 of the files it is about to overwrite so the operator can confirm
   they match README's relocation table; nothing enforces the comparison.
10. **`sccache-redis`: the sandbox half is elsewhere.** The redis endpoint is
    baked into the sandbox image (`livespec-dev-tooling`
    `docker/fabro-sandbox/agent/Dockerfile`); this repo installs only the
    host side, and the "after" measurement is read from Honeycomb.
11. **`container-reclaim`: an open measurement, not an install step.**
    `hosts/hp-xubuntu.env` asks a human with host access to run `docker ps
    -as` on hp and re-derive the 48h horizon if hp's distribution is not
    bimodal.

Secrets an installed service reads at runtime are listed in section 1.
