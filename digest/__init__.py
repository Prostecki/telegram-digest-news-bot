import logging
from datetime import datetime

from digest.enricher import enrich_digest
from digest.fetcher import fetch_news
from digest.generator import generate_digest
from digest.models import Article, Category, Digest, Question, TopStory

__all__ = [
    "run_digest",
    "fetch_news",
    "Digest",
    "Article",
    "Category",
    "Question",
    "TopStory",
]

logger = logging.getLogger(__name__)


def run_digest() -> Digest:
    articles = fetch_news()
    if not articles:
        raise RuntimeError("No articles fetched from any RSS source")
    raw = generate_digest(articles)
    date = datetime.now().strftime("%d-%m-%Y")
    return enrich_digest(raw, articles, date)
