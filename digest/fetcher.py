import re
from html import unescape
from urllib.parse import urlparse

import feedparser

from digest.config import (
    ENTRIES_PER_SOURCE,
    HABR_PREFIX,
    INTEREST_KEYWORDS,
    MAX_ARTICLES,
    MIN_RELEVANT_ARTICLES,
    RSS_SOURCES,
    SNIPPET_MAX_LENGTH,
)


def source_label(feed_url: str) -> str:
    host = urlparse(feed_url).netloc.removeprefix("www.")
    if "habr.com" in host:
        return "Habr"
    if host == "cloudblog.withgoogle.com":
        return "Google Cloud"
    return host


def clean_snippet(text: str, max_len: int = SNIPPET_MAX_LENGTH) -> str:
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def article_lang(source: str, title: str, snippet: str) -> str:
    if source == "Habr":
        return "ru"
    text = f"{title} {snippet}"
    if re.search(r"[а-яА-ЯёЁ]", text):
        return "ru"
    return "en"


def is_relevant(article: dict, feed_url: str) -> bool:
    if feed_url.startswith(HABR_PREFIX):
        return True
    text = f"{article['title']} {article.get('snippet', '')}".lower()
    return any(keyword in text for keyword in INTEREST_KEYWORDS)


def fetch_news() -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    for feed_url in RSS_SOURCES:
        feed = feedparser.parse(feed_url)
        source = source_label(feed_url)

        for entry in feed.entries[:ENTRIES_PER_SOURCE]:
            title = entry.title.strip()
            if not title or title in seen:
                continue

            seen.add(title)
            snippet = clean_snippet(getattr(entry, "summary", ""))
            items.append({
                "title": title,
                "link": getattr(entry, "link", "").strip(),
                "source": source,
                "snippet": snippet,
                "lang": article_lang(source, title, snippet),
                "_feed_url": feed_url,
            })

    relevant = [a for a in items if is_relevant(a, a["_feed_url"])]
    articles = relevant if len(relevant) >= MIN_RELEVANT_ARTICLES else items

    return [
        {k: v for k, v in article.items() if k != "_feed_url"}
        for article in articles[:MAX_ARTICLES]
    ]
