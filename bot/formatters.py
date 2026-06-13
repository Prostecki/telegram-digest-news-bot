import html
from datetime import datetime

from bot.config import CATEGORY_EMOJI, MAX_MESSAGE_LENGTH, OPTION_LABELS
from digest.models import Article, Category, Digest, Question, TopStory


def digest_filename(date: str | None = None) -> str:
    date = date or datetime.now().strftime("%d-%m-%Y")
    return f"{date}-digest.md"


def _answer_label(correct: int) -> str:
    if 0 <= correct < len(OPTION_LABELS):
        return OPTION_LABELS[correct]
    return str(correct + 1)


def _option_label(index: int) -> str:
    if index < len(OPTION_LABELS):
        return OPTION_LABELS[index]
    return str(index + 1)


def _format_article_markdown(article: Article, index: int) -> str:
    lines = [f"{index}. **[{article.source}]** {article.title}"]
    if article.snippet:
        lines.append(f"   {article.snippet}")
    if article.link:
        lines.append(f"   [{article.link}]({article.link})")
    return "\n".join(lines)


def _format_article_telegram(article: Article, index: int) -> str:
    source = html.escape(article.source)
    title = html.escape(article.title)
    lines = [f"\n{index}. <b>[{source}]</b>"]

    if article.link:
        url = html.escape(article.link, quote=True)
        lines.append(f'<a href="{url}">{title}</a>')
    else:
        lines.append(title)

    if article.snippet:
        lines.append(f"<i>{html.escape(article.snippet)}</i>")

    return "\n".join(lines)


def _format_top_story_telegram(story: TopStory, rank: int) -> str:
    source = html.escape(story.article.source)
    title = html.escape(story.article.title)
    lines = [f"\n<b>{rank}. [{source}]</b>"]

    if story.article.link:
        url = html.escape(story.article.link, quote=True)
        lines.append(f'<a href="{url}">{title}</a>')
    else:
        lines.append(title)

    lines.append(f"💡 {html.escape(story.why_it_matters)}")
    lines.append(f"<i>{html.escape(story.deep_dive)}</i>")
    return "\n".join(lines)


def _format_top_story_markdown(story: TopStory, rank: int) -> str:
    lines = [f"### {rank}. [{story.article.source}] {story.article.title}"]
    if story.article.link:
        lines.append(f"[Read more]({story.article.link})")
    lines.extend([
        "",
        f"**Why it matters:** {story.why_it_matters}",
        "",
        story.deep_dive,
        "",
    ])
    if story.audio_segment:
        lines.extend([f"**Podcast segment (EN):** {story.audio_segment}", ""])
    return "\n".join(lines)


def _format_question_markdown(question: Question, index: int) -> list[str]:
    lines = [f"### {index}. {question.question}", ""]
    for j, option in enumerate(question.options):
        lines.append(f"- **{_option_label(j)})** {option}")
    lines.extend([f"- **Answer:** {_answer_label(question.correct)}", ""])
    return lines


def format_digest_markdown(digest: Digest) -> str:
    lines = [
        f"# Tech Digest — {digest.date}",
        "",
        "## Summary",
        "",
        digest.summary,
        "",
        "## Top Stories — Listen",
        "",
    ]

    for i, story in enumerate(digest.top_stories, start=1):
        lines.append(_format_top_story_markdown(story, i))

    lines.extend(["## Read by Category", ""])
    for category in digest.categories:
        lines.append(f"### {category.name}")
        lines.append("")
        for i, article in enumerate(category.articles, start=1):
            lines.append(_format_article_markdown(article, i))
            lines.append("")

    lines.extend(["## Quiz", ""])
    for i, question in enumerate(digest.questions, start=1):
        lines.extend(_format_question_markdown(question, i))

    word_count = len(digest.audio_script.split())
    lines.extend([
        f"## Audio Script (~{word_count} words)",
        "",
        digest.audio_script,
    ])
    return "\n".join(lines)


def _split_text(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > max_len and current:
            chunks.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def _category_articles_count(categories: list[Category]) -> int:
    return sum(len(c.articles) for c in categories)


def format_telegram_messages(digest: Digest) -> list[str]:
    word_count = len(digest.audio_script.split())

    header = (
        f"📰 <b>Tech Digest</b>\n"
        f"📅 <i>{digest.date}</i>\n"
        f"{'─' * 24}\n\n"
        f"📌 <b>Summary</b>\n"
        f"<blockquote>{html.escape(digest.summary)}</blockquote>\n\n"
        f"🎧 <b>Listen:</b> Top {len(digest.top_stories)} podcast (~3-4 min)\n"
        f"📖 <b>Read:</b> {_category_articles_count(digest.categories)} articles by category"
    )

    top_lines = [
        f"🎧 <b>Top Stories — Listen</b> <i>({word_count} words in audio)</i>\n"
        f"{'─' * 24}"
    ]
    for i, story in enumerate(digest.top_stories, start=1):
        top_lines.append(_format_top_story_telegram(story, i))

    read_lines = [f"📖 <b>Read by Category</b>\n{'─' * 24}"]
    for category in digest.categories:
        emoji = CATEGORY_EMOJI.get(category.name, "📁")
        read_lines.append(
            f"\n{emoji} <b>{html.escape(category.name)}</b> "
            f"<i>({len(category.articles)})</i>"
        )
        for i, article in enumerate(category.articles, start=1):
            read_lines.append(_format_article_telegram(article, i))

    quiz_lines = [f"📝 <b>Quiz</b> <i>(top stories)</i>\n{'─' * 24}"]
    for i, question in enumerate(digest.questions, start=1):
        block = [f"\n<b>{i}. {html.escape(question.question)}</b>"]
        for j, option in enumerate(question.options):
            block.append(f"   {_option_label(j)}) {html.escape(option)}")
        block.append(f"   <tg-spoiler>✅ {_answer_label(question.correct)}</tg-spoiler>")
        quiz_lines.append("\n".join(block))

    messages = [header]
    messages.extend(_split_text("\n".join(top_lines), MAX_MESSAGE_LENGTH))
    messages.extend(_split_text("\n".join(read_lines), MAX_MESSAGE_LENGTH))
    messages.extend(_split_text("\n".join(quiz_lines), MAX_MESSAGE_LENGTH))
    return messages
