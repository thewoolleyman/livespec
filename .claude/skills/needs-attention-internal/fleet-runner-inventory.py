#!/usr/bin/env python3
"""fleet-runner-inventory.py -- the ONE authoritative fleet CI capacity inventory.

`livespec-s43svm.42`. Answers "how many runners does the fleet have, of what,
where, and out of what cap" in a single shot, in a shape that CANNOT be read at
the wrong scope, because every count carries its own scope label.

WHY THIS EXISTS. On 2026-08-21 a maintainer was shown 75 and 482 for the same
runners and asked which was true. Neither was wrong: 75 was one repository's
row, 482 was the eight-repository fleet total, and the eight rows summed to
exactly 482. A per-repo count had been compared against a fleet aggregate. The
error was compounded by checking a service on the WRONG HOST and reading its
absence as evidence. If the only sanctioned way to answer the question prints
scope, population, host, cap and total together, that comparison becomes
structurally unavailable rather than merely discouraged.

FIVE PROPERTIES, each forced by a measured failure rather than by taste:

1. NEVER EMIT A BARE TOTAL. `total_count` from the runners endpoint MIXES
   POPULATIONS. While the podman pool was being decommissioned `livespec` read
   75, then 82, then 80 within seconds -- 75 durable stranded registrations plus
   a churning count of autoscaling ARC runners. Every count here is emitted
   under a named population, and the fleet aggregate is an EXPLICITLY LABELLED
   row rather than something a reader constructs by hand.

2. NEVER CACHE. `gh api --cache 60s` returned byte-identical STALE output on
   this endpoint: `livespec-overseer` read 18 while live was 30, then 36, then
   46. For a churning population a cached read does not answer a cheaper
   version of the question, it answers a question about the PAST -- and its
   determinism makes the wrong answer look corroborated on re-run. Freshness is
   a CORRECTNESS property of this inventory, not an optimisation knob. (The
   shipped `github_rate_limit_guard` prescribes exactly the caching that would
   break this; see `livespec-driver-claude-mu5`.)

3. DERIVE THE MEMBER LIST FROM THE MANIFEST, never from a tool's argument list.
   The decommission sweep that prompted this item covered EIGHT repositories
   because it took its list from the pool's configured scope; the fleet has TEN.

4. DERIVE THE SCALE SETS FROM THEIR VALUES FILES, never from repository names.
   The mapping is not guessable: repository `livespec` runs scale set
   `livespec-local-ci-k3s`, `livespec-console-beads-fabro` runs
   `livespec-console-beads-k3s`, and `livespec-orchestrator-git-jsonl` runs
   `livespec-orchestrator-git-k3s`.

5. SPLIT ON THE LABEL SET, not on the count. An EMPTY label array means an ARC
   scale-set member; a NON-EMPTY one means an individually-registered runner.
   That single field separates the two populations cleanly and is present in
   every row. A filter requiring BOTH a shared and a host-unique label misses a
   shared-label-only row -- which is exactly how a sweep verified clean while a
   candidate residue sat outside its predicate.

WHY THIS IS A PROGRAM AND NOT A SHELL LOOP. GitHub's GraphQL schema exposes NO
runner type or field at all (verified by schema introspection: zero matches for
"runner" across every type name), so the per-repository REST endpoint is the
only source and a fan-out is unavoidable. `github_rate_limit_guard` denies a
shell loop containing `gh api`, and this is NOT a restructuring to slip past
that matcher: the inventory must parse JSON, join it against configured caps,
group by population, and emit a labelled aggregate, so it would be a program
even if no guard existed. The read is bounded and one-shot -- two calls per
member against a 5000/hour primary limit -- which is not the polling burst the
guard exists to prevent.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OWNER = "thewoolleyman"
MANIFEST = Path("/data/projects/livespec/.livespec-fleet-manifest.jsonc")
ARC_VALUES_DIR = Path("/data/projects/livespec-dev-tooling/ci-runner/k3s/phase2/arc")

# Every configured ARC scale set runs on the single-node k3s cluster on this
# host. Stated once, here, so a reader never has to guess which machine to check
# -- the wrong-host read is half of the confusion this inventory exists to end.
ARC_HOST = "poweredge-xubuntu (k3s cluster)"

# An ARC runner registers as "<scale-set-name>-<hash>-runner-<hash>", e.g.
# "livespec-overseer-k3s-rwtdp-runner-26pcz". Anchoring on the literal
# "-runner-" infix and stripping the one hash segment before it recovers the
# scale-set name without assuming any hash LENGTH.
ARC_NAME = re.compile(r"^(?P<scale_set>.+)-[^-]+-runner-[^-]+$")


def _read_jsonc(*, path: Path) -> dict:
    """Parse a .jsonc file: strip whole-line // comments and trailing commas."""
    raw = path.read_text()
    txt = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("//"))
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", txt))


def _gh_json(*, endpoint: str) -> tuple[dict | None, str | None]:
    """One uncached GitHub REST read.

    Returns (payload, None) on success and (None, reason) on failure. The caller
    BRANCHES ON THIS TUPLE, never on whether the output was empty: `gh api -q`
    on a 404 prints the literal string "null", which is non-empty and passes an
    emptiness test, so an empty-output test misclassifies every missing
    resource as a present one.
    """
    gh = shutil.which("gh")
    if gh is None:
        return None, "the `gh` CLI is not on PATH"
    completed = subprocess.run(
        [gh, "api", endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        first = completed.stderr.strip().splitlines()
        return None, (first[-1] if first else f"exit {completed.returncode}")
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"unparseable response: {exc}"


def load_scale_sets() -> dict[str, dict]:
    """Map scale-set name -> {cap, repo}, derived from the ARC values files.

    The values file is the CONFIGURED source of truth for the cap; the runner
    listing is the OBSERVED count. Reporting them side by side is the point.
    """
    scale_sets: dict[str, dict] = {}
    if not ARC_VALUES_DIR.is_dir():
        return scale_sets
    for path in sorted(ARC_VALUES_DIR.glob("values-*.yaml")):
        text = path.read_text()
        name = re.search(r'^runnerScaleSetName:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        cap = re.search(r"^maxRunners:\s*(\d+)", text, re.MULTILINE)
        url = re.search(r'^githubConfigUrl:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        if name is None or "<" in name.group(1):
            continue  # the EXAMPLE template, which carries placeholders
        scale_sets[name.group(1).strip()] = {
            "cap": int(cap.group(1)) if cap else None,
            "repo": url.group(1).rstrip("/").split("/")[-1] if url else None,
            "values_file": str(path),
        }
    return scale_sets


def routing_request(*, repo: str) -> tuple[list[str] | None, str | None]:
    """What this repository's gating CI asks for, from CI_RUNNER_LABELS.

    A 404 is NOT an error: it means the repository declares no variable and so
    routes to GitHub-hosted capacity. It is reported as an empty request, and
    the caller must not confuse that with a failed read.
    """
    payload, reason = _gh_json(endpoint=f"repos/{OWNER}/{repo}/actions/variables/CI_RUNNER_LABELS")
    if payload is None:
        if reason and "not found" in reason.lower():
            return [], None
        return None, reason
    try:
        value = json.loads(str(payload.get("value", "[]")))
    except json.JSONDecodeError:
        return None, f"CI_RUNNER_LABELS is not JSON: {payload.get('value')!r}"
    return [str(entry) for entry in value], None


def classify(*, runners: list[dict], scale_sets: dict[str, dict]) -> dict:
    """Group one repository's registrations into named populations.

    Populations are keyed by what a reader can ACT on: a configured scale set,
    an unrecognised ARC-shaped group, or an individually-registered label set.
    """
    populations: dict[str, dict] = {}
    for runner in runners:
        labels = [entry["name"] for entry in runner.get("labels", [])]
        if labels:
            # Individually-registered: the shape the deleted podman lane used.
            key = "labelled:" + ",".join(sorted(labels))
            kind = "individually-registered"
            configured = None
        else:
            match = ARC_NAME.match(str(runner.get("name", "")))
            scale_set = match.group("scale_set") if match else None
            if scale_set and scale_set in scale_sets:
                key, kind = f"arc:{scale_set}", "arc-scale-set"
                configured = scale_sets[scale_set]["cap"]
            else:
                key = f"arc-unrecognised:{scale_set or runner.get('name')}"
                kind, configured = "arc-shaped-unrecognised", None
        entry = populations.setdefault(
            key,
            {
                "population": key,
                "kind": kind,
                "labels": labels,
                "configured_cap": configured,
                "host": ARC_HOST if kind != "individually-registered" else "unknown host",
                "observed": 0,
                "online": 0,
                "offline": 0,
                "busy": 0,
            },
        )
        entry["observed"] += 1
        entry["busy"] += 1 if runner.get("busy") else 0
        if runner.get("status") == "online":
            entry["online"] += 1
        else:
            entry["offline"] += 1
    return populations


def unroutable_reason(*, population: dict, requested_fleetwide: set[str]) -> str | None:
    """Is this population one that no fleet workflow can route a job to?

    THE DETECTOR THIS ITEM EXISTS FOR. 482 stranded registrations sat online for
    nine days after the cutover, served zero jobs, and were seen by no check.
    They advertised `local-ci` + `poweredge` while every repository had already
    been repointed at a scale-set name, so nothing could ever claim them.

    Routability is decided against the UNION of every fleet member's request,
    not against the owning repository's alone: a runner registered on one
    repository is claimable only by that repository's workflows, but a label set
    that no member anywhere requests is unroutable by construction.
    """
    if population["kind"] == "individually-registered":
        if not set(population["labels"]) & requested_fleetwide:
            return (
                "carries labels no fleet repository requests "
                f"({', '.join(population['labels'])})"
            )
        return None
    scale_set = population["population"].split(":", 1)[1]
    if population["kind"] == "arc-shaped-unrecognised":
        return f"ARC-shaped registration for no configured scale set ({scale_set})"
    if scale_set not in requested_fleetwide:
        return f"configured scale set {scale_set} that no repository requests"
    return None


def gather() -> dict:
    manifest = _read_jsonc(path=MANIFEST)
    members = [entry["repo"] if isinstance(entry, dict) else entry for entry in manifest["fleet"]]
    scale_sets = load_scale_sets()

    repos: list[dict] = []
    skipped: list[str] = []
    requested_fleetwide: set[str] = set()

    for repo in members:
        requested, reason = routing_request(repo=repo)
        if requested is None:
            skipped.append(f"{repo} (CI_RUNNER_LABELS read failed: {reason})")
            requested = []
        requested_fleetwide.update(requested)
        payload, reason = _gh_json(endpoint=f"repos/{OWNER}/{repo}/actions/runners")
        if payload is None:
            skipped.append(f"{repo} (runner listing failed: {reason})")
            continue
        repos.append(
            {
                "repo": repo,
                "requests": requested,
                "populations": classify(runners=payload.get("runners", []), scale_sets=scale_sets),
            }
        )

    for record in repos:
        for population in record["populations"].values():
            population["unroutable"] = unroutable_reason(
                population=population, requested_fleetwide=requested_fleetwide
            )

    configured_total = sum(
        entry["cap"] or 0 for name, entry in scale_sets.items() if name in requested_fleetwide
    )
    observed_total = sum(
        population["observed"] for record in repos for population in record["populations"].values()
    )
    return {
        "scope": "livespec fleet members declared in .livespec-fleet-manifest.jsonc",
        "member_count": len(members),
        "members_read": len(repos),
        "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "caveat": (
            "ARC scale-set counts MOVE under autoscaling: registrations are "
            "ephemeral and minRunners is 0, so two readings minutes apart "
            "legitimately differ. An OBSERVED count is a measurement of "
            "something moving; a CONFIGURED cap is a durable fact. Never "
            "compare an observed count taken now against one taken earlier and "
            "call the difference a discrepancy."
        ),
        "repos": repos,
        "fleet_total": {
            "label": "FLEET TOTAL (all members, all populations)",
            "observed_registrations": observed_total,
            "configured_cap_of_requested_scale_sets": configured_total,
        },
        "skipped": skipped,
    }


def render(*, inventory: dict) -> str:
    lines: list[str] = []
    lines.append("# Fleet CI capacity inventory")
    lines.append("")
    lines.append(f"SCOPE: {inventory['scope']}")
    lines.append(
        f"MEMBERS: {inventory['members_read']} read " f"of {inventory['member_count']} declared"
    )
    lines.append(f"READ AT: {inventory['read_at']} (uncached)")
    lines.append("")
    lines.append(f"CAVEAT: {inventory['caveat']}")
    lines.append("")
    for record in inventory["repos"]:
        requests = ", ".join(record["requests"]) or "(none -- GitHub-hosted)"
        lines.append(f"## {record['repo']}  [requests: {requests}]")
        if not record["populations"]:
            lines.append("  no registrations")
            lines.append("")
            continue
        for population in sorted(record["populations"].values(), key=lambda p: p["population"]):
            cap = population["configured_cap"]
            cap_text = f"cap {cap}" if cap is not None else "cap UNCONFIGURED"
            lines.append(
                f"  {population['population']}: "
                f"observed {population['observed']} / {cap_text} "
                f"(online {population['online']}, offline {population['offline']}, "
                f"busy {population['busy']}) on {population['host']}"
            )
            if population["unroutable"]:
                lines.append(f"    UNROUTABLE: {population['unroutable']}")
        lines.append("")
    total = inventory["fleet_total"]
    lines.append(f"## {total['label']}")
    lines.append(f"  observed registrations: {total['observed_registrations']}")
    lines.append(
        "  configured cap of every requested scale set: "
        f"{total['configured_cap_of_requested_scale_sets']}"
    )
    lines.append("")
    if inventory["skipped"]:
        lines.append("## Skipped")
        for note in inventory["skipped"]:
            lines.append(f"  skipped: {note}")
    return "\n".join(lines)


def main() -> int:
    inventory = gather()
    if "--json" in sys.argv[1:]:
        print(json.dumps(inventory, indent=2))
    else:
        print(render(inventory=inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
