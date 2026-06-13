import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser

from digest.config import (
    ENTRIES_PER_SOURCE,
    FETCH_TIMEOUT,
    HABR_PREFIX,
    INTEREST_KEYWORDS,
    MAX_ARTICLES,
    MAX_FETCH_WORKERS,
    MIN_RELEVANT_ARTICLES,
    RSS_SOURCES,
    SNIPPET_MAX_LENGTH,
)
from digest.models import Article

logger = logging.getLogger(__name__)

USER_AGENT = "telegram-digest-bot/1.0 (+https://github.com)"


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


def _fetch_feed(feed_url: str) -> list[dict]:
    try:
        request = Request(feed_url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=FETCH_TIMEOUT) as response:
            raw = response.read()
    except (URLError, socket.timeout, ValueError) as error:
        logger.warning("Failed to fetch %s: %s", feed_url, error)
        return []

    feed = feedparser.parse(raw)
    if feed.bozo:
        logger.warning("Malformed feed %s: %s", feed_url, feed.bozo_exception)

    source = source_label(feed_url)
    items: list[dict] = []
    for entry in feed.entries[:ENTRIES_PER_SOURCE]:
        title = (getattr(entry, "title", "") or "").strip()
        if not title:
            continue
        snippet = clean_snippet(getattr(entry, "summary", ""))
        items.append({
            "title": title,
            "link": (getattr(entry, "link", "") or "").strip(),
            "source": source,
            "snippet": snippet,
            "lang": article_lang(source, title, snippet),
            "_feed_url": feed_url,
        })
    return items


def fetch_news() -> list[Article]:
    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as executor:
        per_feed = executor.map(_fetch_feed, RSS_SOURCES)

    items: list[dict] = []
    seen: set[str] = set()
    for feed_items in per_feed:
        for item in feed_items:
            if item["title"] in seen:
                continue
            seen.add(item["title"])
            items.append(item)

    relevant = [a for a in items if is_relevant(a, a["_feed_url"])]
    chosen = relevant if len(relevant) >= MIN_RELEVANT_ARTICLES else items

    logger.info("Fetched %d articles (%d relevant)", len(items), len(relevant))
    return [Article.from_dict(item) for item in chosen[:MAX_ARTICLES]]
