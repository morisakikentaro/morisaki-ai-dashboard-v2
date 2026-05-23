import json
import os
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """あなたは日本語の経営者向けAI戦略編集者です。
目的は、生成AI関連ニュースを「ニュース一覧」ではなく、毎朝読む価値のある戦略メモへ変換することです。

最重要ルール:
- 出力は必ずJSONのみ。
- 文章は必ず自然な日本語。
- 英語を使ってよいのは、会社名、製品名、サービス名、元記事タイトル、URLのみ。
- 公開HTMLに表示される前提なので、個人名や特定社名を本文で不必要に出さない。
- ただし、元記事タイトルや出典に含まれる会社名はそのままでよい。
- ニュースを並べるのではなく、「今日、世界がどう変わったのか」を説明する。
- 読むのに5〜8分かかってよい。短くまとめすぎない。
- 重要なのは、変化 → 背景 → 影響 → 次の打ち手、の流れを作ること。
- title_jp は必ず日本語。英語タイトルをそのまま使わない。
- original_title には元記事タイトルを保持する。

重視テーマ:
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
- ガバナンス、信頼性、アクセシビリティ
"""


USER_TEMPLATE = """以下の記事候補から、Morning AI Brief を「朝の戦略メモ」として作成してください。

出力JSON形式:
{
  "date": "YYYY-MM-DD",
  "headline": "日本語。今日の大きなテーマ",
  "executive_summary": "日本語。今日の全体像を500〜900字で。ニュース一覧ではなく、構造変化として説明する",
  "big_shift": {
    "title": "日本語。今日の大きな変化",
    "body": "日本語。800〜1400字。何が変わったのか、なぜそうなっているのか、どこに向かっているのかを段落で説明する"
  },
  "why_now": {
    "title": "日本語。なぜ今それが起きているのか",
    "body": "日本語。600〜1000字。技術、事業、検索、情報流通、企業導入、コスト、規制などをつなげて説明する"
  },
  "media_perspective": {
    "title": "視点A：メディア視点",
    "body": "日本語。700〜1200字。AI検索、一次情報、アーカイブ、出典、読者接点、著作権、信頼性の観点から深く説明する",
    "bullets": ["日本語", "日本語", "日本語"]
  },
  "solution_perspective": {
    "title": "視点B：ソリューション視点",
    "body": "日本語。700〜1200字。CMS、Knowledge OS、RAG、構造化、API、権限管理、AIエージェント、Enterprise AIの観点から深く説明する",
    "bullets": ["日本語", "日本語", "日本語"]
  },
  "signals": [
    {
      "title_jp": "必ず日本語見出し",
      "original_title": "元記事タイトル",
      "source": "媒体名",
      "url": "URL",
      "category": "AI検索|AIエージェント|Enterprise AI|CMS/ナレッジ|メディア|規制/著作権|日本企業導入|AIインフラ|AI動向",
      "meaning": "日本語。この記事が示す意味を180〜320字で",
      "importance_score": 0
    }
  ],
  "actions": [
    {
      "title": "日本語。今日の一手",
      "body": "日本語。なぜそれをやるべきか、具体的に何をするかを150〜300字で"
    }
  ]
}

方針:
- signals は最大6件。記事は補助情報として扱う。
- まず大きな構造変化を説明し、最後に根拠記事を置く。
- メディア視点とソリューション視点は、抽象名のままにする。
- 会社名・個人名は本文で不必要に出さない。
- 元記事タイトル、出典、URLは必ず残す。
- 内容が薄い記事は採用しない。
- title_jp は英語禁止。英語タイトルをそのまま使わない。

記事候補:
{articles_json}
"""


def looks_english(text):
    if not text:
        return False
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    japanese_chars = len(re.findall(r"[ぁ-んァ-ン一-龥]", text))
    return ascii_letters > 15 and japanese_chars < 5


def fallback_japanese_title(title, source="", summary=""):
    blob = f"{title} {source} {summary}".lower()
    if any(k in blob for k in ["ai search", "overview", "perplexity", "検索", "seo", "geo"]):
        return "AI検索をめぐる重要動向"
    if any(k in blob for k in ["copyright", "著作権", "publisher", "media", "journalism", "新聞", "ニュース"]):
        return "メディアと著作権をめぐるAI動向"
    if any(k in blob for k in ["cms", "knowledge", "rag", "ナレッジ", "構造化", "コンテンツ管理"]):
        return "CMS・ナレッジ基盤に関するAI動向"
    if any(k in blob for k in ["agent", "エージェント", "autonomous", "automation", "業務自動化"]):
        return "AIエージェント活用の重要動向"
    if any(k in blob for k in ["enterprise", "企業", "導入", "business", "dx", "copilot"]):
        return "企業向け生成AI導入の重要動向"
    if any(k in blob for k in ["cloud", "aws", "azure", "gpu", "nvidia", "データセンター", "半導体"]):
        return "AIインフラをめぐる重要動向"
    return "生成AIをめぐる重要動向"


def fallback_category(title, source="", summary=""):
    blob = f"{title} {source} {summary}".lower()
    if any(k in blob for k in ["ai search", "overview", "perplexity", "検索", "seo", "geo"]):
        return "AI検索"
    if any(k in blob for k in ["copyright", "著作権", "publisher", "media", "journalism", "新聞", "ニュース"]):
        return "メディア"
    if any(k in blob for k in ["cms", "knowledge", "rag", "ナレッジ", "構造化", "コンテンツ管理"]):
        return "CMS/ナレッジ"
    if any(k in blob for k in ["agent", "エージェント", "autonomous", "automation", "業務自動化"]):
        return "AIエージェント"
    if any(k in blob for k in ["enterprise", "企業", "導入", "business", "dx", "copilot"]):
        return "Enterprise AI"
    if any(k in blob for k in ["cloud", "aws", "azure", "gpu", "nvidia", "データセンター", "半導体"]):
        return "AIインフラ"
    return "AI動向"


def make_signal(article):
    original_title = article.get("title", "Untitled")
    source = article.get("source", "")
    summary = article.get("summary") or article.get("content") or ""
    return {
        "title_jp": fallback_japanese_title(original_title, source, summary),
        "original_title": original_title,
        "source": source,
        "url": article.get("url", ""),
        "category": fallback_category(original_title, source, summary),
        "meaning": (
            f"元記事「{original_title}」は、生成AIをめぐる市場・技術・情報流通の変化を示す材料です。"
            "この記事単体で判断するのではなく、AI検索、企業ナレッジ基盤、業務プロセスの変化とつなげて見ることで、"
            "今後の事業機会やリスクを整理しやすくなります。"
        ),
        "importance_score": article.get("selection_score", 65) or 65,
    }


def fallback_brief(raw):
    today = datetime.now().strftime("%Y-%m-%d")
    articles = [a for a in raw.get("articles", []) if a.get("url")][:6]
    signals = [make_signal(a) for a in articles]

    if not signals:
        signals = [{
            "title_jp": "AI検索・AIエージェント・企業ナレッジ基盤が主要テーマに",
            "original_title": "AI search, AI agents and enterprise knowledge platforms",
            "source": "OpenAI News",
            "url": "https://openai.com/news/",
            "category": "AI動向",
            "meaning": "生成AIは、チャットで質問に答える段階から、検索、業務実行、社内外の知識活用へ広がっています。企業はAIが正しく参照できる情報基盤を整える必要があります。",
            "importance_score": 80,
        }]

    return {
        "date": today,
        "headline": "生成AIは、検索・実行・知識基盤の競争へ移っている",
        "executive_summary": (
            "今日の生成AI動向で重要なのは、個別の新機能やモデル性能ではなく、AIが情報流通と業務実行の中心に入り始めていることです。"
            "検索では、ユーザーがリンクを選ぶ前にAIが回答を作るようになり、企業ではAIエージェントが社内データや業務システムを横断して使われ始めています。"
            "この変化の中心には、AIが参照できる信頼性の高い情報基盤があります。メディアにとっては一次情報、出典、アーカイブ、信頼性がより重要になり、ソリューション側にとってはCMS、RAG、構造化データ、権限管理、運用保守が事業機会になります。"
        ),
        "big_shift": {
            "title": "AIは、コンテンツを読む側から業務を動かす側へ進み始めている",
            "body": (
                "これまで生成AIは、文章を作る、質問に答える、要約する、といった利用が中心でした。"
                "しかし今起きている変化は、AIがユーザーの代わりに情報を探し、整理し、判断の材料を作り、場合によっては業務の一部を実行する方向へ進んでいることです。"
                "検索ではAIが回答を先に提示し、企業内ではAIエージェントが文書、FAQ、顧客情報、業務システムを横断して使われ始めています。"
                "このとき価値を持つのは、AIモデルそのものだけではありません。AIが参照できる情報が整理されているか、権限が管理されているか、出典や更新履歴が明確か、業務に接続できる形になっているかが重要になります。"
                "つまり、生成AIの競争は、モデル選定の競争から、情報基盤と業務設計の競争へ移っています。"
            ),
        },
        "why_now": {
            "title": "なぜ今、情報基盤が重要になっているのか",
            "body": (
                "背景には、AI検索とEnterprise AIの同時進行があります。AI検索では、ユーザーがWebページへ移動する前にAIが回答をまとめるため、情報源として引用されるかどうかが重要になります。"
                "一方、企業内ではAIエージェントやRAGの活用が進み、社内文書、Webコンテンツ、FAQ、製品情報、業務データをAIが利用できる状態にする必要が出ています。"
                "そのため、従来のCMSやWebサイトは、単に人間に見せるためのものではなく、AIが理解し、検索し、参照し、業務に使うための知識基盤として再定義されつつあります。"
                "この変化は、メディア企業にもCMS・ソリューション企業にも関係します。信頼できる情報を持つ側と、それをAIが使える形に整える側の価値が同時に高まっているからです。"
            ),
        },
        "media_perspective": {
            "title": "視点A：メディア視点",
            "body": (
                "メディアにとって、AI検索の普及は単なる検索流入の変化ではありません。読者が記事ページに来る前に、AIが記事の内容を要約し、他の情報源と組み合わせて回答する時代が近づいています。"
                "このとき重要になるのは、記事がどれだけ多いかだけではなく、AIが信頼できる一次情報として扱えるかどうかです。出典、更新日、文脈、人物・組織・出来事の関係、過去記事とのつながり、解説の質が、AI時代のメディア価値になります。"
                "さらに、アーカイブの価値も上がります。過去記事は単なる保管物ではなく、AIが社会的文脈を理解するための知識資産になります。これを構造化し、正しく参照される形にできるかが、今後の競争力になります。"
            ),
            "bullets": [
                "AI検索時代には、一次情報・出典・更新履歴の明確さがメディア価値になる",
                "アーカイブは過去記事ではなく、AI時代の知識資産として再評価される",
                "検索流入だけでなく、AIに正しく引用される仕組みを設計する必要がある",
            ],
        },
        "solution_perspective": {
            "title": "視点B：ソリューション視点",
            "body": (
                "ソリューション側から見ると、CMSの役割は大きく変わっています。従来のCMSは、Webページを作り、承認し、公開するための仕組みでした。"
                "しかしAI時代には、CMSは企業の知識を整理し、AI検索やRAG、AIエージェントへ供給する基盤になります。製品情報、FAQ、導入事例、ニュース、PDF、動画、アクセシビリティ情報、更新履歴などを、AIが理解できる形で管理する必要があります。"
                "ここには大きな事業機会があります。多くの企業はAIツールを導入しても、社内情報が散らばっていてAIが使えません。CMS、ナレッジ管理、構造化データ、権限管理、運用保守を組み合わせた提案は、AI導入の現実的な入口になります。"
            ),
            "bullets": [
                "CMSはWeb更新ツールからAI-readyなKnowledge OSへ拡張できる",
                "RAG、構造化、権限管理、履歴管理は顧客提案の中核になる",
                "AI導入支援は初期構築だけでなく、継続運用・改善モデルに向いている",
            ],
        },
        "signals": signals,
        "actions": [
            {
                "title": "AI-ready CMSの要件を1枚に整理する",
                "body": "構造化データ、出典管理、更新履歴、権限管理、API、RAG連携、アクセシビリティを含めて、AI時代にCMSへ求められる要件を簡潔に整理します。営業資料や社内議論の土台になります。",
            },
            {
                "title": "AI検索で引用される情報設計を考える",
                "body": "記事や製品ページがAIにどう読まれるかを前提に、見出し、要約、FAQ、メタデータ、出典表示を見直します。これはSEOの延長ではなく、AIに信頼される情報設計です。",
            },
            {
                "title": "社内ナレッジの散らばりを棚卸しする",
                "body": "AI活用が進まない原因は、モデルではなく情報の散在にあることが多いです。社内文書、FAQ、提案資料、製品情報、サポート履歴がどこにあるかを整理するだけでも次の打ち手が見えてきます。",
            },
        ],
    }


def normalize_signal(item):
    original_title = item.get("original_title") or item.get("title") or ""
    title_jp = item.get("title_jp") or ""
    if not title_jp or title_jp == original_title or looks_english(title_jp):
        title_jp = fallback_japanese_title(original_title, item.get("source", ""), item.get("meaning", ""))
    meaning = item.get("meaning") or ""
    if not meaning or looks_english(meaning):
        meaning = "この記事は、生成AIをめぐる市場・技術・情報流通の変化を示す材料です。単体の記事としてではなく、AI検索、企業ナレッジ基盤、業務プロセスの変化とつなげて見ることが重要です。"
    return {
        "title_jp": title_jp,
        "original_title": original_title,
        "source": item.get("source", "記事を開く"),
        "url": item.get("url", ""),
        "category": item.get("category", fallback_category(original_title, item.get("source", ""), meaning)),
        "meaning": meaning,
        "importance_score": item.get("importance_score", 70),
    }


def validate_brief(brief, raw):
    if not isinstance(brief, dict):
        return fallback_brief(raw)

    fallback = fallback_brief(raw)
    today = datetime.now().strftime("%Y-%m-%d")
    brief["date"] = brief.get("date") or today
    brief["headline"] = brief.get("headline") or fallback["headline"]
    brief["executive_summary"] = brief.get("executive_summary") or fallback["executive_summary"]

    for key in ["big_shift", "why_now", "media_perspective", "solution_perspective"]:
        if not isinstance(brief.get(key), dict) or not brief[key].get("body"):
            brief[key] = fallback[key]

    signals = []
    for item in brief.get("signals", []):
        if isinstance(item, dict) and item.get("url"):
            signals.append(normalize_signal(item))
    if not signals:
        signals = fallback["signals"]
    brief["signals"] = signals[:6]

    actions = brief.get("actions")
    if not isinstance(actions, list) or not actions:
        actions = fallback["actions"]
    brief["actions"] = actions[:3]

    return brief


def main():
    raw_path = Path("data/raw_articles.json")
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {"articles": []}
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
                temperature=0.25,
                response_format={"type": "json_object"},
            )
            brief = validate_brief(json.loads(response.choices[0].message.content), raw)
        except Exception as error:
            print("OpenAI generation failed. fallback used:", error)
            brief = fallback_brief(raw)

    briefs_path = Path("data/briefs.json")
    all_briefs = json.loads(briefs_path.read_text(encoding="utf-8")) if briefs_path.exists() else {}
    all_briefs[brief["date"]] = brief
    briefs_path.parent.mkdir(exist_ok=True)
    briefs_path.write_text(json.dumps(all_briefs, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
