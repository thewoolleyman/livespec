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
What is rehearsed is the producer AT THE RELEASE THIS REPOSITORY
PINS — the `pyproject.toml` `[tool.uv.sources]` tag, which is the
version this consumer actually runs — so the rehearsal is the same
procedure in a factory sandbox, on a laptop and in CI rather than
whatever a nearby working tree happens to be on. That pinned release
is reached from either of two sources, and NEITHER is allowed to
decide whether the rehearsal happens: the sibling clone resolved
through this project's own committed seam (the `.livespec.jsonc`
`cross_repo_targets` entry plus `resolve_effective_local_clone`, which
honors the `LIVESPEC_SIBLING_CLONES_ROOT` override) when that clone
carries the pinned tag, and otherwise a shallow fetch of exactly that
tag from the `github_url` the pin itself names. So no clone path and
no release is spelled here, and a tree with no sibling checkout — a
GitHub Actions runner, say — rehearses identically instead of skipping
into an unexecuted body. Only a tree that can reach the release
through neither source skips, and it names both sources it tried.

The procedure's location inside the producer is then DERIVED from the
producer's own ratified obligation section: the one `## ` section of
its `non-functional-requirements.md` that quotes this repository's
clause title, read out of its git database at the pinned tag. The
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
database at the pinned release — committed state, never a working tree
that may lag or carry edits — and RUNS the real stages, unmodified,
against the real committed per-host profiles, on a scratch `PATH` whose
probes answer nothing. "Probes answer nothing" IS the scenario's empty storage, and
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
_PRODUCER_FORGE = "https://github.com/thewoolleyman/livespec-dev-tooling.git"
_CLAUSE_TITLE = (
    "A host carrying fleet CI MUST be rebuildable from bare metal by a committed procedure"
)
_STAGE_DIR_MARK = "phase0-bare-metal/"
_BACKTICKED = re.compile(r"`([^`\s]+)`")
_DATA_LINE = re.compile(r"^[A-Z][A-Z0-9_]*=")
_TIMEOUT_S = 300.0
# The branch the harness's stand-in producer repositories are initialized on.
# Named explicitly so a git default-branch setting cannot change what they are.
_STANDIN_BRANCH = "main"

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
class _Pin:
    """The producer release this repository declares it consumes."""

    url: str
    tag: str


@dataclass(frozen=True, kw_only=True)
class _Producer:
    """A git database holding the pinned release, and the ref naming it there."""

    clone: Path
    ref: str
    source: str


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


def _pinned_release(*, pyproject_text: str, slug: str) -> _Pin:
    """Read the producer release this repository pins out of its own manifest.

    The pin is the single fact that makes the rehearsal reproducible:
    it names both the release to rehearse and the forge to fetch it
    from, so no environment contributes either. A manifest declaring
    the producer twice is a failure rather than a first-wins guess.
    """
    pattern = re.compile(
        rf'^{re.escape(slug)}\s*=\s*\{{\s*git\s*=\s*"(?P<url>[^"]+)"\s*,'
        rf'\s*tag\s*=\s*"(?P<tag>[^"]+)"\s*\}}\s*$',
        re.MULTILINE,
    )
    found = list(pattern.finditer(pyproject_text))
    assert len(found) == 1, (
        f"this repository's manifest must pin {slug} to exactly one git tag for the "
        f"rehearsal to name a release; found {len(found)} such pins"
    )
    return _Pin(url=found[0].group("url"), tag=found[0].group("tag"))


def _local_clone_at_pin(*, config_text: str, slug: str, tag: str) -> Path | None:
    """The sibling clone resolved through this project's seam, if it holds `tag`.

    Returns `None` — never a skip — for every outcome that is not a
    clone carrying the pinned release, because a missing sibling
    checkout is a fact about the machine rather than about the
    procedure, and the caller reaches the same release from the forge
    instead. A clone that exists but has not fetched the pinned tag
    counts as not having it: rehearsing its `HEAD` would rehearse
    whatever that checkout happens to be on.
    """
    parsed_result = jsonc.loads(text=config_text)
    if not isinstance(parsed_result, Success):
        return None
    parsed: Any = parsed_result.unwrap()
    targets: Any = parsed.get("cross_repo_targets") if isinstance(parsed, dict) else None
    target: Any = targets.get(slug) if isinstance(targets, dict) else None
    if not isinstance(target, dict):
        return None
    resolved = resolve_effective_local_clone(sibling_slug=slug, target=target)
    if resolved is None or not (Path(resolved) / ".git").exists():
        return None
    carries = _run(
        args=["git", "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"], cwd=Path(resolved)
    )
    if carries.returncode != 0:
        return None
    return Path(resolved)


def _fetched_clone_at_pin(*, url: str, tag: str, dest: Path) -> Path | None:
    """Shallow-fetch exactly the pinned release from the producer's forge.

    One commit and one tag, so the fetch costs about what reading a
    local clone would. Returns `None` when the forge cannot be reached
    or does not carry the tag; terminal prompting is disabled so an
    unreachable forge fails rather than waiting for a credential
    nobody is there to type.
    """
    dest.mkdir(parents=True, exist_ok=True)
    into = dest / "forge"
    cloned = _run(
        args=["git", "clone", "--depth", "1", "--branch", tag, url, str(into)],
        cwd=dest,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "LC_ALL": "C"},
    )
    if cloned.returncode != 0:
        return None
    return into


def _producer_at_pin(
    *,
    config_text: str,
    pyproject_text: str,
    slug: str,
    dest: Path,
) -> _Producer:
    """Reach the pinned producer release from a local clone or from the forge.

    Whether a sibling checkout happens to exist decides only WHICH
    source is read, never whether the rehearsal runs — that is what
    makes this module behave the same in a factory sandbox, on a
    laptop and on a CI runner that checks out no sibling repository.
    The one remaining skip is a tree that can reach the release
    through neither source, which names both it tried.
    """
    pin = _pinned_release(pyproject_text=pyproject_text, slug=slug)
    local = _local_clone_at_pin(config_text=config_text, slug=slug, tag=pin.tag)
    if local is not None:
        return _Producer(clone=local, ref=pin.tag, source=f"local clone {local}")
    fetched = _fetched_clone_at_pin(url=pin.url, tag=pin.tag, dest=dest)
    if fetched is None:
        pytest.skip(
            f"{slug} at the pinned release {pin.tag} is reachable neither as a local "
            f"clone carrying that tag nor by fetching it from {pin.url}; the committed "
            "procedure cannot be rehearsed"
        )
    return _Producer(clone=fetched, ref=pin.tag, source=f"shallow fetch of {pin.tag}")


def _synthetic_pin(*, url: str, tag: str) -> str:
    """A manifest fragment pinning the producer, for exercising the harness itself."""
    return f'{_PROVISIONING_SLUG} = {{ git = "{url}", tag = "{tag}" }}\n'


def _synthetic_producer(*, root: Path, tag: str | None) -> Path:
    """A throwaway git repository standing in for the producer's forge copy."""
    root.mkdir(parents=True)
    for args in (
        ["git", "init", "--quiet", f"--initial-branch={_STANDIN_BRANCH}"],
        ["git", "config", "user.email", "rehearsal@example.invalid"],
        ["git", "config", "user.name", "Rehearsal"],
        ["git", "commit", "--quiet", "--allow-empty", "-m", "stand-in for the producer"],
        *([["git", "tag", tag]] if tag is not None else []),
    ):
        done = _run(args=args, cwd=root)
        assert done.returncode == 0, f"{' '.join(args)} failed: {done.stderr}"
    return root


def _derive_stage_dir(*, producer: _Producer) -> str:
    """Read the bare-metal stage's path out of the producer's own clause."""
    shown = _run(args=["git", "show", f"{producer.ref}:{_PRODUCER_SPEC}"], cwd=producer.clone)
    assert shown.returncode == 0, (
        f"{_PROVISIONING_SLUG} committed no {_PRODUCER_SPEC} at {producer.ref} "
        f"({producer.source}): {shown.stderr}"
    )
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


def _materialize(*, producer: _Producer, dest: Path) -> Path:
    """Extract the producer's committed tree at the pinned release into `dest`."""
    archive = dest / "tree.tar"
    written = _run(
        args=["git", "archive", "--format=tar", "-o", str(archive), producer.ref],
        cwd=producer.clone,
    )
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
    dest = tmp_path_factory.mktemp("provisioning")
    producer = _producer_at_pin(
        config_text=(_REPO_ROOT / ".livespec.jsonc").read_text(encoding="utf-8"),
        pyproject_text=(_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        slug=_PROVISIONING_SLUG,
        dest=dest,
    )
    stage_relative = _derive_stage_dir(producer=producer)
    stage_dir = _materialize(producer=producer, dest=dest) / stage_relative
    assert stage_dir.is_dir(), (
        f"{_PROVISIONING_SLUG}'s clause names {stage_relative!r} as the bare-metal "
        f"stage, but {producer.ref} commits no such directory"
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


def test_the_release_rehearsed_is_the_one_this_repository_pins(*, tmp_path: Path) -> None:
    """The rehearsed release comes from the pin, not from any nearby checkout.

    What makes the rehearsal mean the same thing everywhere is that
    the release is read out of this repository's own manifest. So the
    pin is asserted to be a single entry naming the producer's forge
    and a release tag, and the module's `_PRODUCER_FORGE` is asserted
    to still be the forge the pin names — the one place this file
    repeats a fact the manifest owns.
    """
    pin = _pinned_release(
        pyproject_text=(_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        slug=_PROVISIONING_SLUG,
    )
    assert pin.url == _PRODUCER_FORGE, (
        f"this repository now pins {_PROVISIONING_SLUG} from {pin.url}, so the forge "
        f"this module names ({_PRODUCER_FORGE}) is stale"
    )
    assert re.fullmatch(r"v\d+\.\d+\.\d+", pin.tag), (
        f"the rehearsal needs a release tag to materialize; the pin reads {pin.tag!r}, "
        "which is not one"
    )

    doubled = _synthetic_pin(url="https://example.invalid/x.git", tag="v1.0.0") * 2
    with pytest.raises(AssertionError, match="exactly one git tag"):
        _ = _pinned_release(pyproject_text=doubled, slug=_PROVISIONING_SLUG)

    assert _fetched_clone_at_pin(url=str(tmp_path / "absent"), tag="v1.0.0", dest=tmp_path) is None


def test_a_local_clone_is_used_only_when_it_carries_the_pin_and_never_gates_the_rehearsal(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sibling checkout chooses the SOURCE; it never decides whether this runs.

    This is the harness's own guard, and it is the assertion that
    keeps this module honest on a machine with no sibling checkout —
    a GitHub Actions runner, which checks out no sibling repository
    and would otherwise skip into a body nothing ever executes. So
    every way of not having a usable local clone is exercised against
    a stand-in producer whose own forge is a path on disk: each one
    must FALL BACK to the fetch and still yield the pinned release,
    and only a release reachable through neither source may skip.
    """
    monkeypatch.setenv("LIVESPEC_SIBLING_CLONES_ROOT", str(tmp_path / "clones"))
    tag = "v9.99.99"
    forge = _synthetic_producer(root=tmp_path / "forge", tag=tag)
    pyproject = _synthetic_pin(url=f"file://{forge}", tag=tag)
    registered = '{"cross_repo_targets": {"' + _PROVISIONING_SLUG + '": {}}}'

    def resolve(*, config_text: str, dest: Path) -> _Producer:
        return _producer_at_pin(
            config_text=config_text,
            pyproject_text=pyproject,
            slug=_PROVISIONING_SLUG,
            dest=dest,
        )

    unusable = {
        "a manifest that does not parse": "{not json",
        "an unregistered cross-repo target": '{"cross_repo_targets": {}}',
        "no clone at the resolved path": registered,
    }
    for why, config_text in unusable.items():
        assert (
            _local_clone_at_pin(config_text=config_text, slug=_PROVISIONING_SLUG, tag=tag) is None
        )
        fell_back = resolve(config_text=config_text, dest=tmp_path / f"fetch-{len(why)}")
        assert fell_back.ref == tag and "fetch" in fell_back.source, (
            f"{why} must fall back to fetching the pinned release, not decide whether "
            f"the rehearsal happens; got {fell_back.source}"
        )

    present = _synthetic_producer(root=tmp_path / "clones" / _PROVISIONING_SLUG, tag=None)
    assert _local_clone_at_pin(config_text=registered, slug=_PROVISIONING_SLUG, tag=tag) is None
    fell_back = resolve(config_text=registered, dest=tmp_path / "fetch-untagged")
    assert "fetch" in fell_back.source, (
        "a clone that has not fetched the pinned tag must not be rehearsed at its own "
        f"HEAD; got {fell_back.source}"
    )

    tagged = _run(args=["git", "tag", tag], cwd=present)
    assert tagged.returncode == 0, f"tagging the stand-in clone failed: {tagged.stderr}"
    assert _local_clone_at_pin(config_text=registered, slug=_PROVISIONING_SLUG, tag=tag) == present
    from_local = resolve(config_text=registered, dest=tmp_path / "unused")
    assert from_local.clone == present and from_local.ref == tag, (
        "a local clone carrying the pinned tag is the cheaper source and must be "
        f"preferred; got {from_local.source}"
    )

    unreachable = _synthetic_pin(url=str(tmp_path / "no-such-forge"), tag=tag)
    with pytest.raises(pytest.skip.Exception, match="reachable neither as a local clone"):
        _ = _producer_at_pin(
            config_text='{"cross_repo_targets": {}}',
            pyproject_text=unreachable,
            slug=_PROVISIONING_SLUG,
            dest=tmp_path / "fetch-unreachable",
        )
