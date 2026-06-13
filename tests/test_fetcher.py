from digest.fetcher import article_lang, clean_snippet, is_relevant, source_label


def test_source_label_habr():
    assert source_label("https://habr.com/ru/rss/hub/python/") == "Habr"


def test_source_label_google_cloud():
    assert source_label("https://cloudblog.withgoogle.com/rss/") == "Google Cloud"


def test_source_label_strips_www():
    assert source_label("https://www.dev.to/feed") == "dev.to"


def test_clean_snippet_strips_html_and_collapses_space():
    assert clean_snippet("<p>Hello   <b>world</b></p>") == "Hello world"


def test_clean_snippet_truncates():
    text = "word " * 100
    result = clean_snippet(text, max_len=20)
    assert len(result) <= 23
    assert result.endswith("...")


def test_clean_snippet_handles_empty():
    assert clean_snippet("") == ""
    assert clean_snippet(None) == ""


def test_article_lang_habr_is_ru():
    assert article_lang("Habr", "Some english title", "english") == "ru"


def test_article_lang_detects_cyrillic():
    assert article_lang("dev.to", "Привет мир", "") == "ru"


def test_article_lang_defaults_english():
    assert article_lang("dev.to", "Hello world", "a snippet") == "en"


def test_is_relevant_habr_always_true():
    article = {"title": "anything", "snippet": ""}
    assert is_relevant(article, "https://habr.com/ru/rss/hub/python/") is True


def test_is_relevant_matches_keyword():
    article = {"title": "New React 20 release", "snippet": ""}
    assert is_relevant(article, "https://dev.to/feed") is True


def test_is_relevant_no_keyword():
    article = {"title": "Gardening tips for spring", "snippet": "flowers"}
    assert is_relevant(article, "https://dev.to/feed") is False
