import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from digest.config import GEMINI_MODEL
from digest.prompts import DIGEST_SCHEMA, DOMAIN_PROMPT

load_dotenv()

_client = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GCP_LOCATION", "us-central1"),
)


def format_articles_for_gemini(articles: list[dict]) -> str:
    blocks = []
    for index, article in enumerate(articles):
        lang = article.get("lang", "en")
        block = [f"[{index}] Lang:{lang} [{article['source']}] {article['title']}"]
        if article.get("snippet"):
            block.append(f"Snippet: {article['snippet']}")
        if article.get("link"):
            block.append(f"Link: {article['link']}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def generate_digest(articles: list[dict]) -> dict:
    raw = format_articles_for_gemini(articles)
    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"""{DOMAIN_PROMPT}

Articles:
{raw}""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DIGEST_SCHEMA,
        ),
    )
    return json.loads(response.text)
