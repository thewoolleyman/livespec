"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "A fleet CI host is rebuilt from bare metal by
the committed procedure" — the property
`SPECIFICATION/non-functional-requirements.md` ratifies as "A host
carrying fleet CI MUST be rebuildable from bare metal by a committed
procedure". That clause places the recipe, its profiles and its
rehearsal obligation in the repository that provisions the host's job
runtime, never in this specification, so this module rehearses THAT
repository's committed procedure as a consumer reads a producer.

HOW THE PRODUCER IS REACHED, AND WHY NOTHING HERE KNOWS ITS LAYOUT.
The provisioning repository is resolved through this project's own
committed seam — the `.livespec.jsonc` `cross_repo_targets` entry plus
`resolve_effective_local_clone`, which honors the
`LIVESPEC_SIBLING_CLONES_ROOT` override — so the clone path is never
spelled here. The procedure's location inside that clone is then
DERIVED from the producer's own ratified obligation section: the one
`## ` section of its `non-functional-requirements.md` that quotes this
repository's clause title, read out of its git database at `HEAD`. The
bare-metal stage directory is the backticked path that section names;
the profiles are the one directory of `.env` data beside it; the stages
are the scripts in it whose own `--help` advertises `--dry-run` and a
PROFILE argument. A rename inside that tree that the producer's clause
does not announce therefore surfaces as a failure here rather than
passing silently, and this repository reads no path the producer has
not published. Reading the producer is cycle-free: this repository
already consumes it (`pyproject.toml` pins it), so the dependency
points consumer → producer, per `.ai/no-circular-dependency.md`.

WHAT A REHEARSAL IS, OFF THE HOST. The scenario's subject is a host
powered on with empty storage. Nothing here powers on a host. But
every stage of the committed procedure is an executable artifact
carrying a `--dry-run` mode in which each mutating command is PRINTED
and none is run, and every state it reads comes from read-only probes.
So this module materializes the procedure from the producer's git
database — committed state, never a working tree that may lag or carry
edits — and RUNS the real stages, unmodified, against the real
committed per-host profiles, on a scratch `PATH` whose probes answer
nothing. "Probes answer nothing" IS the scenario's empty storage, and
it is what makes the plan independent of the block devices of whatever
machine runs the suite. Every destructive command the stages can reach
is a tripwire on that same `PATH` that records being called, so "the
rehearsal executed nothing" is measured rather than taken from the
stage's own closing line, which is asserted beside it.

WHAT IS LEFT TO THE PRODUCER. The populated-storage halves of the
re-run clause — a plan against a host already in its declared state,
and the refusal naming a volume whose filesystem has drifted — need
probes that answer a FINISHED host, which means standing inside the
producer's probe argv and its parsing: its internals. Those are
rehearsed by the producer's own consumer-tier scenario test, and
asserting them here would couple this repository to a layout its
clause does not publish. What this module asserts of that clause is
the half that needs no such knowledge: the plan is stable across
repeated rehearsals, and no planned step ever names a volume the
profile preserves.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    resolve_effective_local_clone,
)
from livespec.parse import jsonc
from returns.result import Success

__all__: list[str] = []

pytestmark = pytest.mark.integration


_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROVISIONING_SLUG = "livespec-dev-tooling"
_PRODUCER_SPEC = "SPECIFICATION/non-functional-requirements.md"
_CLAUSE_TITLE = (
    "A host carrying fleet CI MUST be rebuildable from bare metal by a committed procedure"
)
_STAGE_DIR_MARK = "phase0-bare-metal/"
_BACKTICKED = re.compile(r"`([^`\s]+)`")
_DATA_LINE = re.compile(r"^[A-Z][A-Z0-9_]*=")
_TIMEOUT_S = 300.0

# The read-only probes a plan is derived from. A stub that answers nothing is
# read as "absent", which is the scenario's empty storage, deterministically —
# no block device, no volume, no filesystem, no firmware boot entry, nothing
# mounted. A probe LEFT OFF this list answers about the machine running the
# suite instead, which would show up as a plan that differs between hosts.
_PROBES = (
    "blkid",
    "efibootmgr",
    "findmnt",
    "lsblk",
    "lvs",
    "pvs",
    "vgs",
)
# Every command the stages can reach that would CHANGE a host. Each is a
# tripwire, so "the dry run executed nothing" is measured, not assumed.
_MUTATORS = (
    "apt-get",
    "debootstrap",
    "lvcreate",
    "mdadm",
    "mkfs",
    "mkfs.ext2",
    "mkfs.ext3",
    "mkfs.ext4",
    "mkfs.vfat",
    "mkfs.xfs",
    "mkswap",
    "parted",
    "partprobe",
    "perccli64",
    "pvcreate",
    "sfdisk",
    "sgdisk",
    "storcli64",
    "udevadm",
    "vgchange",
    "vgcreate",
    "wipefs",
)


@dataclass(frozen=True, kw_only=True)
class _Stage:
    """One stage of the procedure, with the usage line it published."""

    path: Path
    usage: str


@dataclass(frozen=True, kw_only=True)
class _Procedure:
    """The committed procedure, materialized out of the producer's git database."""

    stage_dir: Path
    stages: tuple[_Stage, ...]
    profiles: tuple[Path, ...]
    env: dict[str, str]
    tripwire: Path


@dataclass(frozen=True, kw_only=True)
class _Rehearsal:
    """One stage's dry run against one per-host profile."""

    returncode: int
    stdout: str
    stderr: str
    planned: tuple[str, ...]
    executed: str


def _run(
    *,
    args: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one child process, returning its outcome rather than raising on it."""
    return subprocess.run(
        args,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_S,
        env=env,
    )


def _provisioning_clone(*, config_text: str, slug: str) -> Path:
    """Resolve the provisioning repository through this project's own seam.

    Every outcome that is NOT a usable clone skips rather than fails,
    because a tree with no clone of the provisioning repository cannot
    rehearse its procedure and must not report that it did. Each skip
    names what was missing, so a skipped run is distinguishable from a
    run that had the procedure and exercised it.
    """
    parsed_result = jsonc.loads(text=config_text)
    if not isinstance(parsed_result, Success):
        pytest.skip("this project's .livespec.jsonc did not parse")
    parsed: Any = parsed_result.unwrap()
    targets: Any = parsed.get("cross_repo_targets") if isinstance(parsed, dict) else None
    target: Any = targets.get(slug) if isinstance(targets, dict) else None
    if not isinstance(target, dict):
        pytest.skip(f"{slug} is not a registered cross-repo target")
    resolved = resolve_effective_local_clone(sibling_slug=slug, target=target)
    if resolved is None or not (Path(resolved) / ".git").exists():
        pytest.skip(
            f"no clone of {slug} is resolvable "
            f"(resolved {resolved!r}); the committed procedure cannot be rehearsed"
        )
    return Path(resolved)


def _derive_stage_dir(*, clone: Path) -> str:
    """Read the bare-metal stage's path out of the producer's own clause."""
    shown = _run(args=["git", "show", f"HEAD:{_PRODUCER_SPEC}"], cwd=clone)
    assert (
        shown.returncode == 0
    ), f"{_PROVISIONING_SLUG} committed no {_PRODUCER_SPEC} at HEAD: {shown.stderr}"
    owning = [
        section
        for section in re.split(r"^## ", shown.stdout, flags=re.MULTILINE)
        if _CLAUSE_TITLE in section
    ]
    assert len(owning) == 1, (
        f"{_PROVISIONING_SLUG}'s {_PRODUCER_SPEC} must carry exactly one section "
        f"accepting the clause {_CLAUSE_TITLE!r}; found {len(owning)}"
    )
    named = {path for path in _BACKTICKED.findall(owning[0]) if path.endswith(_STAGE_DIR_MARK)}
    assert len(named) == 1, (
        "that section must name exactly one bare-metal stage directory ending in "
        f"{_STAGE_DIR_MARK!r}; found {sorted(named)}"
    )
    return named.pop()


def _materialize(*, clone: Path, dest: Path) -> Path:
    """Extract the producer's committed tree at `HEAD` into `dest`."""
    archive = dest / "tree.tar"
    written = _run(args=["git", "archive", "--format=tar", "-o", str(archive), "HEAD"], cwd=clone)
    assert written.returncode == 0, f"git archive failed: {written.stderr}"
    tree = dest / "tree"
    tree.mkdir()
    extracted = _run(args=["tar", "-xf", str(archive), "-C", str(tree)], cwd=dest)
    assert extracted.returncode == 0, f"tar failed: {extracted.stderr}"
    return tree


def _write_stub(*, path: Path, body: str) -> None:
    """Write one executable `/bin/sh` stub onto the scratch PATH."""
    _ = path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8")
    path.chmod(0o755)


def _scratch_bin(*, dest: Path, tripwire: Path) -> Path:
    """Build the scratch PATH: probes answer nothing, mutators record a call."""
    scratch = dest / "bin"
    scratch.mkdir()
    for probe in _PROBES:
        _write_stub(path=scratch / probe, body="exit 0\n")
    for mutator in _MUTATORS:
        _write_stub(
            path=scratch / mutator,
            body=f'printf "%s\\n" "$0 $*" >> {tripwire}\nexit 0\n',
        )
    return scratch


def _discover_stages(*, stage_dir: Path, env: dict[str, str]) -> tuple[_Stage, ...]:
    """Select the stages that publish a `--dry-run` rehearsal over a PROFILE."""
    stages: list[_Stage] = []
    for script in sorted(stage_dir.glob("*.sh")):
        helped = _run(args=["bash", script.name, "--help"], cwd=stage_dir, env=env)
        lines = helped.stdout.splitlines()
        usage = lines[0] if lines else ""
        if usage.startswith("Usage:") and "--dry-run" in usage and "PROFILE" in usage:
            stages.append(_Stage(path=script, usage=usage))
    return tuple(stages)


def _profiles_dir(*, stage_dir: Path) -> Path:
    """Locate the one directory of per-host profile data beside the procedure."""
    holders = {found.parent for found in stage_dir.rglob("*.env")}
    assert len(holders) == 1, (
        f"the bare-metal stage must hold its per-host profiles in one directory; "
        f"found {sorted(str(holder) for holder in holders)}"
    )
    return holders.pop()


def _profile_data(*, path: Path) -> dict[str, str]:
    """Read a per-host profile as the KEY=value data it is declared to be."""
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        data[key] = value
    return data


def _data_lines(*, path: Path) -> list[str]:
    """Every line of a profile that is neither blank nor a comment."""
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() != "" and not line.lstrip().startswith("#")
    ]


def _rehearse(
    *,
    procedure: _Procedure,
    stage: _Stage,
    profile: Path,
    work: Path,
) -> _Rehearsal:
    """Dry-run one stage against one profile in the empty-storage world."""
    _ = procedure.tripwire.write_text("", encoding="utf-8")
    args = ["bash", stage.path.name, "--dry-run"]
    if "--mount-root=" in stage.usage:
        args.append(f"--mount-root={work}")
    args.append(f"{profile.parent.name}/{profile.name}")
    done = _run(args=args, cwd=procedure.stage_dir, env=procedure.env)
    return _Rehearsal(
        returncode=done.returncode,
        stdout=done.stdout,
        stderr=done.stderr,
        planned=tuple(line[2:] for line in done.stdout.splitlines() if line.startswith("+ ")),
        executed=procedure.tripwire.read_text(encoding="utf-8"),
    )


@pytest.fixture(scope="module", name="procedure")
def procedure_fixture(*, tmp_path_factory: pytest.TempPathFactory) -> _Procedure:
    """Materialize the committed procedure and the world it is rehearsed in."""
    clone = _provisioning_clone(
        config_text=(_REPO_ROOT / ".livespec.jsonc").read_text(encoding="utf-8"),
        slug=_PROVISIONING_SLUG,
    )
    dest = tmp_path_factory.mktemp("provisioning")
    stage_relative = _derive_stage_dir(clone=clone)
    stage_dir = _materialize(clone=clone, dest=dest) / stage_relative
    assert stage_dir.is_dir(), (
        f"{_PROVISIONING_SLUG}'s clause names {stage_relative!r} as the bare-metal "
        "stage, but HEAD commits no such directory"
    )
    tripwire = dest / "executed.txt"
    _ = tripwire.write_text("", encoding="utf-8")
    scratch_bin = _scratch_bin(dest=dest, tripwire=tripwire)
    env = {
        "PATH": f"{scratch_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "HOME": str(dest),
        "LC_ALL": "C",
    }
    return _Procedure(
        stage_dir=stage_dir,
        stages=_discover_stages(stage_dir=stage_dir, env=env),
        profiles=tuple(sorted(_profiles_dir(stage_dir=stage_dir).glob("*.env"))),
        env=env,
        tripwire=tripwire,
    )


def test_a_second_host_is_a_second_profile_never_a_second_procedure(
    *,
    procedure: _Procedure,
    tmp_path: Path,
) -> None:
    """One procedure consumes one profile per host, and each profile is DATA.

    The scenario's first case is that a second pool member is a
    second PROFILE. Three things make that true rather than claimed:
    each profile names exactly the host its own filename names, every
    line of it is `KEY=value` data so a profile cannot smuggle in
    procedure, and no executable in the procedure carries a host's
    name. Then the same stage files, unmodified, are run against every
    committed profile — each either plans for that profile's own host
    or REFUSES naming that profile, which is what keeps a host a
    profile the procedure declines rather than a silent no-op.
    """
    assert len(procedure.profiles) >= 2, (
        "the rehearsal needs at least two committed per-host profiles to mean "
        f"anything; found {[path.name for path in procedure.profiles]}"
    )
    assert (
        len(procedure.stages) >= 1
    ), f"no stage under {procedure.stage_dir} published a --dry-run rehearsal"

    hosts = {profile.stem for profile in procedure.profiles}
    for profile in procedure.profiles:
        assert (
            _profile_data(path=profile).get("NODE_NAME") == profile.stem
        ), f"{profile.name} must declare NODE_NAME equal to its own stem"
        for line in _data_lines(path=profile):
            assert _DATA_LINE.match(
                line
            ), f"{profile.name} carries {line!r}, which is not KEY=value data"
    for script in sorted(procedure.stage_dir.rglob("*.sh")):
        assert not any(host in script.name for host in hosts), (
            f"{script.name} is named after a host: a second host must be a second "
            "profile, never a second procedure"
        )

    for stage in procedure.stages:
        for profile in procedure.profiles:
            rehearsal = _rehearse(
                procedure=procedure,
                stage=stage,
                profile=profile,
                work=tmp_path / "mnt",
            )
            if rehearsal.returncode == 0:
                assert f"node:     {profile.stem}" in rehearsal.stdout, (
                    f"{stage.path.name} planned against {profile.name} without naming "
                    f"that profile's host; got:\n{rehearsal.stdout}"
                )
            else:
                refused = "FATAL:" in rehearsal.stderr or "REFUSED:" in rehearsal.stderr
                assert refused and profile.name in rehearsal.stderr, (
                    f"{stage.path.name} declined {profile.name} without a refusal "
                    f"naming it; got:\n{rehearsal.stderr}"
                )


def test_the_rehearsal_reaches_each_profiles_declared_state_with_no_step_by_hand(
    *,
    procedure: _Procedure,
    tmp_path: Path,
) -> None:
    """Every role tier a profile declares is reached by a planned step, and none runs.

    "Reaches the profile's declared state with no step performed by
    hand" is asserted as the conjunction it is: a role-labeled tier the
    profile declares but no planned command reaches is a tier an
    operator has to create themselves on the one day the procedure is
    exercised, and a dry run that executed anything is not a rehearsal
    at all. The second half is measured from the tripwires rather than
    read off the stage's own closing line, which is asserted beside it.
    """
    with_tiers = 0
    for profile in procedure.profiles:
        tiers = [
            tier.split(":")[0] for tier in _profile_data(path=profile).get("ROLE_TIERS", "").split()
        ]
        planned: list[str] = []
        for stage in procedure.stages:
            rehearsal = _rehearse(
                procedure=procedure,
                stage=stage,
                profile=profile,
                work=tmp_path / "mnt",
            )
            assert rehearsal.executed == "", (
                f"{stage.path.name} --dry-run against {profile.name} EXECUTED: "
                f"{rehearsal.executed!r}"
            )
            if rehearsal.returncode == 0:
                assert (
                    "none executed" in rehearsal.stdout
                ), f"{stage.path.name} did not report that it executed nothing"
                planned.extend(rehearsal.planned)
        for tier in tiers:
            assert any(tier in command for command in planned), (
                f"{profile.name} declares the role tier {tier!r}, which no planned "
                f"command reaches; the plan was:\n" + "\n".join(planned)
            )
        if tiers:
            with_tiers += 1
    assert with_tiers >= 1, (
        "no committed profile declared a role tier, so the declared-state assertion "
        "held vacuously"
    )


def test_the_rehearsal_is_repeatable_and_names_no_volume_the_profile_preserves(
    *,
    procedure: _Procedure,
    tmp_path: Path,
) -> None:
    """A re-run plans the same sequence, and never a step against a preserved volume.

    The re-run clause's safe half: rehearsing the same stage against
    the same profile in the same world twice must plan the identical
    sequence, so the procedure is something an operator can re-run
    rather than a derivation that drifts. The destruction-refusal
    clause's internals-free half: a volume the profile lists as
    preserved is populated storage the host already carries, and no
    planned step may name one — exact-word, because that is how the
    procedure's own refusal matches.
    """
    preserved_seen = 0
    compared = 0
    for profile in procedure.profiles:
        preserved = _profile_data(path=profile).get("PRESERVED_PARTITIONS", "").split()
        if preserved:
            preserved_seen += 1
        for stage in procedure.stages:
            first = _rehearse(
                procedure=procedure, stage=stage, profile=profile, work=tmp_path / "mnt"
            )
            second = _rehearse(
                procedure=procedure, stage=stage, profile=profile, work=tmp_path / "mnt"
            )
            assert first.planned == second.planned, (
                f"{stage.path.name} planned a different sequence on the second "
                f"rehearsal against {profile.name}"
            )
            for command in first.planned:
                for volume in preserved:
                    assert volume not in command.split(), (
                        f"{stage.path.name} planned {command!r} naming {volume}, which "
                        f"{profile.name} lists in PRESERVED_PARTITIONS"
                    )
            compared += 1
    assert preserved_seen >= 1, (
        "no committed profile preserved a volume, so the refusal assertion held " "vacuously"
    )
    assert compared >= 2, (
        f"only {compared} stage/profile pair(s) were rehearsed; the repeatability "
        "assertion needs the committed matrix"
    )


def test_a_tree_that_cannot_reach_the_procedure_skips_rather_than_reporting_a_rehearsal(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each way of not having the procedure skips, and says which way it was.

    The rehearsal reads another repository, so a tree without a clone
    of it has nothing to rehearse. The only safe outcome there is a
    SKIP that names what was missing: a pass would be a rehearsal
    reported by a run that never ran one, and a failure would redden
    every tree that legitimately carries no sibling clone. All three
    ways of arriving there are exercised, because a resolution that
    skipped for the wrong reason reads identically to one that skipped
    for the right one.
    """
    monkeypatch.setenv("LIVESPEC_SIBLING_CLONES_ROOT", str(tmp_path))

    with pytest.raises(pytest.skip.Exception, match="did not parse"):
        _ = _provisioning_clone(config_text="{not json", slug=_PROVISIONING_SLUG)

    with pytest.raises(pytest.skip.Exception, match="not a registered cross-repo target"):
        _ = _provisioning_clone(config_text='{"cross_repo_targets": {}}', slug=_PROVISIONING_SLUG)

    with pytest.raises(pytest.skip.Exception, match="no clone of"):
        _ = _provisioning_clone(
            config_text='{"cross_repo_targets": {"' + _PROVISIONING_SLUG + '": {}}}',
            slug=_PROVISIONING_SLUG,
        )
