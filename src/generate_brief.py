import json
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """あなたは日本語の経営者向けAIニュース編集者です。
目的は、生成AIニュースを単なる要約ではなく、経営判断に使える「理解支援」に変換することです。

最重要ルール:
- 出力は必ずJSONのみ。
- 表示用の見出し、解説、なぜ重要か、経営インパクト、視点別示唆、アクションは必ず自然な日本語で書く。
- 英語を使ってよいのは、会社名、製品名、サービス名、元記事タイトル、URLのみ。
- 公開HTMLに表示される前提なので、個人名や特定の社名を本文に出さない。
- 会社名が記事タイトルや出典名に含まれる場合はそのままでよい。
- 元記事タイトルは original_title に保持する。
- title_jp には、内容が一目でわかる日本語見出しを付ける。
- summary は「3行要約」ではなく「何が起きているか」として、180〜360字程度で丁寧に説明する。
- why は「なぜ重要か」として、120〜260字程度で経営者にわかる言葉で説明する。
- impact は3〜5項目の日本語リストにする。
- 長い引用は避ける。quote は引用ではなく短い日本語の要点でよい。
- 出典URLは必ず保持する。

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
- one_liner: 日本語。今日の全体像を2〜3文で
- items: 最大6件。国内動向を最低2件、AI検索/メディア/著作権/CMS/ナレッジ系を最低1件含める努力をしてください
- media_insights: 視点A：メディア視点の示唆を3件、日本語
- solution_insights: 視点B：ソリューション視点の示唆を3件、日本語
- actions: 今日のアクションを3件、日本語

各 item は以下の形式:
- title_jp: 日本語見出し。内容が一目でわかるようにする
- original_title: 元記事タイトル。英語記事の場合は英語タイトルのままでよい
- source: 媒体名
- url: 記事URL
- category: 日本語カテゴリ。例: AI検索, AIエージェント, Enterprise AI, CMS/ナレッジ, メディア, 規制/著作権, 日本企業導入, AIインフラ
- summary: 日本語。「何が起きているか」を180〜360字程度で説明
- why: 日本語。「なぜ重要か」を120〜260字程度で説明
- impact: 日本語の配列。経営インパクトを3〜5項目
- quote: 日本語の短い要点。引用ではなく要約でよい
- importance_score: 0〜100の数値

追加方針:
- URLがない記事は採用しない
- 日本語サイトの記事は優先的に採用
- 海外一次情報も重要なものは採用
- 単なる製品アップデートより、経営・情報流通・業務変革に影響するものを優先
- 視点Aはメディア、ニュース、検索流入、著作権、信頼性、編集、読者接点の観点
- 視点BはCMS、ナレッジ基盤、RAG、構造化、実装支援、運用保守、企業DXの観点

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
            "title_jp": "生成AI・AI活用に関する注目動向",
            "original_title": title,
            "source": source,
            "url": url,
            "category": "AI動向",
            "summary": (
                "この記事は、生成AI、AI検索、エンタープライズAI、または企業のAI活用に関連する動向を扱っています。"
                "詳細な本文取得やAI要約に失敗した場合でも、経営者としては、情報発信、業務設計、ナレッジ活用、"
                "AIガバナンスへの影響を確認する価値があります。"
            ),
            "why": (
                "AI活用の競争軸が、単なるツール導入から、情報基盤、業務プロセス、運用体制、"
                "リスク管理へ移っているためです。"
            ),
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
            "title_jp": "AI検索・AIエージェント・企業ナレッジ基盤が主要テーマに",
            "original_title": "AI search, AI agents and enterprise knowledge platforms",
            "source": "OpenAI News",
            "url": "https://openai.com/news/",
            "category": "AI動向",
            "summary": (
                "生成AIは、チャットで質問に答える段階から、検索、業務実行、社内外の知識活用へ広がっています。"
                "企業は、どのAIツールを使うかだけでなく、AIが正しく参照できる情報基盤を整えることが重要になります。"
                "特にCMS、FAQ、社内文書、製品情報、導入事例などの整理が競争力になります。"
            ),
            "why": (
                "AI活用の競争軸が、モデル選定から情報基盤・業務設計・運用体制へ移っているためです。"
                "AIが使えるデータやコンテンツを持つ企業ほど、業務効率化や顧客接点の改善を進めやすくなります。"
            ),
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
        "one_liner": (
            "生成AIは、単なるチャットツールから、検索、業務実行、企業ナレッジ活用の基盤へ広がっています。"
            "これからはAIを使うだけでなく、AIが正しく参照できる情報基盤を持つことが競争力になります。"
        ),
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

        original_title = item.get("original_title") or item.get("title") or ""
        title_jp = item.get("title_jp") or item.get("title") or original_title

        normalized_items.append({
            "title_jp": title_jp,
            "original_title": original_title,
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
            articles_json=json.dumps(raw.get("articles", [])[:40], ensure_ascii=False, indent=2)
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
