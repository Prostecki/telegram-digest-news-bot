import pytest

from digest.config import TOP_STORIES_COUNT
from digest.validator import DigestValidationError, validate_raw_digest


def _valid_raw() -> dict:
    return {
        "summary": "Overview",
        "top_stories": [
            {
                "article_index": 0,
                "why_it_matters": "why0",
                "deep_dive": "deep0",
                "audio_segment": "seg0",
            },
            {
                "article_index": 1,
                "why_it_matters": "why1",
                "deep_dive": "deep1",
                "audio_segment": "seg1",
            },
            {
                "article_index": 2,
                "why_it_matters": "why2",
                "deep_dive": "deep2",
                "audio_segment": "seg2",
            },
        ],
        "categories": [
            {"name": "AI & Agents", "article_indices": [0, 1]},
            {"name": "Fullstack", "article_indices": [2]},
        ],
        "questions": [
            {"question": "Q1?", "options": ["a", "b", "c", "d"], "correct": 0},
            {"question": "Q2?", "options": ["a", "b", "c", "d"], "correct": 1},
            {"question": "Q3?", "options": ["a", "b", "c", "d"], "correct": 2},
        ],
    }


def test_validate_raw_digest_accepts_valid_payload():
    validate_raw_digest(_valid_raw(), article_count=3)


def test_validate_raw_digest_rejects_wrong_top_story_count():
    raw = _valid_raw()
    raw["top_stories"] = raw["top_stories"][:2]

    with pytest.raises(DigestValidationError, match="expected 3 top_stories"):
        validate_raw_digest(raw, article_count=3)


def test_validate_raw_digest_rejects_invalid_index():
    raw = _valid_raw()
    raw["top_stories"][0]["article_index"] = 99

    with pytest.raises(DigestValidationError, match="invalid article_index"):
        validate_raw_digest(raw, article_count=3)


def test_validate_raw_digest_rejects_missing_top_story_in_categories():
    raw = _valid_raw()
    raw["categories"] = [{"name": "AI & Agents", "article_indices": [0]}]

    with pytest.raises(DigestValidationError, match="missing from categories"):
        validate_raw_digest(raw, article_count=3)


def test_validate_raw_digest_rejects_bad_quiz():
    raw = _valid_raw()
    raw["questions"] = raw["questions"][:2]

    with pytest.raises(DigestValidationError, match=f"expected {TOP_STORIES_COUNT} questions"):
        validate_raw_digest(raw, article_count=3)
