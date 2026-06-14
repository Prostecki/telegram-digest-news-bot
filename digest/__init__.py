import logging
from datetime import datetime

from digest.config import MAX_GEMINI_ATTEMPTS, TOP_STORIES_COUNT
from digest.enricher import enrich_digest
from digest.fetcher import fetch_news
from digest.generator import generate_digest
from digest.models import Article, Category, Digest, Question, TopStory
from digest.validator import DigestValidationError, validate_raw_digest

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

    last_error: DigestValidationError | None = None
    raw: dict | None = None
    for attempt in range(1, MAX_GEMINI_ATTEMPTS + 1):
        raw = generate_digest(articles)
        try:
            validate_raw_digest(raw, len(articles))
            break
        except DigestValidationError as exc:
            last_error = exc
            logger.warning(
                "Invalid Gemini digest (attempt %d/%d): %s",
                attempt,
                MAX_GEMINI_ATTEMPTS,
                exc,
            )
    else:
        raise RuntimeError(
            f"Gemini returned invalid digest after {MAX_GEMINI_ATTEMPTS} attempts: "
            f"{last_error}"
        )

    date = datetime.now().strftime("%d-%m-%Y")
    digest = enrich_digest(raw, articles, date)
    if len(digest.top_stories) != TOP_STORIES_COUNT:
        raise RuntimeError(
            f"Digest has {len(digest.top_stories)} top stories, "
            f"expected {TOP_STORIES_COUNT}"
        )
    return digest
