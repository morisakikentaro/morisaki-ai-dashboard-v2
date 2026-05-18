import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser


# RSSで取得できるものを中心に、海外一次情報・国内AI/IT・メディア/検索系を混ぜます。
# 失敗したフィードは無視して、全体処理は止めません。
RSS_FEEDS = [
    # 海外一次情報
    ("OpenAI News", "https://openai.com/news/rss.xml", "global"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/", "global"),
    ("Anthropic News", "https://www.anthropic.com/news/rss.xml", "global"),
    ("Microsoft AI Blog", "https://www.microsoft.com/en-us/ai/blog/feed/", "global"),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/", "global"),

    # メディア / AI検索 / ジャーナリズム
    ("Nieman Lab", "https://www.niemanlab.org/feed/", "media"),
    ("Columbia Journalism Review", "https://www.cjr.org/feed", "media"),
    ("Search Engine Land", "https://searchengineland.com/feed", "search"),

    # 国内IT/AI系。RSS URLは変更されることがあるため、失敗してもスキップします。
    ("ITmedia AI+", "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml", "japan"),
    ("ITmedia NEWS", "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml", "japan"),
    ("Publickey", "https://www.publickey1.jp/atom.xml", "japan"),
    ("Ledge.ai", "https://ledge.ai/feed/", "japan"),
    ("AINOW", "https://ainow.ai/feed/", "japan"),
    ("AI-SCHOLAR", "https://ai-scholar.tech/feed/", "japan"),
    ("CNET Japan", "https://japan.cnet.com/rss/index.rdf", "japan"),
    ("ZDNET Japan", "https://japan.zdnet.com/rss/index.rdf", "japan"),
    ("ASCII.jp", "https://ascii.jp/rss.xml", "japan"),

    # 官公庁・制度
    ("経済産業省 新着情報", "https://www.meti.go.jp/rss/meti_news.xml", "policy"),
    ("デジタル庁 新着情報", "https://www.digital.go.jp/rss.xml", "policy"),

    # キーワード検索系RSS。国内導入事例の拾い漏れ対策。
    ("Google News JP: 生成AI 企業 導入", "https://news.google.com/rss/search?q=" + quote_plus("生成AI 企業 導入") + "&hl=ja&gl=JP&ceid=JP:ja", "japan"),
    ("Google News JP: AI検索 メディア 著作権", "https://news.google.com/rss/search?q=" + quote_plus("AI検索 メディア 著作権") + "&hl=ja&gl=JP&ceid=JP:ja", "media"),
    ("Google News JP: CMS AI RAG ナレッジ", "https://news.google.com/rss/search?q=" + quote_plus("CMS AI RAG ナレッジ") + "&hl=ja&gl=JP&ceid=JP:ja", "japan"),
]

KEYWORDS = [
    "生成ai", "生成 ai", "人工知能", "ai", "llm", "chatgpt", "claude", "gemini",
    "copilot", "openai", "anthropic", "google", "microsoft", "nvidia",
    "ai検索", "検索", "overview", "perplexity", "search", "seo", "geo",
    "agent", "agents", "エージェント", "自律", "業務自動化",
    "enterprise", "エンタープライズ", "企業導入", "導入事例", "dx",
    "cms", "コンテンツ管理", "ナレッジ", "knowledge", "rag", "構造化",
    "メディア", "新聞", "ニュース", "journalism", "publisher", "著作権", "copyright",
    "アクセシビリティ", "ガバナンス", "規制", "policy",
]


def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    return " ".join(text.replace("\n", " ").replace("\r", " ").split()).strip()


def matches(item):
    blob = " ".join([
        item.get("title", ""),
        item.get("summary", ""),
        item.get("url", ""),
        item.get("source", ""),
    ]).lower()
    return any(keyword.lower() in blob for keyword in KEYWORDS)


def parse_feed(source_name, feed_url, group):
    items = []
    parsed = feedparser.parse(feed_url)

    for entry in parsed.entries[:12]:
        title = clean_text(entry.get("title"))
        url = clean_text(entry.get("link"))
        summary = clean_text(entry.get("summary") or entry.get("description"))
        published = clean_text(entry.get("published") or entry.get("updated"))

        if not title or not url:
            continue

        item = {
            "title": title,
            "url": url,
            "summary": summary[:600],
            "published": published,
            "source": source_name or clean_text(parsed.feed.get("title")),
            "source_group": group,
        }

        if matches(item):
            items.append(item)

    return items


def main():
    articles = []

    for source_name, feed_url, group in RSS_FEEDS:
        try:
            articles.extend(parse_feed(source_name, feed_url, group))
        except Exception as error:
            print(f"[WARN] failed feed: {source_name} {feed_url}: {error}")

    # URL重複除去。Google News経由と本家RSSで重なる場合があるため。
    seen = set()
    unique = []
    for article in articles:
        key = article["url"].split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)

    # 国内・メディア・検索系を少し優先しつつ、海外一次情報も残す。
    priority = {"japan": 0, "media": 1, "search": 1, "policy": 2, "global": 3}
    unique.sort(key=lambda x: (priority.get(x.get("source_group"), 9), x.get("published", "")), reverse=False)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": unique[:50],
    }

    Path("data").mkdir(exist_ok=True)
    Path("data/raw_articles.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
