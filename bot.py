import asyncio
import html
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

from digest import run_digest
from tts import synthesize_speech

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TTS_LANGUAGE = "en-US"
DIGESTS_DIR = Path(__file__).parent / "digests"
MAX_MESSAGE_LENGTH = 4096
OPTION_LABELS = "ABCD"

CATEGORY_EMOJI = {
    "AI & Agents": "🤖",
    "Fullstack": "⚛️",
    "Backend & APIs": "🐍",
    "GCP & DevOps": "☁️",
    "Databases": "🗄️",
    "Worth Reading": "📚",
}


def digest_filename(date: str | None = None) -> str:
    date = date or datetime.now().strftime("%d-%m-%Y")
    return f"{date}-digest.md"


def _format_article_markdown(article: dict, index: int) -> str:
    lines = [f"{index}. **[{article['source']}]** {article['title']}"]
    if article.get("snippet"):
        lines.append(f"   {article['snippet']}")
    if article.get("link"):
        lines.append(f"   [{article['link']}]({article['link']})")
    return "\n".join(lines)


def _format_article_telegram(article: dict, index: int) -> str:
    source = html.escape(article["source"])
    title = html.escape(article["title"])
    lines = [f"\n{index}. <b>[{source}]</b>"]

    if article.get("link"):
        url = html.escape(article["link"], quote=True)
        lines.append(f'<a href="{url}">{title}</a>')
    else:
        lines.append(title)

    if article.get("snippet"):
        lines.append(f"<i>{html.escape(article['snippet'])}</i>")

    return "\n".join(lines)


def _format_top_story_telegram(story: dict, rank: int) -> str:
    source = html.escape(story["source"])
    title = html.escape(story["title"])
    lines = [f"\n<b>{rank}. [{source}]</b>"]

    if story.get("link"):
        url = html.escape(story["link"], quote=True)
        lines.append(f'<a href="{url}">{title}</a>')
    else:
        lines.append(title)

    lines.append(f"💡 {html.escape(story['why_it_matters'])}")
    lines.append(f"<i>{html.escape(story['deep_dive'])}</i>")
    return "\n".join(lines)


def _format_top_story_markdown(story: dict, rank: int) -> str:
    lines = [f"### {rank}. [{story['source']}] {story['title']}"]
    if story.get("link"):
        lines.append(f"[Read more]({story['link']})")
    lines.extend([
        "",
        f"**Why it matters:** {story['why_it_matters']}",
        "",
        story["deep_dive"],
        "",
    ])
    if story.get("audio_segment"):
        lines.extend([
            f"**Podcast segment (EN):** {story['audio_segment']}",
            "",
        ])
    return "\n".join(lines)


def format_digest_markdown(digest: dict) -> str:
    date = digest.get("date", datetime.now().strftime("%d-%m-%Y"))
    lines = [
        f"# Tech Digest — {date}",
        "",
        "## Summary",
        "",
        digest["summary"],
        "",
        "## Top Stories — Listen",
        "",
    ]

    for i, story in enumerate(digest.get("top_stories", []), start=1):
        lines.append(_format_top_story_markdown(story, i))

    lines.extend(["## Read by Category", ""])
    for category in digest.get("categories", []):
        lines.append(f"### {category['name']}")
        lines.append("")
        for i, article in enumerate(category["articles"], start=1):
            lines.append(_format_article_markdown(article, i))
            lines.append("")

    lines.extend(["## Quiz", ""])
    for i, q in enumerate(digest["questions"], start=1):
        lines.append(f"### {i}. {q['question']}")
        lines.append("")
        for j, option in enumerate(q["options"]):
            label = OPTION_LABELS[j] if j < len(OPTION_LABELS) else str(j + 1)
            lines.append(f"- **{label})** {option}")
        correct = q["correct"]
        answer = (
            OPTION_LABELS[correct]
            if 0 <= correct < len(OPTION_LABELS)
            else str(correct + 1)
        )
        lines.extend([f"- **Answer:** {answer}", ""])

    word_count = len(digest.get("audio_script", "").split())
    lines.extend([
        f"## Audio Script (~{word_count} words)",
        "",
        digest.get("audio_script", ""),
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


def format_telegram_messages(digest: dict) -> list[str]:
    date = digest.get("date", datetime.now().strftime("%d-%m-%Y"))
    word_count = len(digest.get("audio_script", "").split())

    header = (
        f"📰 <b>Tech Digest</b>\n"
        f"📅 <i>{date}</i>\n"
        f"{'─' * 24}\n\n"
        f"📌 <b>Summary</b>\n"
        f"<blockquote>{html.escape(digest['summary'])}</blockquote>\n\n"
        f"🎧 <b>Listen:</b> Top {len(digest.get('top_stories', []))} podcast (~3-4 min)\n"
        f"📖 <b>Read:</b> {sum(len(c['articles']) for c in digest.get('categories', []))} articles by category"
    )

    top_lines = [
        f"🎧 <b>Top Stories — Listen</b> <i>({word_count} words in audio)</i>\n"
        f"{'─' * 24}"
    ]
    for i, story in enumerate(digest.get("top_stories", []), start=1):
        top_lines.append(_format_top_story_telegram(story, i))

    read_lines = [f"📖 <b>Read by Category</b>\n{'─' * 24}"]
    for category in digest.get("categories", []):
        emoji = CATEGORY_EMOJI.get(category["name"], "📁")
        read_lines.append(
            f"\n{emoji} <b>{html.escape(category['name'])}</b> "
            f"<i>({len(category['articles'])})</i>"
        )
        for i, article in enumerate(category["articles"], start=1):
            read_lines.append(_format_article_telegram(article, i))

    quiz_lines = [f"📝 <b>Quiz</b> <i>(top stories)</i>\n{'─' * 24}"]
    for i, q in enumerate(digest["questions"], start=1):
        block = [f"\n<b>{i}. {html.escape(q['question'])}</b>"]
        for j, option in enumerate(q["options"]):
            label = OPTION_LABELS[j] if j < len(OPTION_LABELS) else str(j + 1)
            block.append(f"   {label}) {html.escape(option)}")
        correct = q["correct"]
        answer_label = (
            OPTION_LABELS[correct]
            if 0 <= correct < len(OPTION_LABELS)
            else str(correct + 1)
        )
        block.append(f"   <tg-spoiler>✅ {answer_label}</tg-spoiler>")
        quiz_lines.append("\n".join(block))

    messages = [header]
    messages.extend(_split_text("\n".join(top_lines), MAX_MESSAGE_LENGTH))
    messages.extend(_split_text("\n".join(read_lines), MAX_MESSAGE_LENGTH))
    messages.extend(_split_text("\n".join(quiz_lines), MAX_MESSAGE_LENGTH))
    return messages


def save_digest_file(digest: dict) -> Path:
    DIGESTS_DIR.mkdir(exist_ok=True)
    content = format_digest_markdown(digest)
    path = DIGESTS_DIR / digest_filename(digest.get("date"))
    path.write_text(content, encoding="utf-8")
    return path


async def send_digest() -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")

    print("Generating digest...")
    digest = await asyncio.to_thread(run_digest)
    messages = format_telegram_messages(digest)
    markdown = format_digest_markdown(digest)
    filename = digest_filename(digest.get("date"))
    file_path = save_digest_file(digest)

    print("Synthesizing audio...")
    audio_text = digest.get("audio_script") or digest["summary"]
    audio_bytes = await asyncio.to_thread(
        synthesize_speech, audio_text, TTS_LANGUAGE
    )

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with bot:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=(
                f"🗞 <b>Digest ready</b>\n"
                f"📅 {digest.get('date')}\n"
                f"🎧 Top stories podcast + 📖 categorized reading\n"
                f"📎 <code>{filename}</code>"
            ),
            parse_mode=ParseMode.HTML,
        )

        await bot.send_audio(
            chat_id=TELEGRAM_CHAT_ID,
            audio=BytesIO(audio_bytes),
            filename=f"{digest.get('date')}-top5-podcast.mp3",
            title=f"Top Tech News — {digest.get('date')}",
            caption=f"🎧 Top {len(digest.get('top_stories', []))} stories (~3-4 min)",
        )

        for message in messages:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.HTML,
            )

        await bot.send_document(
            chat_id=TELEGRAM_CHAT_ID,
            document=BytesIO(markdown.encode("utf-8")),
            filename=filename,
            caption=f"📄 {filename}",
        )

    print(
        f"Sent podcast + {len(messages)} message(s) + file to chat {TELEGRAM_CHAT_ID}\n"
        f"Saved locally: {file_path}"
    )


if __name__ == "__main__":
    asyncio.run(send_digest())
