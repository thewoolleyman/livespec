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
    # A row without an explicit threshold defaults.
    assert tracks[1].ctx_threshold == registry.DEFAULT_CTX_THRESHOLD


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


def test_discover_plans_excludes_archive_and_handoffless(tmp_path):
    repo = tmp_path / "repo"
    _make_plan(repo, "topic-a")
    _make_plan(repo, "topic-b")
    _make_plan(repo, "no-handoff", with_handoff=False)  # excluded: no handoff.md
    # An archived plan (under plan/archive/) must be excluded.
    archived = repo / "plan" / "archive" / "old-topic"
    archived.mkdir(parents=True)
    (archived / "handoff.md").write_text("old\n", encoding="utf-8")
    # A stray file directly under plan/ must be ignored.
    (repo / "plan" / "README.md").write_text("x\n", encoding="utf-8")

    triples = registry.discover_plans([repo])
    topics = [topic for _repo, topic, _handoff in triples]
    assert topics == ["topic-a", "topic-b"]
    # Handoff path is absolute and points at the topic's handoff.md.
    assert triples[0][2].endswith("/repo/plan/topic-a/handoff.md")


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


def test_write_rows_is_atomic_and_skips_when_unchanged(tmp_path):
    # B6: rewrite_mapping skips the write entirely when no row is dropped.
    store = tmp_path / "map.jsonl"
    registry.append_mapping(registry.Track(topic="a", repo="/r", tmux="r--a"), store)
    before = store.stat().st_mtime_ns
    dropped = registry.rewrite_mapping(lambda _row: True, store)  # keep all
    assert dropped == 0
    assert store.stat().st_mtime_ns == before  # unchanged → not rewritten
