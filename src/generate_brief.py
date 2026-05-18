import json
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """あなたは日本語の経営者向けAIニュース編集者です。
目的は、生成AIニュースを単なる要約ではなく、経営判断に使えるブリーフへ変換することです。

重要:
- 出力は必ずJSONのみ。
- 見出し、要約、なぜ重要か、経営インパクト、視点別示唆、アクションは、必ず自然な日本語で書いてください。
- 英語を使ってよいのは、会社名、製品名、サービス名、元記事タイトル、URLのみです。
- 公開HTMLに表示される前提なので、個人名や特定の社名を本文に出さないでください。
- 「視点A：メディア視点」「視点B：ソリューション視点」という抽象表現を使ってください。
- 長い引用は避けてください。引用風の要点を書く場合も25語以内にしてください。
- 出典URLは必ず保持してください。
- 記事タイトルは元記事タイトルのままでよいですが、summary / why / impact / insights / actions は日本語にしてください。

重視するテーマ:
- 生成AI
- AI検索
- AIエージェント
- Enterprise AI
- CMS
- ナレッジ管理
- RAG
- 構造化データ
- メディア企業のAI対応
- 著作権、AIクローラー、AI検索流入
- 日本企業の生成AI導入
- ガバナンス、アクセシビリティ、信頼性
"""


USER_TEMPLATE = """以下の記事候補から、Morning AI Brief を作成してください。

出力要件:
- JSONのみで出力
- headline: 日本語
- one_liner: 日本語
- items: 最大6件
- media_insights: 視点A：メディア視点の示唆を3件、日本語
- solution_insights: 視点B：ソリューション視点の示唆を3件、日本語
- actions: 今日のアクションを3件、日本語

各 item は以下の形式:
- title: 元記事タイトル。英語記事の場合は英語タイトルのままでよい
- source: 媒体名
- url: 記事URL
- category: 日本語カテゴリ。例: AI検索, AIエージェント, Enterprise AI, CMS/ナレッジ, メディア, 規制/著作権, 日本企業導入, AIインフラ
- summary: 日本語の3行要約。自然な経営者向け日本語
- why: 日本語。「なぜ重要か」を1〜2文で
- impact: 日本語の配列。経営インパクトを3〜4項目
- quote: 日本語の短い要点。引用ではなく要約でよい
- importance_score: 0〜100の数値

追加方針:
- 会社名・個人名を本文で不必要に出さない
- ただし、記事タイトルや出典名に含まれる会社名はそのままでよい
- 視点Aはメディア、ニュース、検索流入、著作権、信頼性、編集、読者接点の観点
- 視点BはCMS、ナレッジ基盤、RAG、構造化、実装支援、運用保守、企業DXの観点
- URLがない記事は採用しない
- できるだけ新しく、経営インパクトが大きいものを優先

記事候補:
{articles_json}
"""


def fallback_brief(raw_articles):
    today = datetime.now().strftime("%Y-%m-%d")
    articles = raw_articles.get("articles", [])[:6]

    items = []
    for article in articles:
        title = article.get("title", "Untitled")
        url = article.get("url", "")
        source = article.get("source", "")

        if not url:
            continue

        items.append({
            "title": title,
            "source": source,
            "url": url,
            "category": "AI動向",
            "summary": (
                "生成AI、AI検索、またはエンタープライズAIに関連する注目記事です。"
                "企業の情報発信、業務設計、ナレッジ活用への影響を確認する価値があります。"
            ),
            "why": "AI活用の競争軸が、ツール導入から情報基盤・業務プロセス・運用体制へ移っているためです。",
            "impact": [
                "AI検索に引用されやすい情報設計が重要になる",
                "社内外のコンテンツを構造化する必要が高まる",
                "AI活用支援は単発導入より継続運用モデルと相性がよい",
            ],
            "quote": "AIが扱いやすい情報基盤づくりが競争力になります。",
            "importance_score": 70,
        })

    if not items:
        items = [{
            "title": "AI検索・AIエージェント・企業ナレッジ基盤が主要テーマに",
            "source": "OpenAI News",
            "url": "https://openai.com/news/",
            "category": "AI動向",
            "summary": (
                "生成AIはチャット利用から、検索、業務実行、社内外の知識活用へ広がっています。"
                "企業はAIが参照しやすい情報基盤を整える必要があります。"
            ),
            "why": "AI活用の競争軸が、モデル選定から情報基盤・業務設計・運用体制へ移っているためです。",
            "impact": [
                "AI検索に引用されやすい情報設計が重要になる",
                "CMSやナレッジ基盤の価値が高まる",
                "AI導入支援は継続運用モデルと相性がよい",
            ],
            "quote": "AI時代は、情報基盤そのものが競争力になります。",
            "importance_score": 80,
        }]

    return {
        "date": today,
        "headline": "生成AIは検索・実行・知識基盤へ",
        "one_liner": "AIを使うだけでなく、AIが正しく参照できる情報基盤を持つことが競争力になります。",
        "items": items,
        "media_insights": [
            "AI検索時代には、一次情報・信頼性・引用されやすい構造がメディア価値になります。",
            "記事をAIが理解しやすい構造に整えることが、検索流入や読者接点の再設計につながります。",
            "著作権、学習データ、要約表示による流入変化は継続監視が必要です。",
        ],
        "solution_insights": [
            "CMSはWeb更新ツールから、AI-readyな企業知識基盤へ拡張できます。",
            "RAG、構造化、権限管理、履歴管理は顧客提案の中核になります。",
            "顧客の社内ナレッジ整理は、生成AI導入の入口として提案しやすい領域です。",
        ],
        "actions": [
            "AI検索・生成AI時代に必要なCMS要件を整理する。",
            "出典付きニュースカードを継続的にレビューする。",
            "AI-readyな情報基盤の提案項目を1つ追加する。",
        ],
    }


def validate_and_normalize_brief(brief, raw_articles):
    today = datetime.now().strftime("%Y-%m-%d")
    if not isinstance(brief, dict):
        return fallback_brief(raw_articles)

    brief["date"] = brief.get("date") or today
    brief["headline"] = brief.get("headline") or "生成AIの最新動向"
    brief["one_liner"] = brief.get("one_liner") or "生成AIの動向を、経営・メディア・ソリューション視点で整理します。"

    items = brief.get("items")
    if not isinstance(items, list):
        items = []

    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if not item.get("url"):
            continue

        normalized_items.append({
            "title": item.get("title", ""),
            "source": item.get("source", "記事を開く"),
            "url": item.get("url", ""),
            "category": item.get("category", "AI動向"),
            "summary": item.get("summary", ""),
            "why": item.get("why", item.get("why_important", "")),
            "impact": item.get("impact", item.get("business_impact", [])),
            "quote": item.get("quote", ""),
            "importance_score": item.get("importance_score", 70),
        })

    if not normalized_items:
        return fallback_brief(raw_articles)

    brief["items"] = normalized_items[:6]

    if not isinstance(brief.get("media_insights"), list):
        brief["media_insights"] = brief.get("asahi_insights", [])
    if not isinstance(brief.get("solution_insights"), list):
        brief["solution_insights"] = brief.get("alfasado_insights", [])
    if not isinstance(brief.get("actions"), list):
        brief["actions"] = []

    if not brief["media_insights"]:
        brief["media_insights"] = [
            "AI検索時代には、一次情報・信頼性・引用されやすい構造がメディア価値になります。",
            "記事をAIが理解しやすい構造に整えることが、検索流入や読者接点の再設計につながります。",
            "著作権、学習データ、要約表示による流入変化は継続監視が必要です。",
        ]

    if not brief["solution_insights"]:
        brief["solution_insights"] = [
            "CMSはWeb更新ツールから、AI-readyな企業知識基盤へ拡張できます。",
            "RAG、構造化、権限管理、履歴管理は顧客提案の中核になります。",
            "顧客の社内ナレッジ整理は、生成AI導入の入口として提案しやすい領域です。",
        ]

    if not brief["actions"]:
        brief["actions"] = [
            "AI検索・生成AI時代に必要なCMS要件を整理する。",
            "出典付きニュースカードを継続的にレビューする。",
            "AI-readyな情報基盤の提案項目を1つ追加する。",
        ]

    return brief


def main():
    raw_path = Path("data/raw_articles.json")
    if raw_path.exists():
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        raw = {"articles": []}

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        brief = fallback_brief(raw)
    else:
        client = OpenAI(api_key=api_key)
        prompt = USER_TEMPLATE.format(
            articles_json=json.dumps(raw.get("articles", [])[:30], ensure_ascii=False, indent=2)
        )

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            brief = json.loads(response.choices[0].message.content)
            brief = validate_and_normalize_brief(brief, raw)
        except Exception as error:
            print("OpenAI generation failed. fallback used:", error)
            brief = fallback_brief(raw)

    briefs_path = Path("data/briefs.json")
    if briefs_path.exists():
        all_briefs = json.loads(briefs_path.read_text(encoding="utf-8"))
    else:
        all_briefs = {}

    all_briefs[brief["date"]] = brief
    briefs_path.parent.mkdir(exist_ok=True)
    briefs_path.write_text(
        json.dumps(all_briefs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
