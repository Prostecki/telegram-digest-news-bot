RSS_SOURCES = [
    "https://daily.dev/rss.xml",
    "https://habr.com/ru/rss/hub/python/",
    "https://habr.com/ru/rss/hub/javascript/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://habr.com/ru/rss/hub/devops/",
    "https://habr.com/ru/rss/hub/nosql/",
    "https://dev.to/feed",
    "https://dev.to/feed/tag/python",
    "https://dev.to/feed/tag/typescript",
    "https://dev.to/feed/tag/nextjs",
    "https://dev.to/feed/tag/react",
    "https://dev.to/feed/tag/gcp",
    "https://plainenglish.io/feed",
    "https://javascriptweekly.com/rss",
    "https://3thinkrs.com/feed",
    "https://developers.googleblog.com/feeds/posts/default",
    "https://cloudblog.withgoogle.com/rss/",
    "https://blog.google/technology/developers/rss/",
]

INTEREST_KEYWORDS = [
    "react", "next.js", "nextjs", "javascript", "typescript", "tailwind", "vite",
    "framer motion", "frontend", "css",
    "node.js", "nodejs", "express", "hono", "python", "fastapi", "backend",
    "rest api", "api", "websocket",
    "gemini", "google adk", "adk", "mcp", "llm", "ai agent", "agent", "multi-agent",
    "voice ai", "gemini live", "coding agent", "figma", "design token", "cline",
    "copilot", "cursor",
    "gcp", "google cloud", "cloud run", "firebase", "firestore", "bigquery",
    "terraform", "docker", "ci/cd", "iam", "cloud engineer",
    "sql", "postgresql", "postgres", "supabase", "firecms",
    "saas", "b2b", "medtech", "fullstack",
    "разработ", "программ", "typescript", "react", "next", "база данных",
    "нейросет", "искусственн", "машинн", "облак", "terraform", "docker",
    "firebase", "backend", "frontend", "fullstack", "devops",
]

ENTRIES_PER_SOURCE = 1
MAX_ARTICLES = 10
SNIPPET_MAX_LENGTH = 220
TOP_STORIES_COUNT = 3
MIN_RELEVANT_ARTICLES = 4

FETCH_TIMEOUT = 10
MAX_FETCH_WORKERS = 8

HABR_PREFIX = "https://habr.com/"

CATEGORIES = [
    "AI & Agents",
    "Fullstack",
    "Backend & APIs",
    "GCP & DevOps",
    "Databases",
    "Worth Reading",
]

GEMINI_MODEL = "gemini-2.5-flash"
