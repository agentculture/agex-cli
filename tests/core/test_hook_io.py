from concurrent.futures import ThreadPoolExecutor

from agent_experience.core.hook_io import append_event, load_events, render_table
from agent_experience.core.paths import ensure_init


def test_append_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    append_event("post-tool-use", {"tool": "Read", "ts": "2026-04-18T10:00:00Z"})
    append_event("post-tool-use", {"tool": "Write", "ts": "2026-04-18T10:00:01Z"})
    events = load_events("post-tool-use")
    assert len(events) == 2
    assert events[0]["tool"] == "Read"


def test_load_events_missing_stream_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    assert load_events("never-written") == []


def test_append_event_rejects_invalid_stream_name(tmp_path, monkeypatch):
    import pytest

    monkeypatch.chdir(tmp_path)
    ensure_init()
    for bad in ("../evil", "/etc/passwd", "..", "a/b", "UPPER", "_leading"):
        with pytest.raises(ValueError, match="invalid stream name"):
            append_event(bad, {"k": "v"})
        with pytest.raises(ValueError, match="invalid stream name"):
            load_events(bad)
    # Ensure no stray files landed in .agex/data/
    assert list((tmp_path / ".agex" / "data").iterdir()) == []


def test_load_events_skips_malformed_lines_with_warning(tmp_path, monkeypatch):
    import pytest

    monkeypatch.chdir(tmp_path)
    ensure_init()
    # Write a mix of valid and malformed lines (simulates a partial write
    # or an externally edited data file).
    data_file = tmp_path / ".agex" / "data" / "post-tool-use.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(
        '{"ts":"2026-04-18T10:00:00Z","tool":"Read"}\n'
        '{"ts":"2026-04-18T10:00:01Z","tool"\n'  # truncated, invalid JSON
        '{"ts":"2026-04-18T10:00:02Z","tool":"Write"}\n',
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="skipping malformed JSON line"):
        events = load_events("post-tool-use")
    assert len(events) == 2
    assert [e["tool"] for e in events] == ["Read", "Write"]


def test_render_table_produces_markdown():
    events = [
        {"ts": "2026-04-18T10:00:00Z", "tool": "Read"},
        {"ts": "2026-04-18T10:00:01Z", "tool": "Write"},
    ]
    table = render_table(events, columns=["ts", "tool"])
    assert "| ts | tool |" in table
    assert "| 2026-04-18T10:00:00Z | Read |" in table


def test_concurrent_appends_no_corruption(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(
            lambda i: append_event("stop", {"i": i}),
            range(50),
        ))
    events = load_events("stop")
    assert len(events) == 50
    assert sorted(e["i"] for e in events) == list(range(50))
