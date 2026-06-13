import logging

from digest import run_digest

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    print("Fetching news...")
    digest = run_digest()
    print(f"Top stories: {len(digest.top_stories)}, categories: {len(digest.categories)}")

    print("\n--- SUMMARY ---")
    print(digest.summary)
    print(f"\n--- AUDIO SCRIPT ({len(digest.audio_script.split())} words) ---")
    print(digest.audio_script[:500], "...")

    print("\n--- TOP STORIES (LISTEN) ---")
    for i, story in enumerate(digest.top_stories, start=1):
        print(f"{i}. [{story.article.source}] {story.article.title}")
        print(f"   Why: {story.why_it_matters}")

    print("\n--- CATEGORIES (READ) ---")
    for category in digest.categories:
        print(f"\n{category.name} ({len(category.articles)})")
        for article in category.articles[:3]:
            print(f"  - {article.title[:70]}")

    print("\n--- QUESTIONS ---")
    for i, question in enumerate(digest.questions, start=1):
        print(f"{i}. {question.question}")


if __name__ == "__main__":
    main()
