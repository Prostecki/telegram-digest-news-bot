from digest.enricher import enrich_digest
from digest.models import Article


def _articles() -> list[Article]:
    return [
        Article(title="A0", link="l0", source="dev.to", snippet="s0", lang="en"),
        Article(title="A1", link="l1", source="Habr", snippet="s1", lang="ru"),
        Article(title="A2", link="l2", source="dev.to", snippet="s2", lang="en"),
    ]


def _raw() -> dict:
    return {
        "summary": "Overview",
        "top_stories": [
            {
                "article_index": 0,
                "why_it_matters": "why0",
                "deep_dive": "deep0",
                "audio_segment": "seg0",
            }
        ],
        "categories": [
            {"name": "AI & Agents", "article_indices": [0, 2]},
            {"name": "Backend & APIs", "article_indices": [99]},
        ],
        "questions": [
            {"question": "Q1?", "options": ["a", "b", "c", "d"], "correct": 2}
        ],
    }


def test_enrich_maps_top_story_to_article():
    digest = enrich_digest(_raw(), _articles(), "13-06-2026")
    assert len(digest.top_stories) == 1
    story = digest.top_stories[0]
    assert story.article.title == "A0"
    assert story.why_it_matters == "why0"
    assert story.audio_segment == "seg0"


def test_enrich_skips_out_of_range_top_story():
    raw = _raw()
    raw["top_stories"][0]["article_index"] = 99
    digest = enrich_digest(raw, _articles(), "13-06-2026")
    assert digest.top_stories == []


def test_enrich_builds_categories_and_drops_empty():
    digest = enrich_digest(_raw(), _articles(), "13-06-2026")
    assert len(digest.categories) == 1
    assert digest.categories[0].name == "AI & Agents"
    assert [a.title for a in digest.categories[0].articles] == ["A0", "A2"]


def test_enrich_dedupes_category_articles():
    raw = _raw()
    raw["categories"][0]["article_indices"] = [0, 0, 2]
    digest = enrich_digest(raw, _articles(), "13-06-2026")
    assert len(digest.categories[0].articles) == 2


def test_enrich_questions_and_audio_script():
    digest = enrich_digest(_raw(), _articles(), "13-06-2026")
    assert digest.questions[0].correct == 2
    assert "seg0" in digest.audio_script
    assert digest.date == "13-06-2026"
