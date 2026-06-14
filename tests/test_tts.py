import subprocess
from pathlib import Path

from tts import _merge_mp3, _pick_voice, _split_for_tts


def test_merge_mp3_single_part():
    data = b"fake-mp3"
    assert _merge_mp3([data]) == data


def test_merge_mp3_uses_ffmpeg(monkeypatch):
    monkeypatch.setattr("tts.shutil.which", lambda _: "/usr/bin/ffmpeg")

    def fake_run(cmd, capture_output=True, check=False):
        Path(cmd[-1]).write_bytes(b"merged-mp3")
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr("tts.subprocess.run", fake_run)

    result = _merge_mp3([b"part-a", b"part-b"])

    assert result == b"merged-mp3"


def test_short_text_single_chunk():
    assert _split_for_tts("Hello world.") == ["Hello world."]


def test_long_text_splits_under_limit():
    text = ("This is a sentence. " * 600).strip()
    chunks = _split_for_tts(text, max_bytes=500)
    assert len(chunks) > 1
    assert all(len(c.encode("utf-8")) <= 500 for c in chunks)


def test_split_preserves_all_words():
    text = "Alpha. Beta. Gamma. Delta. Epsilon."
    chunks = _split_for_tts(text, max_bytes=15)
    rejoined = " ".join(chunks)
    for word in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
        assert word in rejoined


def test_pick_voice_default(monkeypatch):
    monkeypatch.delenv("TTS_VOICE", raising=False)
    assert _pick_voice("en-US") == "en-US-Neural2-J"


def test_pick_voice_override(monkeypatch):
    monkeypatch.setenv("TTS_VOICE", "en-US-Custom")
    assert _pick_voice("en-US") == "en-US-Custom"
