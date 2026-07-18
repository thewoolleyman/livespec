"""Tests for registry.py — mapping store + discovery ⋈ mapping.

Run: ``uv run pytest .claude/skills/overseer/ -q`` (these beside-tests are NOT
in the product ``tests/`` tree). ``import registry`` resolves via conftest.py.
"""

import dataclasses
import json

import pytest
import registry
from registry import Track


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Every test runs with cwd inside tmp_path (repo convention)."""
    monkeypatch.chdir(tmp_path)


# --------------------------------------------------------------------------- #
# Track dataclass.
# --------------------------------------------------------------------------- #


def test_track_is_frozen_and_keyword_only():
    track = Track(topic="t", repo="/r")
    with pytest.raises(dataclasses.FrozenInstanceError):
        track.topic = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        Track("t", "/r")  # type: ignore[call-arg]  # positional is rejected


def test_make_unassigned():
    track = Track.make_unassigned(repo="/r", topic="x", handoff="/r/plan/x/handoff.md")
    assert track.is_unassigned is True
    assert track.assigned is False
    assert track.tmux is None
    assert track.handoff == "/r/plan/x/handoff.md"


def test_repo_slug_and_tmux_id_are_repo_qualified():
    assert registry.repo_slug("/data/projects/livespec") == "livespec"
    # B1: separator is tmux-legal `--` (a `:` is sanitized to `_` by tmux and never
    # round-trips).
    assert registry.tmux_id("/data/projects/livespec", "collector") == "livespec--collector"


# --------------------------------------------------------------------------- #
# Mapping store: append / read / remove / rewrite.
# --------------------------------------------------------------------------- #


def test_append_read_roundtrip(tmp_path):
    store = tmp_path / "map.jsonl"
    registry.append_mapping(
        Track(
            topic="alpha",
            repo="/data/projects/livespec",
            tmux="livespec:alpha",
            handoff="/data/projects/livespec/plan/alpha/handoff.md",
            resume="read handoff and follow it",
            epic="livespec-0001",
            ctx_threshold=40,
            pinned_session_id="sess-1",
        ),
        store,
    )
    registry.append_mapping(
        Track(topic="beta", repo="/data/projects/other", tmux="other:beta"),
        store,
    )

    tracks = registry.read_mapping(store)
    assert [t.topic for t in tracks] == ["alpha", "beta"]
    alpha = tracks[0]
    assert alpha.tmux == "livespec:alpha"
    assert alpha.ctx_threshold == 40
    assert alpha.epic == "livespec-0001"
    assert alpha.pinned_session_id == "sess-1"
    assert alpha.assigned is True
    # A row without an explicit threshold has NO per-track override → None (so the
    # daemon-wide default applies at evaluate time), NOT DEFAULT_CTX_THRESHOLD.
    assert tracks[1].ctx_threshold is None


def test_ctx_threshold_none_is_omitted_explicit_int_roundtrips(tmp_path):
    """A track with no override (ctx_threshold=None) serializes a row WITHOUT the
    key and reads back None; an explicit int serializes the key and round-trips."""
    store = tmp_path / "map.jsonl"
    registry.append_mapping(Track(topic="nooverride", repo="/r", tmux="r--nooverride"), store)
    registry.append_mapping(
        Track(topic="pinned", repo="/r", tmux="r--pinned", ctx_threshold=60), store
    )

    rows = [json.loads(line) for line in store.read_text().splitlines() if line.strip()]
    assert "ctx_threshold" not in rows[0]  # None → key omitted
    assert rows[1]["ctx_threshold"] == 60  # explicit int → key present

    tracks = registry.read_mapping(store)
    by_topic = {t.topic: t for t in tracks}
    assert by_topic["nooverride"].ctx_threshold is None
    assert by_topic["pinned"].ctx_threshold == 60


def test_read_mapping_fail_soft_on_malformed_lines(tmp_path):
    store = tmp_path / "map.jsonl"
    good_a = json.dumps({"topic": "a", "repo": "/r"})
    good_b = json.dumps({"topic": "b", "repo": "/r"})
    store.write_text(
        good_a
        + "\n"
        + "{ this is not json\n"  # malformed → skipped
        + "\n"  # blank → skipped silently
        + "[1, 2, 3]\n"  # non-object → skipped
        + json.dumps({"repo": "/r"})  # missing topic → skipped
        + "\n"
        + good_b
        + "\n",
        encoding="utf-8",
    )
    tracks = registry.read_mapping(store)
    assert [t.topic for t in tracks] == ["a", "b"]


def test_remove_mapping_is_repo_qualified(tmp_path):
    """Same topic in two repos: removing one must not remove the other."""
    store = tmp_path / "map.jsonl"
    registry.append_mapping(Track(topic="shared", repo="/data/projects/livespec"), store)
    registry.append_mapping(Track(topic="shared", repo="/data/projects/other"), store)
    registry.append_mapping(Track(topic="solo", repo="/data/projects/livespec"), store)

    removed = registry.remove_mapping("/data/projects/livespec", "shared", store)
    assert removed == 1

    remaining = registry.read_mapping(store)
    keys = {(t.repo, t.topic) for t in remaining}
    assert keys == {("/data/projects/other", "shared"), ("/data/projects/livespec", "solo")}


def test_rewrite_mapping_preserves_unknown_keys(tmp_path):
    store = tmp_path / "map.jsonl"
    store.write_text(
        json.dumps({"topic": "a", "repo": "/r", "added_at": "2026-07-12T13:00:00Z"})
        + "\n"
        + json.dumps({"topic": "b", "repo": "/r", "added_at": "2026-07-12T14:00:00Z"})
        + "\n",
        encoding="utf-8",
    )
    dropped = registry.rewrite_mapping(lambda row: row.get("topic") != "a", store)
    assert dropped == 1

    surviving = [json.loads(line) for line in store.read_text().splitlines() if line.strip()]
    assert len(surviving) == 1
    assert surviving[0]["topic"] == "b"
    assert surviving[0]["added_at"] == "2026-07-12T14:00:00Z"  # unknown key preserved


# --------------------------------------------------------------------------- #
# Discovery.
# --------------------------------------------------------------------------- #


def _make_plan(repo, topic, *, with_handoff=True):
    plan_topic = repo / "plan" / topic
    plan_topic.mkdir(parents=True, exist_ok=True)
    if with_handoff:
        (plan_topic / "handoff.md").write_text("handoff\n", encoding="utf-8")
    return plan_topic


def test_discover_plans_excludes_archive(tmp_path):
    repo = tmp_path / "repo"
    _make_plan(repo, "topic-a")
    _make_plan(repo, "topic-b")
    # Directory existence IS the track now — a plan/<topic>/ dir with NO handoff.md
    # is still discovered (the handoff path is only a conventional pointer).
    _make_plan(repo, "no-handoff", with_handoff=False)
    # An archived plan (under plan/archive/) must still be excluded.
    archived = repo / "plan" / "archive" / "old-topic"
    archived.mkdir(parents=True)
    (archived / "handoff.md").write_text("old\n", encoding="utf-8")
    # A stray FILE directly under plan/ must be ignored (only child DIRS are tracks).
    (repo / "plan" / "README.md").write_text("x\n", encoding="utf-8")

    triples = registry.discover_plans([repo])
    topics = [topic for _repo, topic, _handoff in triples]
    # Every plan/<topic>/ dir is a track (sorted); the literal 'archive' dir excluded.
    assert topics == ["no-handoff", "topic-a", "topic-b"]
    # The handoff path is the conventional <topic>/handoff.md pointer (need not exist).
    assert triples[0][2].endswith("/repo/plan/no-handoff/handoff.md")


def test_discover_plans_fail_soft_on_missing_plan_dir(tmp_path):
    repo = tmp_path / "repo-without-plan"
    repo.mkdir()
    assert registry.discover_plans([repo]) == []


# --------------------------------------------------------------------------- #
# Join = discovery LEFT-JOIN mapping.
# --------------------------------------------------------------------------- #


def test_join_left_join_fills_and_marks_unassigned(tmp_path):
    repo = str(tmp_path / "repo")
    discovered = [
        (repo, "mapped", f"{repo}/plan/mapped/handoff.md"),
        (repo, "unmapped", f"{repo}/plan/unmapped/handoff.md"),
    ]
    mapping = [
        Track(topic="mapped", repo=repo, tmux="repo:mapped", handoff=None),  # no handoff
    ]
    rows = registry.join(discovered, mapping)
    by_topic = {t.topic: t for t in rows}

    assert by_topic["mapped"].assigned is True
    assert by_topic["mapped"].tmux == "repo:mapped"
    # Handoff filled from discovery because the mapping row lacked one.
    assert by_topic["mapped"].handoff == f"{repo}/plan/mapped/handoff.md"

    assert by_topic["unmapped"].is_unassigned is True
    assert by_topic["unmapped"].tmux is None
    assert by_topic["unmapped"].handoff == f"{repo}/plan/unmapped/handoff.md"


def test_join_is_repo_qualified_no_cross_link(tmp_path):
    """Two repos share topic 'shared'; a mapping for only one must not
    cross-link to the other (adversarial-review blocker #8)."""
    repo_a = str(tmp_path / "repo-a")
    repo_b = str(tmp_path / "repo-b")
    discovered = [
        (repo_a, "shared", f"{repo_a}/plan/shared/handoff.md"),
        (repo_b, "shared", f"{repo_b}/plan/shared/handoff.md"),
    ]
    mapping = [Track(topic="shared", repo=repo_a, tmux="repo-a:shared")]
    rows = registry.join(discovered, mapping)
    by_repo = {t.repo: t for t in rows}
    assert by_repo[repo_a].assigned is True
    assert by_repo[repo_a].tmux == "repo-a:shared"
    assert by_repo[repo_b].is_unassigned is True


# --------------------------------------------------------------------------- #
# watch_set (manifest JSONC → local checkouts with a plan/ dir).
# --------------------------------------------------------------------------- #


def _write_manifest(projects_root, fleet_names, adopter_names=()):
    core = projects_root / "livespec"
    core.mkdir(parents=True, exist_ok=True)
    fleet = ",\n".join(f'    {{ "repo": "{n}", "class": "library" }}' for n in fleet_names)
    adopters = ",\n".join(
        f'    {{ "repo": "{n}", "profile": ["baseline"], "posture": "pinned" }}'
        for n in adopter_names
    )
    manifest = (
        "// fleet membership manifest (JSONC — comments allowed)\n"
        "{\n"
        '  "owner": "thewoolleyman",\n'
        f'  "fleet": [\n{fleet}\n  ],\n'
        f'  "adopters": [\n{adopters}\n  ]\n'
        "}\n"
    )
    path = core / ".livespec-fleet-manifest.jsonc"
    path.write_text(manifest, encoding="utf-8")
    return path


def test_watch_set_selects_manifest_repos_with_plan_dir_plus_extras(tmp_path):
    projects_root = tmp_path / "projects"
    manifest_path = _write_manifest(
        projects_root,
        fleet_names=["livespec", "sibling-a", "no-plan"],
        adopter_names=["adopter-x"],
    )
    # Give each candidate a plan/ dir except 'no-plan'.
    for name in ("livespec", "sibling-a", "adopter-x"):
        (projects_root / name / "plan").mkdir(parents=True, exist_ok=True)
    (projects_root / "no-plan").mkdir(parents=True, exist_ok=True)  # no plan/ → excluded
    extra = tmp_path / "off-manifest-repo"
    extra.mkdir()

    result = registry.watch_set(manifest_path, [extra])
    result_names = {registry.repo_slug(p) for p in result}
    assert result_names == {"livespec", "sibling-a", "adopter-x", "off-manifest-repo"}
    assert "no-plan" not in result_names  # excluded: no plan/ dir
    assert all(p == registry._norm(p) for p in result)  # normalized absolute


def test_watch_set_fail_soft_on_unreadable_manifest(tmp_path):
    missing = tmp_path / "projects" / "livespec" / ".livespec-fleet-manifest.jsonc"
    extra = tmp_path / "extra"
    extra.mkdir()
    result = registry.watch_set(missing, [extra])
    assert [registry.repo_slug(p) for p in result] == ["extra"]


def test_parse_jsonc_is_string_aware_and_tolerates_trailing_comma():
    text = (
        "{\n"
        '  "url": "http://example.com/a//b",  // trailing line comment\n'
        "  /* block comment */\n"
        '  "items": ["a", "b",],\n'  # trailing comma
        "}\n"
    )
    parsed = registry._parse_jsonc(text)
    assert parsed["url"] == "http://example.com/a//b"  # // inside string preserved
    assert parsed["items"] == ["a", "b"]


# --------------------------------------------------------------------------- #
# archive-GC.
# --------------------------------------------------------------------------- #


def test_archived_or_gone(tmp_path):
    repo = tmp_path / "repo"
    _make_plan(repo, "live")
    assert registry.archived_or_gone(str(repo), "live") is False
    # Gone entirely.
    assert registry.archived_or_gone(str(repo), "never-existed") is True
    # Moved under plan/archive/.
    archived = repo / "plan" / "archive" / "retired"
    archived.mkdir(parents=True)
    assert registry.archived_or_gone(str(repo), "retired") is True


# --------------------------------------------------------------------------- #
# Injection-stamp sidecar.
# --------------------------------------------------------------------------- #


def test_injection_stamp_roundtrip_is_repo_qualified(tmp_path):
    stamp = tmp_path / "stamps.json"
    repo_a = "/data/projects/livespec"
    repo_b = "/data/projects/other"
    assert registry.read_injection_stamp(repo_a, "t", stamp) is None

    registry.write_injection_stamp(repo_a, "t", 123.5, stamp)
    assert registry.read_injection_stamp(repo_a, "t", stamp) == 123.5
    # Same topic, different repo → independent (no cross-link).
    assert registry.read_injection_stamp(repo_b, "t", stamp) is None

    registry.write_injection_stamp(repo_a, "t", 200.0, stamp)  # overwrite
    assert registry.read_injection_stamp(repo_a, "t", stamp) == 200.0


def test_injection_stamp_fail_soft_on_garbage(tmp_path):
    stamp = tmp_path / "stamps.json"
    stamp.write_text("not json at all", encoding="utf-8")
    assert registry.read_injection_stamp("/r", "t", stamp) is None


def test_archived_or_gone_active_wins_over_same_named_archive(tmp_path):
    # B6: an ACTIVE plan whose topic ALSO exists under plan/archive/ must NOT be
    # reported archived (else its mapping is GC-dropped every tick).
    repo = tmp_path / "repo"
    (repo / "plan" / "collector").mkdir(parents=True)
    (repo / "plan" / "archive" / "collector").mkdir(parents=True)
    assert registry.archived_or_gone(str(repo), "collector") is False
    # truly archived (no active dir) → True
    (repo / "plan" / "old").mkdir()  # keep plan/ around
    (repo / "plan" / "archive" / "gone").mkdir(parents=True)
    assert registry.archived_or_gone(str(repo), "gone") is True
    # plan dir simply missing under an existing repo → gone
    assert registry.archived_or_gone(str(repo), "never-existed") is True


def test_repo_root_present(tmp_path):
    assert registry.repo_root_present(str(tmp_path)) is True
    assert registry.repo_root_present(str(tmp_path / "nope")) is False


def test_clear_injection_stamp(tmp_path):
    stamp = tmp_path / "stamps.json"
    registry.write_injection_stamp("/r", "t", 123.5, stamp)
    assert registry.read_injection_stamp("/r", "t", stamp) == 123.5
    registry.clear_injection_stamp("/r", "t", stamp)
    assert registry.read_injection_stamp("/r", "t", stamp) is None
    # clearing an absent stamp is a no-op (no crash)
    registry.clear_injection_stamp("/r", "t", stamp)


def test_injection_stamp_dict_shape_bands_roundtrip(tmp_path):
    """Part 2: the sidecar value is {"at": <float>, "bands": [...]}. write opens a
    fresh round (at set, bands reset); add_notified_band appends idempotently and
    preserves at; a re-write resets the bands for the new round."""
    stamp = tmp_path / "stamps.json"
    registry.write_injection_stamp("/r", "t", 500.0, stamp)
    assert registry.read_injection_stamp("/r", "t", stamp) == 500.0
    assert registry.read_notified_bands("/r", "t", stamp) == []  # fresh round: no bands

    registry.add_notified_band("/r", "t", 45, stamp)
    registry.add_notified_band("/r", "t", 40, stamp)
    registry.add_notified_band("/r", "t", 45, stamp)  # duplicate → idempotent no-op
    assert registry.read_notified_bands("/r", "t", stamp) == [45, 40]
    assert registry.read_injection_stamp("/r", "t", stamp) == 500.0  # `at` preserved

    registry.write_injection_stamp("/r", "t", 600.0, stamp)  # a NEW round resets bands
    assert registry.read_notified_bands("/r", "t", stamp) == []
    assert registry.read_injection_stamp("/r", "t", stamp) == 600.0


def test_clear_injection_stamp_resets_at_and_bands(tmp_path):
    """Part 2: clear deletes the key entirely → both `at` and `bands` reset."""
    stamp = tmp_path / "stamps.json"
    registry.write_injection_stamp("/r", "t", 500.0, stamp)
    registry.add_notified_band("/r", "t", 45, stamp)
    registry.clear_injection_stamp("/r", "t", stamp)
    assert registry.read_injection_stamp("/r", "t", stamp) is None
    assert registry.read_notified_bands("/r", "t", stamp) == []


def test_injection_stamp_legacy_bare_float_backcompat(tmp_path):
    """Part 2 back-compat: a pre-escalation sidecar stores a BARE float per key.
    read_injection_stamp still returns it, read_notified_bands is empty, and
    add_notified_band UPGRADES the value to the dict shape preserving the float
    as `at`."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(json.dumps({"/r\tt": 321.0}), encoding="utf-8")  # legacy bare-float value
    assert registry.read_injection_stamp("/r", "t", stamp) == 321.0
    assert registry.read_notified_bands("/r", "t", stamp) == []
    registry.add_notified_band("/r", "t", 45, stamp)
    assert registry.read_injection_stamp("/r", "t", stamp) == 321.0  # `at` preserved on upgrade
    assert registry.read_notified_bands("/r", "t", stamp) == [45]


def test_write_rows_is_atomic_and_skips_when_unchanged(tmp_path):
    # B6: rewrite_mapping skips the write entirely when no row is dropped.
    store = tmp_path / "map.jsonl"
    registry.append_mapping(registry.Track(topic="a", repo="/r", tmux="r--a"), store)
    before = store.stat().st_mtime_ns
    dropped = registry.rewrite_mapping(lambda _row: True, store)  # keep all
    assert dropped == 0
    assert store.stat().st_mtime_ns == before  # unchanged → not rewritten


def test_resume_pending_roundtrip_and_preserves_at_and_bands(tmp_path):
    """R1: set_resume_pending marks the flag on the round dict WITHOUT disturbing `at`
    (so the ready marker still certifies — mtime > at) or the notified bands."""
    stamp = tmp_path / "stamps.json"
    registry.write_injection_stamp("/r", "t", 500.0, stamp)
    registry.add_notified_band("/r", "t", 40, stamp)
    assert registry.read_resume_pending("/r", "t", stamp) is False  # not set yet

    registry.set_resume_pending("/r", "t", stamp)
    assert registry.read_resume_pending("/r", "t", stamp) is True
    assert registry.read_injection_stamp("/r", "t", stamp) == 500.0  # `at` preserved
    assert registry.read_notified_bands("/r", "t", stamp) == [40]  # bands preserved


def test_resume_pending_is_cleared_by_round_close_and_by_a_fresh_round(tmp_path):
    """R1: the pending flag is round-scoped — clear_injection_stamp (restart closed) and
    write_injection_stamp (a fresh round) both drop it, so it can never outlive its round."""
    stamp = tmp_path / "stamps.json"
    registry.write_injection_stamp("/r", "t", 500.0, stamp)
    registry.set_resume_pending("/r", "t", stamp)
    registry.clear_injection_stamp("/r", "t", stamp)
    assert registry.read_resume_pending("/r", "t", stamp) is False  # round closed → flag gone

    registry.write_injection_stamp("/r", "t", 600.0, stamp)
    registry.set_resume_pending("/r", "t", stamp)
    registry.write_injection_stamp("/r", "t", 700.0, stamp)  # a NEW round overwrites the dict
    assert registry.read_resume_pending("/r", "t", stamp) is False


def test_repoint_tmux_rewrites_only_the_matching_row_and_is_idempotent(tmp_path):
    """R2: repoint_tmux rewrites a (repo, topic) row's tmux field, preserves unknown keys,
    leaves other rows untouched, and no-ops (returns False, no write) when already correct."""
    store = tmp_path / "map.jsonl"
    store.write_text(
        json.dumps({"topic": "a", "repo": "/r", "tmux": "old", "added_at": "keep"})
        + "\n"
        + json.dumps({"topic": "b", "repo": "/r", "tmux": "b-tmux"})
        + "\n",
        encoding="utf-8",
    )
    assert registry.repoint_tmux("/r", "a", "new", store) is True
    rows = {r.topic: r.tmux for r in registry.read_mapping(store)}
    assert rows == {"a": "new", "b": "b-tmux"}  # only `a` moved
    raw_a = next(
        json.loads(ln) for ln in store.read_text().splitlines() if json.loads(ln)["topic"] == "a"
    )
    assert raw_a["added_at"] == "keep"  # unknown key survives the rewrite

    before = store.stat().st_mtime_ns
    assert registry.repoint_tmux("/r", "a", "new", store) is False  # already correct → no-op
    assert store.stat().st_mtime_ns == before  # not rewritten
    assert registry.repoint_tmux("/r", "missing", "x", store) is False  # no such row → no-op
