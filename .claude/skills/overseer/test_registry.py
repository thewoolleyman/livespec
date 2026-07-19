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


def test_tmux_id_is_the_bare_topic_by_default():
    # Default (no known collision): a session is named after the bare plan topic —
    # NOT repo-qualified (maintainer-declared 2026-07-19). repo_slug still returns the
    # basename (it is used for DISPLAY and for the collision prefix below).
    assert registry.repo_slug("/data/projects/livespec") == "livespec"
    assert registry.tmux_id("/data/projects/livespec", "collector") == "collector"
    # A topic that itself contains dashes stays bare (a dash is never sanitized).
    assert registry.tmux_id("/data/projects/livespec", "autonomous-mode") == "autonomous-mode"


def test_tmux_id_single_dash_repo_prefix_only_on_collision():
    # When the topic collides across repos, and ONLY then, it is repo-qualified as
    # `<slug>-<topic>` with a SINGLE dash (not the retired double-dash).
    assert (
        registry.tmux_id("/data/projects/livespec", "collector", {"collector"})
        == "livespec-collector"
    )
    # A collision set that does NOT contain this topic leaves it bare.
    assert registry.tmux_id("/data/projects/livespec", "collector", {"other"}) == "collector"


def test_colliding_topics_are_topics_in_two_or_more_repos():
    discovered = [
        ("/data/projects/livespec", "shared", "h1"),
        ("/data/projects/livespec-console-beads-fabro", "shared", "h2"),
        ("/data/projects/livespec", "solo", "h3"),
    ]
    assert registry.colliding_topics(discovered) == frozenset({"shared"})


def test_colliding_topics_ignores_the_same_repo_seen_twice():
    # Two triples for the SAME (normalized) repo + topic is NOT a cross-repo collision.
    discovered = [
        ("/data/projects/livespec", "dup", "h1"),
        ("/data/projects/livespec/", "dup", "h2"),
    ]
    assert registry.colliding_topics(discovered) == frozenset()


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
# Fail-soft store resilience (B6/B7): a corrupt, unreadable, or unwritable store
# must degrade ONE reader/writer and never crash the daemon that supervises all
# tracks. Every case asserts the fail-soft RESULT, not merely that nothing raised.
# --------------------------------------------------------------------------- #


def test_file_lock_proceeds_unlocked_when_the_lock_cannot_be_acquired(
    tmp_path, monkeypatch, capsys
):
    """B7: losing the lock race is better than losing the daemon — an unlockable
    store falls back to an UNLOCKED read-modify-write and the append still lands."""
    store = tmp_path / "map.jsonl"

    def _refuse_flock(_fd, _operation):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(registry.fcntl, "flock", _refuse_flock)
    registry.append_mapping(Track(topic="a", repo="/r", tmux="r-a"), store)

    assert [t.topic for t in registry.read_mapping(store)] == ["a"]  # write still landed
    assert "could not acquire lock" in capsys.readouterr().err


def test_file_lock_proceeds_unlocked_when_the_lock_file_cannot_be_opened(tmp_path, capsys):
    """B7: the lock sidecar failing to OPEN (no handle was ever acquired) takes the
    same unlocked fallback — the caller runs and reports, and the daemon lives."""
    unwritable = tmp_path / "unwritable"
    unwritable.mkdir()
    unwritable.chmod(0o500)  # readable + traversable, but nothing may be created in it
    store = unwritable / "map.jsonl"
    try:
        registry.append_mapping(Track(topic="a", repo="/r"), store)
        assert registry.read_mapping(store) == []  # the append itself also failed soft
    finally:
        unwritable.chmod(0o755)

    err = capsys.readouterr().err
    assert "could not acquire lock" in err
    assert "could not append to" in err
    assert not (unwritable / "map.jsonl.lock").exists()  # no lock sidecar was created


def test_read_mapping_fail_soft_on_an_unreadable_store(tmp_path, capsys):
    """B7: a store that exists but cannot be read yields an EMPTY mapping (naming
    the offender), not a propagated PermissionError."""
    store = tmp_path / "map.jsonl"
    store.write_text(json.dumps({"topic": "a", "repo": "/r"}) + "\n", encoding="utf-8")
    store.chmod(0o000)
    try:
        assert registry.read_mapping(store) == []
    finally:
        store.chmod(0o600)
    assert "unreadable mapping store" in capsys.readouterr().err


def test_atomic_write_fail_soft_leaves_the_store_intact_and_removes_the_temp(
    tmp_path, monkeypatch, capsys
):
    """B6/B7: a mid-write failure must never truncate the store nor leave a ``.tmp``
    turd behind — the temp file is unlinked and the old content survives whole."""
    store = tmp_path / "map.jsonl"
    store.write_text(json.dumps({"topic": "keep", "repo": "/r"}) + "\n", encoding="utf-8")

    def _boom(_fd):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(registry.os, "fsync", _boom)
    registry._write_rows([{"topic": "replacement", "repo": "/r"}], store)

    assert [t.topic for t in registry.read_mapping(store)] == ["keep"]  # not truncated
    assert [p.name for p in tmp_path.iterdir()] == ["map.jsonl"]  # temp file cleaned up
    assert "could not write" in capsys.readouterr().err


def test_append_mapping_fail_soft_when_the_store_cannot_be_opened(tmp_path, capsys):
    """B7: an unopenable store path (here a DIRECTORY sitting where the file
    belongs) drops the append with a warning instead of crashing the caller."""
    store = tmp_path / "map.jsonl"
    store.mkdir()
    registry.append_mapping(Track(topic="a", repo="/r"), store)

    assert registry.read_mapping(store) == []  # nothing recorded, nothing raised
    assert "could not append to" in capsys.readouterr().err


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


def test_discover_plans_fail_soft_on_an_unreadable_plan_dir(tmp_path, capsys):
    """B7: a plan/ that becomes unlistable between the is_dir check and iterdir
    (chmod, NFS hiccup, mid-clone) skips that ONE repo — every other watched repo
    still contributes, rather than the whole discovery pass crashing the daemon."""
    poisoned = tmp_path / "repo-poisoned"
    _make_plan(poisoned, "topic-a")
    healthy = tmp_path / "repo-healthy"
    _make_plan(healthy, "topic-b")
    (poisoned / "plan").chmod(0o000)  # unlistable, but still stats as a dir
    try:
        triples = registry.discover_plans([poisoned, healthy])
    finally:
        (poisoned / "plan").chmod(0o755)

    assert [(registry.repo_slug(r), t) for r, t, _h in triples] == [("repo-healthy", "topic-b")]
    assert "unreadable plan dir" in capsys.readouterr().err


def test_discover_plans_fail_soft_on_an_unreadable_plan_child(tmp_path, capsys):
    """B7: with plan/ readable but not traversable (r--), iterdir still lists the
    children while stat'ing one raises — that child is dropped and named, and the
    rest of the discovery set survives."""
    poisoned = tmp_path / "repo-poisoned"
    _make_plan(poisoned, "unstattable")
    healthy = tmp_path / "repo-healthy"
    _make_plan(healthy, "topic-b")
    (poisoned / "plan").chmod(0o444)
    try:
        triples = registry.discover_plans([poisoned, healthy])
    finally:
        (poisoned / "plan").chmod(0o755)

    assert [(registry.repo_slug(r), t) for r, t, _h in triples] == [("repo-healthy", "topic-b")]
    assert "unreadable plan child" in capsys.readouterr().err


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


def test_parse_jsonc_honors_backslash_escapes_inside_a_string_literal():
    # A BACKSLASH-ESCAPED quote does not end the literal, so the `//` and `/*` that
    # follow it are still INSIDE the string and must survive stripping. An escaped
    # backslash is likewise consumed as one character, not as an escape of the quote.
    parsed = registry._parse_jsonc(r'{"a": "x\"y // z /* w */", "b": "trailing\\"}')
    assert parsed["a"] == 'x"y // z /* w */'
    assert parsed["b"] == "trailing\\"


def test_strip_jsonc_comments_consumes_an_unterminated_string_literal():
    # The stripper is not a validator: an unterminated literal runs to the end of
    # the input, so the `//` inside it is preserved rather than treated as the
    # start of a comment. Reporting the malformed JSON is json.loads's job.
    text = '{"a": "unterminated // not-a-comment'
    assert registry._strip_jsonc_comments(text) == text
    with pytest.raises(json.JSONDecodeError):
        registry._parse_jsonc(text)


def test_watch_set_skips_a_non_list_section_and_non_dict_entries(tmp_path):
    """The manifest walk is fail-soft over shape: a section that is not an array,
    and array members that are not objects, contribute nothing while the
    well-formed entries in the same manifest still resolve."""
    projects_root = tmp_path / "projects"
    core = projects_root / "livespec"
    core.mkdir(parents=True)
    manifest_path = core / ".livespec-fleet-manifest.jsonc"
    manifest_path.write_text(
        "{\n"
        '  "fleet": "not-a-list",\n'  # non-list section → skipped wholesale
        '  "adopters": ["bare-string", 7, null, { "repo": 7 }, { "repo": "sibling-a" }]\n'
        "}\n",
        encoding="utf-8",
    )
    (projects_root / "sibling-a" / "plan").mkdir(parents=True)

    result = registry.watch_set(manifest_path)
    assert [registry.repo_slug(p) for p in result] == ["sibling-a"]


def test_watch_set_dedupes_extras_against_the_manifest_and_skips_missing_ones(tmp_path):
    """An extra_repo that the manifest ALREADY selected appears exactly once — a repo
    listed twice would be discovered, and therefore supervised, twice. An extra with
    no checkout on disk contributes nothing."""
    projects_root = tmp_path / "projects"
    manifest_path = _write_manifest(projects_root, fleet_names=["sibling-a"])
    (projects_root / "sibling-a" / "plan").mkdir(parents=True)

    result = registry.watch_set(
        manifest_path,
        [projects_root / "sibling-a", tmp_path / "no-such-checkout"],
    )
    assert [registry.repo_slug(p) for p in result] == ["sibling-a"]


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


def test_repo_root_present_is_false_when_the_root_cannot_be_stated(tmp_path):
    """B6: a root that raises rather than answering (an untraversable parent — the
    unmounted-volume / mid-move case) reads as ABSENT, so the daemon's GC keeps the
    mapping row instead of crashing the tick."""
    parent = tmp_path / "untraversable"
    (parent / "repo").mkdir(parents=True)
    parent.chmod(0o000)
    try:
        assert registry.repo_root_present(str(parent / "repo")) is False
    finally:
        parent.chmod(0o755)


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


# --------------------------------------------------------------------------- #
# Injection-stamp sidecar: fail-soft over a corrupt / legacy / half-shaped value.
# --------------------------------------------------------------------------- #


def test_injection_stamp_fail_soft_when_the_sidecar_is_not_a_json_object(tmp_path, capsys):
    """Well-formed JSON of the WRONG shape (a bare array) is reported distinctly
    from malformed JSON, and every reader degrades to its empty answer."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(json.dumps([1, 2]), encoding="utf-8")

    assert registry.read_injection_stamp("/r", "t", stamp) is None
    assert registry.read_notified_bands("/r", "t", stamp) == []
    assert registry.read_resume_pending("/r", "t", stamp) is False
    assert "is not a JSON object" in capsys.readouterr().err


def test_read_injection_stamp_is_none_when_the_round_dict_has_no_at(tmp_path):
    """A dict-shaped value that never opened a round (no ``at``) has no timestamp —
    but the rest of the entry is still readable, so it is not discarded wholesale."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(
        json.dumps({"/r\tt": {"bands": [45], "resume_pending": True}}), encoding="utf-8"
    )
    assert registry.read_injection_stamp("/r", "t", stamp) is None
    assert registry.read_notified_bands("/r", "t", stamp) == [45]
    assert registry.read_resume_pending("/r", "t", stamp) is True


def test_read_injection_stamp_warns_and_returns_none_on_a_non_numeric_stamp(tmp_path, capsys):
    """Both sidecar shapes name the offending track on an unusable ``at``. ``true``
    is deliberately NOT numeric (jsonio.as_float rejects bool, which is an int
    subclass), so it must not silently read back as 1.0."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(
        json.dumps({"/r\tdict": {"at": True}, "/r\tlegacy": "not-a-number"}), encoding="utf-8"
    )
    assert registry.read_injection_stamp("/r", "dict", stamp) is None
    assert registry.read_injection_stamp("/r", "legacy", stamp) is None

    err = capsys.readouterr().err
    assert "non-numeric injection stamp for /r::dict" in err
    assert "non-numeric injection stamp for /r::legacy" in err


def test_read_notified_bands_ignores_a_non_list_bands_member(tmp_path):
    """A ``bands`` member of the wrong type reads as "nothing notified yet" without
    costing the entry its still-usable ``at``."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(json.dumps({"/r\tt": {"at": 500.0, "bands": "45"}}), encoding="utf-8")
    assert registry.read_notified_bands("/r", "t", stamp) == []
    assert registry.read_injection_stamp("/r", "t", stamp) == 500.0


def test_add_notified_band_on_a_track_with_no_open_round(tmp_path):
    """Part 2: an absent key yields a bare bands-only entry — the band is recorded
    without inventing an ``at`` (no round was opened, so none may certify)."""
    stamp = tmp_path / "stamps.json"
    registry.add_notified_band("/r", "t", 45, stamp)
    assert registry.read_notified_bands("/r", "t", stamp) == [45]
    assert registry.read_injection_stamp("/r", "t", stamp) is None


def test_set_resume_pending_on_a_track_with_no_open_round(tmp_path):
    """R1: the retry keys on the FLAG, not on ``at`` — an absent key is written as a
    bare {"resume_pending": true} so the submit still retries."""
    stamp = tmp_path / "stamps.json"
    registry.set_resume_pending("/r", "t", stamp)
    assert registry.read_resume_pending("/r", "t", stamp) is True
    assert registry.read_injection_stamp("/r", "t", stamp) is None


def test_set_resume_pending_upgrades_a_legacy_bare_scalar_value(tmp_path):
    """R1 back-compat: a legacy bare-float value is upgraded to the dict shape with
    the float preserved as ``at``; a legacy bare NON-numeric value is unusable, so
    the upgrade keeps only the flag."""
    stamp = tmp_path / "stamps.json"
    stamp.write_text(
        json.dumps({"/r\tnumeric": 321.0, "/r\tjunk": "not-a-number"}), encoding="utf-8"
    )
    registry.set_resume_pending("/r", "numeric", stamp)
    registry.set_resume_pending("/r", "junk", stamp)

    assert registry.read_resume_pending("/r", "numeric", stamp) is True
    assert registry.read_injection_stamp("/r", "numeric", stamp) == 321.0  # `at` preserved
    assert registry.read_resume_pending("/r", "junk", stamp) is True
    assert registry.read_injection_stamp("/r", "junk", stamp) is None  # unusable → dropped
