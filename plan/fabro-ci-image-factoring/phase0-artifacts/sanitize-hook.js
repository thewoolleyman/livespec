#!/usr/bin/env node
// sanitize-hook.js — Phase 0 containment shim for ACTIONS_RUNNER_CONTAINER_HOOKS.
//
// The stock GitHub Actions runner unconditionally mounts the host docker socket
// (-v /var/run/docker.sock:/var/run/docker.sock) into `container:` jobs and can
// pass through create-options a workflow requests. This wrapper enforces the
// Phase 0 runner-containment invariants (plan/fabro-ci-image-factoring/
// phase0-runner-containment-design.md) at the hook boundary — independent of what
// the runner emits — before delegating to the real container hook:
//
//   * strip any host-socket bind (/var/run/docker.sock, /run/docker.sock, and the
//     rootless podman socket) from system/user mount volumes (test 4);
//   * strip host-namespace / privilege escalations from createOptions
//     (--privileged, --pid=host, --network=host, --ipc=host, --userns=host, …);
//   * pass everything else through untouched (run_script_step / cleanup_job etc.).
//
// The real hook (hooklib getInputFromStdin) reads only the LAST line of stdin, so
// the payload is single-line JSON; we parse it, sanitize, and re-emit one line.
'use strict';
const fs = require('fs');
const { spawnSync } = require('child_process');

const REAL_HOOK = '/home/ci-runner/actions-runner/container-hooks/index.js';
const BAD_SOURCES = new Set([
  '/var/run/docker.sock',
  '/run/docker.sock',
  '/run/user/1001/podman/podman.sock',
]);
const BAD_OPTS = [
  '--privileged',
  '--pid=host', '--pid host',
  '--network=host', '--net=host',
  '--ipc=host',
  '--userns=host',
  '--security-opt=label=disable', '--security-opt label=disable',
  '--cap-add=all', '--cap-add=ALL',
];

function sanitizeContainer(c) {
  if (!c || typeof c !== 'object') return;
  for (const key of ['systemMountVolumes', 'userMountVolumes']) {
    if (Array.isArray(c[key])) {
      c[key] = c[key].filter((v) => !(v && BAD_SOURCES.has(v.sourceVolumePath)));
    }
  }
  if (typeof c.createOptions === 'string') {
    let opts = c.createOptions;
    for (const bad of BAD_OPTS) opts = opts.split(bad).join('');
    c.createOptions = opts.replace(/\s+/g, ' ').trim();
  }
}

function delegate(inputText) {
  const r = spawnSync(process.execPath, [REAL_HOOK], {
    input: inputText,
    stdio: ['pipe', 'inherit', 'inherit'],
  });
  process.exit(r.status == null ? 1 : r.status);
}

const raw = fs.readFileSync(0, 'utf8');
const line = raw.split('\n').filter((s) => s.trim().length).pop() || '';
let data;
try {
  data = JSON.parse(line);
} catch (e) {
  // Not parseable here — let the real hook produce the canonical error.
  delegate(raw);
}
const args = (data && data.args) || {};
if (args.container && typeof args.container === 'object') sanitizeContainer(args.container);
if (Array.isArray(args.services)) args.services.forEach(sanitizeContainer);
delegate(JSON.stringify(data) + '\n');
