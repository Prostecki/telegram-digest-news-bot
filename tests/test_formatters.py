from bot.formatters import (
    _split_text,
    digest_filename,
    format_digest_markdown,
    format_telegram_messages,
)
from digest.models import Article, Category, Digest, Question, TopStory


def _digest() -> Digest:
    article = Article(title="Title <x>", link="https://a", source="dev.to", snippet="snip")
    return Digest(
        date="13-06-2026",
        summary="Summary & more",
        top_stories=[
            TopStory(article=article, why_it_matters="why", deep_dive="deep", audio_segment="seg")
        ],
        categories=[Category(name="AI & Agents", articles=[article])],
        questions=[Question(question="Q?", options=["a", "b", "c", "d"], correct=1)],
        audio_script="one two three",
        articles=[article],
    )


def test_digest_filename():
    assert digest_filename("13-06-2026") == "13-06-2026-digest.md"


def test_split_text_short_returns_single():
    assert _split_text("hello", 100) == ["hello"]


def test_split_text_splits_long():
    text = "\n".join(f"line {i}" for i in range(100))
    chunks = _split_text(text, 50)
    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)


def test_telegram_messages_escape_html():
    messages = format_telegram_messages(_digest())
    joined = "\n".join(messages)
    assert "Title &lt;x&gt;" in joined
    assert "Summary &amp; more" in joined


def test_telegram_messages_have_sections():
    messages = format_telegram_messages(_digest())
    joined = "\n".join(messages)
    assert "Tech Digest" in joined
    assert "Top Stories" in joined
    assert "Read by Category" in joined
    assert "Quiz" in joined


def test_telegram_quiz_answer_label():
    messages = format_telegram_messages(_digest())
    joined = "\n".join(messages)
    assert "✅ B" in joined


def test_markdown_contains_sections():
    md = format_digest_markdown(_digest())
    assert "# Tech Digest — 13-06-2026" in md
    assert "**Answer:** B" in md
    assert "Audio Script" in md
