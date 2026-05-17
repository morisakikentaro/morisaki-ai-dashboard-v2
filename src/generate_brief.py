import json
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI

SYSTEM_PROMPT = """あなたは森崎賢太郎さん専用のAI経営インテリジェンス編集者です。
目的は、生成AIニュースを単に要約することではなく、経営判断に使える形へ変換することです。

重視する視点:
- 経営者視点
- 朝日新聞社に関連するメディア、編集、信頼性、AI検索、著作権、ニュースビジネス
- アルファサードに関連するCMS、コンテンツ管理、構造化、RAG、ナレッジ管理、アクセシビリティ、企業DX
- 日本企業の生成AI導入状況
- ビジネス活用、AIエージェント、エンタープライズAI

出力は必ずJSONのみ。
記事本文の長い引用は避け、短い引用風の要点は25語以内にしてください。
"""

USER_TEMPLATE = """以下の記事候補から、森崎さん向け Morning AI Brief を作ってください。

要件:
- 重要ニュースを最大5件
- 各記事に title, summary, quote, url, source, importance_score, asahi_score, alfasado_score, category を付与
- category は "AI検索", "メディア", "CMS/ナレッジ", "日本企業導入", "AIエージェント", "規制/著作権", "その他" のいずれか
- 朝日新聞社視点の示唆を3つ
- アルファサード視点の示唆を3つ
- 今日の経営アクションを3つ
- 今日の一言を1つ
- 日本語で出力

記事候補:
{articles_json}
"""

def fallback_brief(raw_articles):
    today = datetime.now().strftime("%Y-%m-%d")
    articles = raw_articles.get("articles", [])[:5]
    return {
        "date": today,
        "headline": "生成AIの最新動向を確認",
        "one_liner": "AIを使うだけでなく、AIが動ける情報基盤を作れるかが差になります。",
        "items": [
            {
                "title": a.get("title", "Untitled"),
                "summary": a.get("summary", "")[:180],
                "quote": "経営視点では、業務と情報基盤への影響を見るべきです。",
                "url": a.get("url", ""),
                "source": a.get("source", ""),
                "importance_score": 70,
                "asahi_score": 60,
                "alfasado_score": 60,
                "category": "その他",
            } for a in articles
        ],
        "asahi_insights": [
            "AI検索時代には、一次情報・信頼性・引用されやすさが重要になります。",
            "記事をAIが理解しやすい構造に整えることが、流通面の競争力になります。",
            "著作権と学習データの論点は継続監視が必要です。"
        ],
        "alfasado_insights": [
            "CMSはAI-readyな知識基盤へ拡張できます。",
            "RAG、構造化、権限管理、履歴管理は顧客提案の中核になります。",
            "顧客の社内ナレッジ整理は、生成AI導入の入口になります。"
        ],
        "actions": [
            "顧客向けAI-ready CMS診断項目を1つ追加する。",
            "朝日新聞社視点で、AI検索と信頼性の論点をメモ化する。",
            "社内のAI活用小実験を1つ選び、効果測定する。"
        ],
    }

def main():
    raw_path = Path("data/raw_articles.json")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    today = datetime.now().strftime("%Y-%m-%d")
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        brief = fallback_brief(raw)
    else:
        client = OpenAI(api_key=api_key)
        prompt = USER_TEMPLATE.format(
            articles_json=json.dumps(raw["articles"][:30], ensure_ascii=False, indent=2)
        )
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
        brief["date"] = brief.get("date") or today

    briefs_path = Path("data/briefs.json")
    if briefs_path.exists():
        all_briefs = json.loads(briefs_path.read_text(encoding="utf-8"))
    else:
        all_briefs = {}

    all_briefs[brief["date"]] = brief
    briefs_path.write_text(json.dumps(all_briefs, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
