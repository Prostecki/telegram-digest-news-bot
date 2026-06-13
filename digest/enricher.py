from digest.audio_builder import build_podcast_script


def _resolve_article(articles: list[dict], index: int) -> dict | None:
    if 0 <= index < len(articles):
        return articles[index]
    return None


def enrich_digest(digest: dict, articles: list[dict]) -> dict:
    enriched_top = []
    for story in digest.get("top_stories", []):
        article = _resolve_article(articles, story["article_index"])
        if article:
            enriched_top.append({**article, **story})
    digest["top_stories"] = enriched_top

    enriched_categories = []
    for category in digest.get("categories", []):
        cat_articles = []
        seen_titles: set[str] = set()
        for index in category.get("article_indices", []):
            article = _resolve_article(articles, index)
            if article and article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                cat_articles.append(article)
        if cat_articles:
            enriched_categories.append({
                "name": category["name"],
                "articles": cat_articles,
            })

    digest["categories"] = enriched_categories
    digest["articles"] = articles
    digest["audio_script"] = build_podcast_script(digest["top_stories"])
    return digest
