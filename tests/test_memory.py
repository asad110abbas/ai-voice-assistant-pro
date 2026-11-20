import json
import os
import tempfile
import pytest
from src.brain.memory import new_session_dir, save_transcript, load_transcript


def test_new_session_dir_creates_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session_dir = new_session_dir()
    assert os.path.exists(session_dir)
    assert "session_" in session_dir


def test_save_transcript_writes_valid_json(tmp_path):
    session_dir = str(tmp_path)
    history = [{"role": "user", "content": "Hello"}]
    metadata = {
        "language": "en",
        "escalated": False,
        "start_time": "2026-01-01T00:00:00",
        "end_time": "2026-01-01T00:01:00",
        "duration": 60,
    }
    save_transcript(history, metadata, session_dir)
    transcript_path = os.path.join(session_dir, "transcript.json")
    assert os.path.exists(transcript_path)
    with open(transcript_path) as f:
        data = json.load(f)
    assert data["history"] == history
    assert data["language"] == "en"
    assert data["escalated"] is False


def test_load_transcript_reads_back_correctly(tmp_path):
    session_dir = str(tmp_path)
    history = [{"role": "user", "content": "Test"}]
    metadata = {"language": "ur", "escalated": True, "start_time": "", "end_time": "", "duration": 0}
    save_transcript(history, metadata, session_dir)
    result = load_transcript(session_dir)
    assert result["history"] == history
    assert result["language"] == "ur"
    assert result["escalated"] is True


def test_load_transcript_returns_empty_dict_if_missing(tmp_path):
    result = load_transcript(str(tmp_path))
    assert result == {}
