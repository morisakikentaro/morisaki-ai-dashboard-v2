import json
from pathlib import Path
from html import escape
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))


def esc(value):
    return escape(str(value or ""))


def load_briefs():
    path = Path("data/briefs.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_item(item):
    title_jp = item.get("title_jp") or item.get("title") or item.get("original_title", "")
    original_title = item.get("original_title") or item.get("title") or title_jp
    return {
        "title_jp": title_jp,
        "original_title": original_title,
        "summary": item.get("summary", ""),
        "quote": item.get("quote", ""),
        "url": item.get("url", ""),
        "source": item.get("source", "記事を開く"),
        "category": item.get("category", "AI動向"),
        "importance_score": item.get("importance_score", ""),
        "why": item.get("why", item.get("why_important", "経営・事業戦略に影響する可能性があるため、継続的に確認したいテーマです。")),
        "impact": item.get("impact", item.get("business_impact", [])),
    }


def render_impacts(impact):
    if isinstance(impact, str):
        impact = [impact]
    if not impact:
        impact = [
            "AI検索・AI活用を前提にした情報設計が重要になる",
            "社内外のコンテンツを構造化し、AIが参照しやすくする必要がある",
            "単発導入ではなく、運用・改善・ガバナンスまで含めた体制が必要になる",
        ]
    return "\\n".join(f"<li>{esc(x)}</li>" for x in impact[:5])


def render_card(item):
    item = normalize_item(item)
    source_link = f'<a href="{esc(item["url"])}" target="_blank" rel="noopener">{esc(item["source"])}</a>' if item["url"] else esc(item["source"])
    return f"""
      <article class="news-card">
        <div class="news-head">
          <div>
            <div class="category">{esc(item["category"])}</div>
            <h3>{esc(item["title_jp"])}</h3>
          </div>
          <div class="score"><span>重要度</span><b>{esc(item["importance_score"])}</b></div>
        </div>

        <div class="source-box">
          <div class="source-label">出典</div>
          <div class="source-title">{esc(item["original_title"])}</div>
          <div class="source-url">{source_link}</div>
        </div>

        <div class="summary-block">
          <h4>何が起きているか</h4>
          <p>{esc(item["summary"])}</p>
        </div>

        <div class="summary-block">
          <h4>なぜ重要か</h4>
          <p>{esc(item["why"])}</p>
        </div>

        <div class="summary-block">
          <h4>経営インパクト</h4>
          <ul>{render_impacts(item["impact"])}</ul>
        </div>
      </article>
    """


def render_list(items):
    return "\\n".join(f"<li>{esc(x)}</li>" for x in (items or []))


def main():
    briefs = load_briefs()
    if briefs:
        latest_date = sorted(briefs.keys())[-1]
        brief = briefs[latest_date]
    else:
        brief = {
            "headline": "Morning AI Brief",
            "one_liner": "生成AIの最新動向を、経営・メディア・ソリューション視点で整理します。",
            "items": [],
            "media_insights": [],
            "solution_insights": [],
            "actions": [],
        }

    today_label = datetime.now(JST).strftime("%Y年%m月%d日")
    items = brief.get("items", [])[:6]
    if not items:
        items = [{
            "title_jp": "AI検索・AIエージェント・企業ナレッジ基盤が主要テーマに",
            "original_title": "AI search, AI agents and enterprise knowledge platforms",
            "summary": "生成AIはチャット利用から、検索、業務実行、社内外の知識活用へ広がっています。企業はAIが参照しやすい情報基盤を整える必要があります。",
            "source": "OpenAI News",
            "url": "https://openai.com/news/",
            "category": "AI動向",
            "importance_score": 80,
            "why": "AI活用の競争軸が、モデル選定から情報基盤・業務設計・運用体制へ移っているためです。",
            "impact": ["AI検索に引用されやすい情報設計が重要になる", "CMSやナレッジ基盤の価値が高まる", "AI導入支援は継続運用モデルと相性がよい"],
        }]

    media_insights = brief.get("media_insights") or brief.get("asahi_insights") or [
        "AI検索時代には、一次情報・信頼性・引用されやすい構造がメディア価値になります。",
        "記事をAIが理解しやすい構造に整えることが、検索流入や読者接点の再設計につながります。",
        "著作権、学習データ、要約表示による流入変化は継続監視が必要です。",
    ]
    solution_insights = brief.get("solution_insights") or brief.get("alfasado_insights") or [
        "CMSはWeb更新ツールから、AI-readyな企業知識基盤へ拡張できます。",
        "RAG、構造化、権限管理、履歴管理は顧客提案の中核になります。",
        "顧客の社内ナレッジ整理は、生成AI導入の入口になります。",
    ]
    actions = brief.get("actions") or [
        "AI検索・生成AI時代に必要なCMS要件を整理する。",
        "出典付きニュースカードを継続的にレビューする。",
        "AI-readyな情報基盤の提案項目を1つ追加する。",
    ]

    cards_html = "\\n".join(render_card(item) for item in items)

    html = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morning AI Brief</title>
  <style>
    :root{{--ink:#0f172a;--muted:#64748b;--line:#dbe3ef;--blue:#0f62fe;--blue-soft:#eef6ff;--purple:#6d28d9;--purple-soft:#f5f0ff;--green:#059669;--bg:#f8fbff;--shadow:0 16px 40px rgba(15,23,42,.08)}}
    *{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
    body{{margin:0;color:var(--ink);background:radial-gradient(circle at 0% 0%,rgba(15,98,254,.10),transparent 32%),radial-gradient(circle at 100% 0%,rgba(109,40,217,.08),transparent 28%),linear-gradient(180deg,#fff 0%,var(--bg) 100%);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans","Yu Gothic",Meiryo,sans-serif;line-height:1.75}}
    .wrap{{width:min(1180px,calc(100% - 40px));margin:0 auto;padding:28px 0 34px}}
    header{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:26px}}
    h1{{margin:0;font-size:46px;line-height:1.05;letter-spacing:-.055em;color:#111936}}
    .subtitle{{margin-top:8px;color:#25324d;font-size:18px;font-weight:650}}
    .meta{{text-align:right;color:#334155;font-weight:800;white-space:nowrap}} .meta small{{display:block;color:var(--muted);margin-top:4px;font-weight:750}}
    .tabs{{display:flex;gap:10px;border-bottom:1px solid var(--line);margin-bottom:28px;overflow-x:auto}}
    .tab{{color:#17233f;text-decoration:none;font-weight:900;padding:13px 14px 14px;border-bottom:3px solid transparent;white-space:nowrap}}
    .tab:hover{{color:var(--blue)}} .tab.active{{color:var(--blue);border-color:var(--blue)}}
    .panel,.news-card,.perspective,.actions{{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);padding:24px;margin-bottom:22px}}
    .panel h2,.actions h2{{margin:0 0 12px;font-size:25px;line-height:1.35;letter-spacing:-.03em}}
    .lead{{font-size:16px;color:#1f2937;margin:0;max-width:960px}}
    .news-grid{{display:grid;grid-template-columns:1fr;gap:18px}}
    .news-head{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin-bottom:14px}}
    .category{{display:inline-block;background:var(--blue-soft);color:var(--blue);font-size:12px;font-weight:950;padding:4px 9px;border-radius:999px;margin-bottom:8px}}
    .news-card h3{{margin:0;font-size:22px;line-height:1.35;letter-spacing:-.03em}}
    .score{{min-width:76px;text-align:center;border:1px solid #e2e8f0;background:#f8fafc;border-radius:14px;padding:8px;font-weight:900}}
    .score span{{display:block;color:var(--muted);font-size:11px}} .score b{{display:block;color:#dc2626;font-size:26px;line-height:1.1}}
    .source-box{{border:1px solid #d8e6fb;background:#f8fbff;border-radius:14px;padding:13px 15px;margin:14px 0}}
    .source-label{{font-size:12px;color:var(--muted);font-weight:900}} .source-title{{font-weight:900;margin-top:2px}}
    .source-url a{{color:var(--blue);font-weight:850;text-decoration:none;font-size:13px;word-break:break-all}}
    .summary-block{{margin-top:16px}} .summary-block h4{{margin:0 0 5px;font-size:14px;color:#17233f}}
    .summary-block p{{margin:0;color:#263248}} .summary-block ul{{margin:0;padding-left:1.2em;color:#263248}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px}}
    .perspective.media{{border-color:#cfe1ff}} .perspective.solution{{border-color:#ddd3ff}}
    .section-title{{display:flex;align-items:center;gap:12px;margin:0 0 18px;font-size:23px;letter-spacing:-.03em}}
    .media .section-title{{color:var(--blue)}} .solution .section-title{{color:var(--purple)}}
    .icon{{width:44px;height:44px;display:grid;place-items:center;border-radius:12px;flex:0 0 auto;font-size:23px}}
    .media .icon{{background:var(--blue-soft)}} .solution .icon{{background:var(--purple-soft)}}
    .perspective ul,.actions ul{{margin:0;padding-left:1.2em;color:#263248}}
    .actions h2{{color:var(--green)}} .links{{display:grid;gap:10px}}
    .link-card{{border:1px solid var(--line);border-radius:14px;background:#fff;padding:14px 16px}}
    .link-card a{{color:var(--blue);font-weight:900;text-decoration:none}} .link-card p{{margin:4px 0 0;color:var(--muted);font-size:13px}}
    .note{{color:var(--muted);font-size:13px;text-align:center;margin:22px 0 4px}}
    @media(max-width:900px){{.wrap{{width:min(100% - 24px,1180px);padding-top:18px}}header{{display:block}}h1{{font-size:36px}}.meta{{text-align:left;margin-top:16px}}.grid{{grid-template-columns:1fr}}.panel,.perspective,.news-card,.actions{{padding:20px}}.news-head{{display:block}}.score{{margin-top:12px;width:86px}}}}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div><h1>Morning AI Brief</h1><div class="subtitle">AI経営ダッシュボード / 出典付き解説カード版</div></div>
      <div class="meta"><span>{esc(today_label)}</span><small>毎朝7時更新</small></div>
    </header>
    <nav class="tabs" aria-label="ページ内ナビゲーション">
      <a class="tab active" href="#summary">今日のAI要約</a>
      <a class="tab" href="#news">出典付き解説</a>
      <a class="tab" href="#perspectives">視点別示唆</a>
      <a class="tab" href="#actions">今日のアクション</a>
      <a class="tab" href="#links">参考リンク</a>
    </nav>
    <section class="panel" id="summary">
      <h2>{esc(brief.get("headline", "今日のAI要約"))}</h2>
      <p class="lead">{esc(brief.get("one_liner", "生成AIの最新動向を、経営・メディア・ソリューション視点で整理します。"))}</p>
    </section>
    <section id="news" class="news-grid">{cards_html}</section>
    <section class="grid" id="perspectives">
      <div class="perspective media"><h2 class="section-title"><span class="icon">▤</span>視点A：メディア視点</h2><ul>{render_list(media_insights)}</ul></div>
      <div class="perspective solution"><h2 class="section-title"><span class="icon">△</span>視点B：ソリューション視点</h2><ul>{render_list(solution_insights)}</ul></div>
    </section>
    <section class="actions" id="actions"><h2>今日のアクション提案</h2><ul>{render_list(actions)}</ul></section>
    <section class="panel" id="links">
      <h2>参考リンク</h2>
      <div class="links">
        <div class="link-card"><a href="https://openai.com/news/" target="_blank" rel="noopener">OpenAI News</a><p>AIモデル、プロダクト、エージェント関連の公式アップデート。</p></div>
        <div class="link-card"><a href="https://blog.google/technology/ai/" target="_blank" rel="noopener">Google AI Blog</a><p>検索、AIプロダクト、研究開発に関する発表。</p></div>
        <div class="link-card"><a href="https://www.anthropic.com/news" target="_blank" rel="noopener">Anthropic News</a><p>Claude、AI安全性、エンタープライズ活用の最新情報。</p></div>
      </div>
    </section>
    <p class="note">本レポートは公開情報を基にAIが生成した要約です。投資判断・経営判断はご自身の責任で行ってください。</p>
  </div>
</body>
</html>"""
    Path("public").mkdir(exist_ok=True)
    Path("public/index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
