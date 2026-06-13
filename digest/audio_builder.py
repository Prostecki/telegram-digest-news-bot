from digest.models import TopStory


def build_podcast_script(top_stories: list[TopStory]) -> str:
    """Assemble TTS text from explicit per-story English segments."""
    if not top_stories:
        return "No top stories today. Check Telegram for the full reading list."

    intro = (
        f"Welcome to your tech digest. "
        f"Here are the top {len(top_stories)} stories for today."
    )
    parts = [intro]

    for i, story in enumerate(top_stories, start=1):
        segment = story.audio_segment.strip()
        if segment:
            parts.append(segment)
            continue
        parts.append(
            f"Story {i}, from {story.article.source}: "
            f"{story.article.title}. {story.why_it_matters}"
        )

    parts.append(
        "That's your listen digest. "
        "Open Telegram for links, categories, and the rest of today's reading list."
    )
    return " ".join(parts)
