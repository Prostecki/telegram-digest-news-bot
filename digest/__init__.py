from datetime import datetime

from digest.enricher import enrich_digest
from digest.fetcher import fetch_news
from digest.generator import generate_digest

__all__ = ["fetch_news", "run_digest"]


def run_digest() -> dict:
    articles = fetch_news()
    digest = generate_digest(articles)
    digest = enrich_digest(digest, articles)
    digest["date"] = datetime.now().strftime("%d-%m-%Y")
    return digest
