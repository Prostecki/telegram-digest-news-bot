from digest.config import CATEGORIES, TOP_STORIES_COUNT


class DigestValidationError(ValueError):
    """Gemini JSON does not match the expected digest shape."""


def validate_raw_digest(raw: dict, article_count: int) -> None:
    errors: list[str] = []

    if not str(raw.get("summary", "")).strip():
        errors.append("summary is empty")

    top_stories = raw.get("top_stories", [])
    if len(top_stories) != TOP_STORIES_COUNT:
        errors.append(f"expected {TOP_STORIES_COUNT} top_stories, got {len(top_stories)}")

    top_indices: set[int] = set()
    for index, story in enumerate(top_stories):
        article_index = story.get("article_index")
        if not isinstance(article_index, int) or not (0 <= article_index < article_count):
            errors.append(f"top_stories[{index}] has invalid article_index {article_index!r}")
        else:
            top_indices.add(article_index)

        for field in ("why_it_matters", "deep_dive", "audio_segment"):
            if not str(story.get(field, "")).strip():
                errors.append(f"top_stories[{index}] missing {field}")

    if len(top_indices) != len(top_stories):
        errors.append("top_stories contain duplicate article_index values")

    categories = raw.get("categories", [])
    if not categories:
        errors.append("categories is empty")

    seen_names: set[str] = set()
    assigned_indices: set[int] = set()
    for index, category in enumerate(categories):
        name = category.get("name")
        if name not in CATEGORIES:
            errors.append(f"categories[{index}] has unknown name {name!r}")
        if name in seen_names:
            errors.append(f"duplicate category {name!r}")
        seen_names.add(name)

        article_indices = category.get("article_indices", [])
        if not article_indices:
            errors.append(f"categories[{index}] has no article_indices")

        for article_index in article_indices:
            if not isinstance(article_index, int) or not (0 <= article_index < article_count):
                errors.append(
                    f"categories[{index}] has invalid article_index {article_index!r}"
                )
            assigned_indices.add(article_index)

    missing_top = top_indices - assigned_indices
    if missing_top:
        errors.append(f"top story indices missing from categories: {sorted(missing_top)}")

    questions = raw.get("questions", [])
    if len(questions) != TOP_STORIES_COUNT:
        errors.append(f"expected {TOP_STORIES_COUNT} questions, got {len(questions)}")

    for index, question in enumerate(questions):
        if not str(question.get("question", "")).strip():
            errors.append(f"questions[{index}] missing question text")

        options = question.get("options", [])
        if len(options) != 4:
            errors.append(f"questions[{index}] must have 4 options, got {len(options)}")

        correct = question.get("correct")
        if not isinstance(correct, int) or not (0 <= correct < len(options)):
            errors.append(f"questions[{index}] has invalid correct index {correct!r}")

    if errors:
        raise DigestValidationError("; ".join(errors))
