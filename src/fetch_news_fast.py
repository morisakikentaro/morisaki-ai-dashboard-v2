import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser


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

    # 国内IT/AI系
    ("ITmedia AI+", "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml", "japan"),
    ("ITmedia NEWS", "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml", "japan"),
    ("Publickey", "https://www.publickey1.jp/atom.xml", "japan"),
    ("Ledge.ai", "https://ledge.ai/feed/", "japan"),
    ("AINOW", "https://ainow.ai/feed/", "japan"),
    ("AI-SCHOLAR", "https://ai-scholar.tech/feed/", "japan"),
    ("CNET Japan", "https://japan.cnet.com/rss/index.rdf", "japan"),
    ("ZDNET Japan", "https://japan.zdnet.com/rss/index.rdf", "japan"),

    # 官公庁・制度
    ("経済産業省 新着情報", "https://www.meti.go.jp/rss/meti_news.xml", "policy"),
    ("デジタル庁 新着情報", "https://www.digital.go.jp/rss.xml", "policy"),

    # Google News検索RSS
    ("Google News JP: 生成AI 企業 導入", "https://news.google.com/rss/search?q=" + quote_plus("生成AI 企業 導入") + "&hl=ja&gl=JP&ceid=JP:ja", "japan"),
    ("Google News JP: AI検索 メディア 著作権", "https://news.google.com/rss/search?q=" + quote_plus("AI検索 メディア 著作権") + "&hl=ja&gl=JP&ceid=JP:ja", "media"),
    ("Google News JP: CMS AI RAG ナレッジ", "https://news.google.com/rss/search?q=" + quote_plus("CMS AI RAG ナレッジ") + "&hl=ja&gl=JP&ceid=JP:ja", "japan"),
    ("Google News JP: AIエージェント 日本企業", "https://news.google.com/rss/search?q=" + quote_plus("AIエージェント 日本企業") + "&hl=ja&gl=JP&ceid=JP:ja", "japan"),
]

MATCH_KEYWORDS = [
    "生成ai", "生成 ai", "人工知能", "ai", "llm", "chatgpt", "claude", "gemini",
    "copilot", "openai", "anthropic", "google", "microsoft", "nvidia",
    "ai検索", "検索", "overview", "perplexity", "search", "seo", "geo",
    "agent", "agents", "エージェント", "自律", "業務自動化",
    "enterprise", "エンタープライズ", "企業導入", "導入事例", "dx",
    "cms", "コンテンツ管理", "ナレッジ", "knowledge", "rag", "構造化",
    "メディア", "新聞", "ニュース", "journalism", "publisher", "著作権", "copyright",
    "アクセシビリティ", "ガバナンス", "規制", "policy",
]

IMPACT_KEYWORDS = {
    "ai_search": ["ai検索", "overview", "perplexity", "search", "seo", "geo", "検索流入", "著作権", "copyright", "publisher"],
    "enterprise": ["enterprise", "エンタープライズ", "企業導入", "業務", "dx", "copilot", "claude", "chatgpt", "gemini"],
    "cms_knowledge": ["cms", "ナレッジ", "knowledge", "rag", "構造化", "コンテンツ管理", "データ基盤"],
    "media": ["メディア", "新聞", "ニュース", "journalism", "publisher", "読者", "編集", "報道"],
    "japan": ["日本", "国内", "企業", "自治体", "官公庁", "導入"],
    "infra": ["半導体", "gpu", "データセンター", "クラウド", "aws", "azure", "nvidia", "インフラ"],
}


def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.replace("\n", " ").replace("\r", " ").split()).strip()
    return text


def matches(item):
    blob = " ".join([
        item.get("title", ""),
        item.get("summary", ""),
        item.get("url", ""),
        item.get("source", ""),
    ]).lower()
    return any(keyword.lower() in blob for keyword in MATCH_KEYWORDS)


def score_article(item):
    blob = " ".join([
        item.get("title", ""),
        item.get("summary", ""),
        item.get("source", ""),
    ]).lower()

    score = 0
    matched_topics = []

    for topic, keywords in IMPACT_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword.lower() in blob)
        if hits:
            score += min(hits * 8, 24)
            matched_topics.append(topic)

    group = item.get("source_group")
    if group == "global":
        score += 12
    elif group == "japan":
        score += 14
    elif group in ("media", "search"):
        score += 18
    elif group == "policy":
        score += 10

    if item.get("summary") and len(item["summary"]) > 120:
        score += 8

    dev_only_words = ["runtime", "ランタイム", "コードエディタ", "javascript", "python", "rust", "zig", "mojo"]
    if any(w in blob for w in dev_only_words) and not any(w in blob for w in ["enterprise", "企業", "導入", "クラウド", "aiエージェント"]):
        score -= 8

    return score, matched_topics


def parse_feed(source_name, feed_url, group):
    items = []
    parsed = feedparser.parse(feed_url)

    # 各RSSは最大8件まで。外部サイト本文取得はしないので高速です。
    for entry in parsed.entries[:8]:
        title = clean_text(entry.get("title"))
        url = clean_text(entry.get("link"))
        summary = clean_text(entry.get("summary") or entry.get("description"))
        published = clean_text(entry.get("published") or entry.get("updated"))

        if not title or not url:
            continue

        item = {
            "title": title,
            "url": url,
            "summary": summary[:900],
            "content": summary[:1200],  # generate_brief.pyが参照できるようsummaryをcontentにも入れる
            "published": published,
            "source": source_name or clean_text(parsed.feed.get("title")),
            "source_group": group,
        }

        if not matches(item):
            continue

        score, topics = score_article(item)
        item["selection_score"] = score
        item["matched_topics"] = topics
        items.append(item)

    return items


def select_balanced_articles(articles, limit=24):
    if not articles:
        return []

    articles = sorted(articles, key=lambda a: a.get("selection_score", 0), reverse=True)

    selected = []
    used_urls = set()

    def add_from(predicate, max_count):
        count = 0
        for article in articles:
            key = article["url"].split("?")[0]
            if key in used_urls:
                continue
            if predicate(article):
                selected.append(article)
                used_urls.add(key)
                count += 1
            if count >= max_count:
                break

    # 偏りすぎを防ぐ。日本・海外・メディア/検索を混ぜる。
    add_from(lambda a: a.get("source_group") in ("media", "search") or "ai_search" in a.get("matched_topics", []), 5)
    add_from(lambda a: a.get("source_group") == "japan" or "japan" in a.get("matched_topics", []), 7)
    add_from(lambda a: a.get("source_group") == "global", 6)
    add_from(lambda a: "cms_knowledge" in a.get("matched_topics", []) or "enterprise" in a.get("matched_topics", []), 5)

    for article in articles:
        key = article["url"].split("?")[0]
        if key not in used_urls:
            selected.append(article)
            used_urls.add(key)
        if len(selected) >= limit:
            break

    return selected[:limit]


def main():
    articles = []
    for source_name, feed_url, group in RSS_FEEDS:
        try:
            articles.extend(parse_feed(source_name, feed_url, group))
        except Exception as error:
            print(f"[WARN] failed feed: {source_name} {feed_url}: {error}")

    seen = set()
    unique = []
    for article in articles:
        key = article["url"].split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)

    selected = select_balanced_articles(unique, limit=24)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": selected,
    }

    Path("data").mkdir(exist_ok=True)
    Path("data/raw_articles.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Collected {len(unique)} articles, selected {len(selected)} articles.")


if __name__ == "__main__":
    main()
