from digest import run_digest


def main() -> None:
    print("Fetching news...")
    digest = run_digest()
    print(f"Top stories: {len(digest['top_stories'])}, categories: {len(digest['categories'])}")

    print("\n--- SUMMARY ---")
    print(digest["summary"])
    print(f"\n--- AUDIO SCRIPT ({len(digest['audio_script'].split())} words) ---")
    print(digest["audio_script"][:500], "...")
    print("\n--- TOP STORIES (LISTEN) ---")
    for i, story in enumerate(digest["top_stories"], start=1):
        print(f"{i}. [{story['source']}] {story['title']}")
        print(f"   Why: {story['why_it_matters']}")
    print("\n--- CATEGORIES (READ) ---")
    for cat in digest["categories"]:
        print(f"\n{cat['name']} ({len(cat['articles'])})")
        for article in cat["articles"][:3]:
            print(f"  - {article['title'][:70]}")
    print("\n--- QUESTIONS ---")
    for i, q in enumerate(digest["questions"]):
        print(f"{i+1}. {q['question']}")


if __name__ == "__main__":
    main()
