from digest.audio_builder import build_podcast_script
from digest.models import Article, TopStory


def _story(segment: str = "", why: str = "") -> TopStory:
    return TopStory(
        article=Article(title="T", link="", source="dev.to", snippet=""),
        why_it_matters=why,
        deep_dive="",
        audio_segment=segment,
    )


def test_empty_returns_fallback():
    result = build_podcast_script([])
    assert "No top stories" in result


def test_uses_audio_segment_when_present():
    script = build_podcast_script([_story(segment="Custom segment text.")])
    assert "Custom segment text." in script
    assert script.startswith("Welcome to your tech digest.")


def test_falls_back_to_title_when_no_segment():
    script = build_podcast_script([_story(why="It matters a lot.")])
    assert "from dev.to" in script
    assert "It matters a lot." in script


def test_includes_outro():
    script = build_podcast_script([_story(segment="x")])
    assert "That's your listen digest." in script
