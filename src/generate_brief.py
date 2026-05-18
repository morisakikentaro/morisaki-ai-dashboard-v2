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
- summary は「何が起きているか」として、220〜450字程度で丁寧に説明する。
- why は「なぜ重要か」として、140〜300字程度で経営者にわかる言葉で説明する。
- impact は3〜5項目の日本語リストにする。
- quote は引用ではなく、短い日本語の要点にする。
- 出典URLは必ず保持する。
- 本文情報が不足する記事は、無理に採用しない。汎用的な説明文で埋めない。

記事選定方針:
- 単にAIという単語がある記事ではなく、経営・情報流通・業務変革に影響がある記事を優先する。
- 国内動向、海外一次情報、メディア/AI検索/CMS/ナレッジ系をバランスよく含める。
- 技術者向けの細かい開発ツール記事は、経営インパクトが説明できる場合のみ採用する。
- 似た記事が複数ある場合は、より一次情報に近いもの、または経営インパクトが明確なものを選ぶ。

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
- items: 最大6件
- media_insights: 視点A：メディア視点の示唆を3件、日本語
- solution_insights: 視点B：ソリューション視点の示唆を3件、日本語
- actions: 今日のアクションを3件、日本語

各 item は以下の形式:
- title_jp: 日本語見出し。内容が一目でわかるようにする
- original_title: 元記事タイトル。英語記事の場合は英語タイトルのままでよい
- source: 媒体名
- url: 記事URL
- category: 日本語カテゴリ。例: AI検索, AIエージェント, Enterprise AI, CMS/ナレッジ, メディア, 規制/著作権, 日本企業導入, AIインフラ
- summary: 日本語。「何が起きているか」を220〜450字程度で説明
- why: 日本語。「なぜ重要か」を140〜300字程度で説明
- impact: 日本語の配列。経営インパクトを3〜5項目
- quote: 日本語の短い要点。引用ではなく要約でよい
- importance_score: 0〜100の数値

必ず避けること:
- 「この記事は生成AIに関連する注目記事です」のような汎用文で埋めること
- 内容が薄いのに採用すること
- 全部を日本サイトまたは全部を海外サイトに偏らせること
- 企業名や個人名を本文で不必要に出すこと

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
        content = article.get("content") or article.get("summary") or ""

        if not url or len(content) < 80:
            continue

        items.append({
            "title_jp": title[:80],
            "original_title": title,
            "source": source,
            "url": url,
            "category": "AI動向",
            "summary": content[:350],
            "why": "この記事は、AI活用、企業の情報基盤、業務変革、またはAIインフラに関係する可能性があります。詳細を確認し、自社の事業や顧客提案にどう影響するかを見極める価値があります。",
            "impact": [
                "AI活用を前提にした情報設計や業務設計が重要になる",
                "社内外のコンテンツやデータを整理する必要が高まる",
                "単発導入ではなく、運用・改善・ガバナンスまで含めた体制が必要になる",
            ],
            "quote": "AI活用は情報基盤と運用体制の競争になりつつあります。",
            "importance_score": 65,
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
        summary = item.get("summary", "")

        # 汎用文だけのカードを極力排除
        generic_phrases = [
            "生成AI、AI検索、またはエンタープライズAIに関連する注目記事です",
            "詳細な本文取得やAI要約に失敗",
            "この記事は、生成AI",
        ]
        if any(p in summary for p in generic_phrases):
            continue

        normalized_items.append({
            "title_jp": title_jp,
            "original_title": original_title,
            "source": item.get("source", "記事を開く"),
            "url": item.get("url", ""),
            "category": item.get("category", "AI動向"),
            "summary": summary,
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
            articles_json=json.dumps(raw.get("articles", [])[:24], ensure_ascii=False, indent=2)
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
