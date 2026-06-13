from digest.config import CATEGORIES, TOP_STORIES_COUNT

WORDS_PER_AUDIO_SEGMENT = 120

DIGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "2-3 sentence executive overview in English",
        },
        "top_stories": {
            "type": "array",
            "description": f"Exactly {TOP_STORIES_COUNT} most important stories for audio",
            "items": {
                "type": "object",
                "properties": {
                    "article_index": {"type": "integer"},
                    "why_it_matters": {
                        "type": "string",
                        "description": "1-2 sentences in the article's language (ru/en)",
                    },
                    "deep_dive": {
                        "type": "string",
                        "description": "4-6 sentences in the article's language (ru/en)",
                    },
                    "audio_segment": {
                        "type": "string",
                        "description": (
                            f"English podcast segment, ~{WORDS_PER_AUDIO_SEGMENT} words. "
                            "Must start with 'Story N from SOURCE: TITLE.' then explain "
                            "what happened, who is involved, and why a fullstack engineer should care."
                        ),
                    },
                },
                "required": [
                    "article_index",
                    "why_it_matters",
                    "deep_dive",
                    "audio_segment",
                ],
            },
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "article_indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": ["name", "article_indices"],
            },
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "correct": {"type": "integer"},
                },
                "required": ["question", "options", "correct"],
            },
        },
    },
    "required": ["summary", "top_stories", "categories", "questions"],
}

DOMAIN_PROMPT = f"""You are a tech news analyst for Mark Taratynov — GCP ACE certified fullstack engineer in Stockholm.

His stack: React, Next.js, TypeScript, Python, FastAPI, Node.js, Gemini, Google ADK, MCP, GCP, Terraform, Firestore, BigQuery, PostgreSQL, Supabase.

Articles are numbered [0], [1], ... Each has Lang, source, title, snippet, and link.

Your job — split content into LISTEN mode (top {TOP_STORIES_COUNT}) and READ mode (everything else categorized).

## Top {TOP_STORIES_COUNT} — LISTEN mode (audio podcast)
Pick exactly {TOP_STORIES_COUNT} stories with the biggest global/industry impact relevant to a senior fullstack engineer.
Prioritize: major product launches (Google, OpenAI, etc.), paradigm shifts (agents, MCP, new frameworks), significant GCP/AI moves.
NOT for audio: minor tutorials, personal blog posts, niche Habr how-tos unless industry-shaping.

For each top story provide:
- article_index
- why_it_matters: 1-2 sentences IN THE ARTICLE'S LANGUAGE (ru for Habr, en for others) — for Telegram READ
- deep_dive: 4-6 sentences IN THE ARTICLE'S LANGUAGE — for Telegram READ
- audio_segment: ~{WORDS_PER_AUDIO_SEGMENT} words IN ENGLISH ONLY. This text is read aloud.
  Format: "Story 1 from SOURCE: exact article title. Then explain what happened in plain English,
  who released it or who is affected, and why Mark (fullstack + GCP + AI) should care."
  Be specific — mention product names, technologies, numbers if in snippet. No vague phrases like
  "interesting development" or "worth watching".

## Categories — READ mode
Assign EVERY article index to exactly one category. Use only these names:
{", ".join(CATEGORIES)}

Top {TOP_STORIES_COUNT} articles should ALSO appear in their category.

## Quiz
Exactly {TOP_STORIES_COUNT} questions about the top stories only. 4 options each (A-D). correct = 0-based index.
Use the same language as each story (Russian for Habr, English for others).

## General
- LANGUAGE RULE: why_it_matters and deep_dive MUST match article Lang. audio_segment is ALWAYS English.
- summary: 2-3 sentence executive overview in English
- Filter out politics, crime, crypto scams, unrelated fluff"""
