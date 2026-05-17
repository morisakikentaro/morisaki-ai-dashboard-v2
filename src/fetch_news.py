import json
from datetime import datetime, timezone
from pathlib import Path

import feedparser

RSS_FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.anthropic.com/news/rss.xml",
    "https://www.microsoft.com/en-us/ai/blog/feed/",
    "https://www.niemanlab.org/feed/",
    "https://www.cjr.org/feed",
    "https://prtimes.jp/topics/keywords/%E7%94%9F%E6%88%90AI",
]

KEYWORDS = [
    "生成AI", "AI", "人工知能", "LLM", "ChatGPT", "Claude", "Gemini",
    "AI検索", "search", "agent", "エージェント", "CMS", "RAG",
    "media", "journalism", "news", "copyright", "著作権",
    "enterprise", "DX", "ナレッジ", "knowledge"
]

def matches(entry: dict) -> bool:
    text = " ".join([
        str(entry.get("title", "")),
        str(entry.get("summary", "")),
        str(entry.get("link", "")),
    ]).lower()
    return any(k.lower() in text for k in KEYWORDS)

def main():
    articles = []
    for feed_url in RSS_FEEDS:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:12]:
            item = {
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "published": entry.get("published", "") or entry.get("updated", ""),
                "source": parsed.feed.get("title", feed_url),
            }
            if item["title"] and item["url"] and matches(item):
                articles.append(item)

    # URLで重複除去
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            unique.append(a)
            seen.add(a["url"])

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": unique[:40],
    }

    Path("data").mkdir(exist_ok=True)
    Path("data/raw_articles.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
