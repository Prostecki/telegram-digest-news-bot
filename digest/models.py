from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    link: str
    source: str
    snippet: str = ""
    lang: str = "en"

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        return cls(
            title=data["title"],
            link=data.get("link", ""),
            source=data["source"],
            snippet=data.get("snippet", ""),
            lang=data.get("lang", "en"),
        )


@dataclass
class TopStory:
    article: Article
    why_it_matters: str
    deep_dive: str
    audio_segment: str = ""


@dataclass
class Category:
    name: str
    articles: list[Article] = field(default_factory=list)


@dataclass
class Question:
    question: str
    options: list[str]
    correct: int


@dataclass
class Digest:
    date: str
    summary: str
    top_stories: list[TopStory] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    audio_script: str = ""
    articles: list[Article] = field(default_factory=list)
