from digest.audio_builder import build_podcast_script
from digest.models import Article, Category, Digest, Question, TopStory


def _resolve_article(articles: list[Article], index: int) -> Article | None:
    if 0 <= index < len(articles):
        return articles[index]
    return None


def enrich_digest(raw: dict, articles: list[Article], date: str) -> Digest:
    top_stories: list[TopStory] = []
    for story in raw.get("top_stories", []):
        article = _resolve_article(articles, story.get("article_index", -1))
        if article is None:
            continue
        top_stories.append(TopStory(
            article=article,
            why_it_matters=story.get("why_it_matters", ""),
            deep_dive=story.get("deep_dive", ""),
            audio_segment=story.get("audio_segment", ""),
        ))

    categories: list[Category] = []
    for category in raw.get("categories", []):
        seen_titles: set[str] = set()
        cat_articles: list[Article] = []
        for index in category.get("article_indices", []):
            article = _resolve_article(articles, index)
            if article and article.title not in seen_titles:
                seen_titles.add(article.title)
                cat_articles.append(article)
        if cat_articles:
            categories.append(Category(name=category["name"], articles=cat_articles))

    questions = [
        Question(
            question=q["question"],
            options=q.get("options", []),
            correct=q.get("correct", 0),
        )
        for q in raw.get("questions", [])
    ]

    return Digest(
        date=date,
        summary=raw.get("summary", ""),
        top_stories=top_stories,
        categories=categories,
        questions=questions,
        audio_script=build_podcast_script(top_stories),
        articles=articles,
    )
