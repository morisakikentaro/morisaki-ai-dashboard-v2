import json
from pathlib import Path
from html import escape
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))


def esc(value):
    return escape(str(value or ""))


def load_latest_brief():
    path = Path("data/briefs.json")
    if not path.exists():
        return {}
    briefs = json.loads(path.read_text(encoding="utf-8"))
    if not briefs:
        return {}
    latest_date = sorted(briefs.keys())[-1]
    return briefs[latest_date]


def paragraphs(text):
    text = str(text or "")
    parts = [p.strip() for p in text.replace("\r", "").split("\n") if p.strip()]
    if len(parts) <= 1:
        # 長文が1段落で来た場合は読みやすい長さで軽く分割
        raw = text.strip()
        if len(raw) > 420:
            sentences = raw.replace("。", "。\n").split("\n")
            chunks = []
            buf = ""
            for s in sentences:
                if not s:
                    continue
                if len(buf) + len(s) > 360:
                    chunks.append(buf)
                    buf = s
                else:
                    buf += s
            if buf:
                chunks.append(buf)
            parts = chunks
        else:
            parts = [raw] if raw else []
    return "\n".join(f"<p>{esc(p)}</p>" for p in parts)


def render_bullets(items):
    return "\n".join(f"<li>{esc(x)}</li>" for x in (items or []))


def render_actions(actions):
    html = []
    for action in actions or []:
        if isinstance(action, str):
            html.append(f"<article class='action'><h3>{esc(action)}</h3></article>")
        else:
            html.append(
                f"<article class='action'><h3>{esc(action.get('title',''))}</h3><p>{esc(action.get('body',''))}</p></article>"
            )
    return "\n".join(html)


def render_signal(item):
    source_link = f'<a href="{esc(item.get("url",""))}" target="_blank" rel="noopener">{esc(item.get("source","記事を開く"))}</a>' if item.get("url") else esc(item.get("source",""))
    return f"""
      <article class="signal">
        <div class="signal-top">
          <div>
            <div class="category">{esc(item.get("category","AI動向"))}</div>
            <h3>{esc(item.get("title_jp",""))}</h3>
          </div>
          <div class="score"><span>重要度</span><b>{esc(item.get("importance_score",""))}</b></div>
        </div>
        <div class="source-box">
          <div class="source-label">元記事タイトル</div>
          <div class="source-title">{esc(item.get("original_title",""))}</div>
          <div class="source-url">出典：{source_link}</div>
        </div>
        <div class="meaning">
          <h4>このニュースが示す意味</h4>
          <p>{esc(item.get("meaning",""))}</p>
        </div>
      </article>
    """


def main():
    brief = load_latest_brief()
    if not brief:
        brief = {
            "headline": "生成AIは、検索・実行・知識基盤の競争へ移っている",
            "executive_summary": "生成AIの動向を、経営・メディア・ソリューション視点で整理します。",
            "big_shift": {"title": "今日の大きな変化", "body": ""},
            "why_now": {"title": "なぜ今それが起きているのか", "body": ""},
            "media_perspective": {"title": "視点A：メディア視点", "body": "", "bullets": []},
            "solution_perspective": {"title": "視点B：ソリューション視点", "body": "", "bullets": []},
            "signals": [],
            "actions": [],
        }

    today_label = datetime.now(JST).strftime("%Y年%m月%d日")
    signals_html = "\n".join(render_signal(s) for s in brief.get("signals", [])[:6])

    html = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morning AI Brief</title>
  <style>
    :root{{--ink:#0f172a;--muted:#64748b;--line:#dbe3ef;--blue:#0f62fe;--blue-soft:#eef6ff;--purple:#6d28d9;--purple-soft:#f5f0ff;--green:#059669;--green-soft:#ecfdf5;--bg:#f8fbff;--shadow:0 16px 40px rgba(15,23,42,.08)}}
    *{{box-sizing:border-box}}
    html{{scroll-behavior:smooth}}
    body{{margin:0;color:var(--ink);background:radial-gradient(circle at 0% 0%,rgba(15,98,254,.10),transparent 32%),radial-gradient(circle at 100% 0%,rgba(109,40,217,.08),transparent 28%),linear-gradient(180deg,#fff 0%,var(--bg) 100%);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans","Yu Gothic",Meiryo,sans-serif;line-height:1.85}}
    .wrap{{width:min(1120px,calc(100% - 40px));margin:0 auto;padding:30px 0 42px}}
    header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}}
    h1{{font-size:46px;line-height:1.06;letter-spacing:-.055em;margin:0;color:#111936}}
    .subtitle{{margin-top:10px;color:#25324d;font-size:18px;font-weight:700}}
    .meta{{text-align:right;color:#334155;font-weight:850;white-space:nowrap}}.meta small{{display:block;color:var(--muted);font-weight:750;margin-top:4px}}
    .tabs{{display:flex;gap:10px;border-bottom:1px solid var(--line);margin-bottom:28px;overflow-x:auto}}
    .tab{{color:#17233f;text-decoration:none;font-weight:900;padding:13px 14px 14px;border-bottom:3px solid transparent;white-space:nowrap}}.tab.active{{color:var(--blue);border-color:var(--blue)}}
    .hero,.section,.perspective,.signal,.actions-panel{{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:20px;box-shadow:var(--shadow);padding:28px;margin-bottom:22px}}
    .eyebrow{{font-size:13px;color:var(--blue);font-weight:950;letter-spacing:.08em;margin-bottom:8px}}
    h2{{font-size:28px;line-height:1.35;letter-spacing:-.035em;margin:0 0 16px}}
    .hero h2{{font-size:34px}}
    p{{margin:0 0 1em;color:#263248}}
    p:last-child{{margin-bottom:0}}
    .body-text p{{font-size:16px}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
    .perspective.media{{border-color:#cfe1ff}}.perspective.solution{{border-color:#ddd3ff}}
    .perspective h2{{display:flex;align-items:center;gap:10px}}
    .icon{{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-size:22px;flex:0 0 auto}}
    .media .icon{{background:var(--blue-soft);color:var(--blue)}}.solution .icon{{background:var(--purple-soft);color:var(--purple)}}
    ul{{margin:12px 0 0;padding-left:1.2em;color:#263248}}
    li{{margin:.35em 0}}
    .signals{{display:grid;grid-template-columns:1fr;gap:16px}}
    .signal{{margin-bottom:0;padding:22px}}
    .signal-top{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}}
    .category{{display:inline-block;background:var(--blue-soft);color:var(--blue);font-size:12px;font-weight:950;padding:4px 9px;border-radius:999px;margin-bottom:8px}}
    .signal h3{{font-size:21px;line-height:1.35;letter-spacing:-.03em;margin:0}}
    .score{{min-width:76px;text-align:center;border:1px solid #e2e8f0;background:#f8fafc;border-radius:14px;padding:8px;font-weight:900}}
    .score span{{display:block;color:var(--muted);font-size:11px}}.score b{{display:block;color:#dc2626;font-size:26px;line-height:1.1}}
    .source-box{{border:1px solid #d8e6fb;background:#f8fbff;border-radius:14px;padding:13px 15px;margin:14px 0}}
    .source-label{{font-size:12px;color:var(--muted);font-weight:900}}.source-title{{font-weight:900;margin-top:2px}}
    .source-url{{font-size:13px;color:var(--muted);margin-top:3px}}.source-url a{{color:var(--blue);font-weight:850;text-decoration:none;word-break:break-all}}
    .meaning h4{{margin:0 0 5px;font-size:14px;color:#17233f}}
    .actions-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
    .action{{border:1px solid #cfe9dc;background:linear-gradient(180deg,#fff,#f4fffa);border-radius:15px;padding:18px}}
    .action h3{{margin:0 0 8px;font-size:17px;color:#047857}}
    .note{{color:var(--muted);font-size:13px;text-align:center;margin:22px 0 4px}}
    @media(max-width:900px){{.wrap{{width:min(100% - 24px,1120px);padding-top:18px}}header{{display:block}}h1{{font-size:36px}}.meta{{text-align:left;margin-top:16px}}.grid,.actions-grid{{grid-template-columns:1fr}}.hero,.section,.perspective,.signal,.actions-panel{{padding:20px}}.signal-top{{display:block}}.score{{margin-top:12px;width:86px}}}}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>Morning AI Brief</h1>
        <div class="subtitle">AI時代の変化を理解する朝の戦略メモ</div>
      </div>
      <div class="meta"><span>{esc(today_label)}</span><small>毎朝更新</small></div>
    </header>

    <nav class="tabs">
      <a class="tab active" href="#summary">全体像</a>
      <a class="tab" href="#shift">今日の変化</a>
      <a class="tab" href="#perspectives">視点別示唆</a>
      <a class="tab" href="#signals">関連ニュース</a>
      <a class="tab" href="#actions">今日の一手</a>
    </nav>

    <section class="hero" id="summary">
      <div class="eyebrow">EXECUTIVE CONTEXT</div>
      <h2>{esc(brief.get("headline",""))}</h2>
      <div class="body-text">{paragraphs(brief.get("executive_summary",""))}</div>
    </section>

    <section class="section" id="shift">
      <div class="eyebrow">BIG SHIFT</div>
      <h2>{esc((brief.get("big_shift") or {}).get("title","今日の大きな変化"))}</h2>
      <div class="body-text">{paragraphs((brief.get("big_shift") or {}).get("body",""))}</div>
    </section>

    <section class="section">
      <div class="eyebrow">WHY NOW</div>
      <h2>{esc((brief.get("why_now") or {}).get("title","なぜ今それが起きているのか"))}</h2>
      <div class="body-text">{paragraphs((brief.get("why_now") or {}).get("body",""))}</div>
    </section>

    <section class="grid" id="perspectives">
      <div class="perspective media">
        <h2><span class="icon">▤</span>{esc((brief.get("media_perspective") or {}).get("title","視点A：メディア視点"))}</h2>
        <div class="body-text">{paragraphs((brief.get("media_perspective") or {}).get("body",""))}</div>
        <ul>{render_bullets((brief.get("media_perspective") or {}).get("bullets",[]))}</ul>
      </div>
      <div class="perspective solution">
        <h2><span class="icon">△</span>{esc((brief.get("solution_perspective") or {}).get("title","視点B：ソリューション視点"))}</h2>
        <div class="body-text">{paragraphs((brief.get("solution_perspective") or {}).get("body",""))}</div>
        <ul>{render_bullets((brief.get("solution_perspective") or {}).get("bullets",[]))}</ul>
      </div>
    </section>

    <section id="signals">
      <div class="eyebrow">SOURCE SIGNALS</div>
      <h2>関連ニュース：今日の変化を示す材料</h2>
      <div class="signals">{signals_html}</div>
    </section>

    <section class="actions-panel" id="actions">
      <div class="eyebrow">NEXT ACTIONS</div>
      <h2>今日の一手</h2>
      <div class="actions-grid">{render_actions(brief.get("actions",[]))}</div>
    </section>

    <p class="note">本レポートは公開情報を基にAIが生成した要約です。投資判断・経営判断はご自身の責任で行ってください。</p>
  </div>
</body>
</html>"""

    Path("public").mkdir(exist_ok=True)
    Path("public/index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
