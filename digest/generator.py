import json
import logging
import os

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from digest.config import GEMINI_MODEL
from digest.models import Article
from digest.prompts import DIGEST_SCHEMA, DOMAIN_PROMPT

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_LOCATION", "us-central1"),
        )
    return _client


def format_articles_for_gemini(articles: list[Article]) -> str:
    blocks = []
    for index, article in enumerate(articles):
        block = [f"[{index}] Lang:{article.lang} [{article.source}] {article.title}"]
        if article.snippet:
            block.append(f"Snippet: {article.snippet}")
        if article.link:
            block.append(f"Link: {article.link}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    reraise=True,
)
def generate_digest(articles: list[Article]) -> dict:
    raw = format_articles_for_gemini(articles)
    response = _get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{DOMAIN_PROMPT}\n\nArticles:\n{raw}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DIGEST_SCHEMA,
        ),
    )
    return json.loads(response.text)
