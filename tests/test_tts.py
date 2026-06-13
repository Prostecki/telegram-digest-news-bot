from tts import _pick_voice, _split_for_tts


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
