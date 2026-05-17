import json
from pathlib import Path
from html import escape

def score_class(score):
    try:
        score = int(score)
    except Exception:
        score = 0
    if score >= 85:
        return "high"
    if score >= 70:
        return "mid"
    return "low"

def render_item(item):
    title = escape(item.get("title", ""))
    summary = escape(item.get("summary", ""))
    quote = escape(item.get("quote", ""))
    url = escape(item.get("url", ""))
    source = escape(item.get("source", ""))
    category = escape(item.get("category", ""))
    score = item.get("importance_score", 0)
    cls = score_class(score)
    link = f'<a href="{url}" target="_blank" rel="noopener">{source or "記事を開く"}</a>' if url else source
    return f"""
    <article class="item">
      <div class="item-head">
        <div>
          <div class="cat">{category}</div>
          <h3>{title}</h3>
          <p>{summary}</p>
        </div>
        <div class="score {cls}"><span>重要度</span><b>{score}</b></div>
      </div>
      <div class="quote">{quote}</div>
      <div class="source">出典・参考：{link}</div>
    </article>
    """

def list_html(items):
    return "".join(f"<li>{escape(str(x))}</li>" for x in items)

def main():
    briefs = json.loads(Path("data/briefs.json").read_text(encoding="utf-8"))
    dates = sorted(briefs.keys(), reverse=True)
    latest = dates[0] if dates else ""

    data_json = json.dumps(briefs, ensure_ascii=False)

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>森崎さん専用 AI経営ダッシュボード</title>
<style>
:root{{--bg:#eef3fb;--panel:#fff;--ink:#0f172a;--muted:#64748b;--line:#d8e0ef;--blue:#1d4ed8;--green:#15803d;--orange:#ea580c;--red:#dc2626;--shadow:0 14px 40px rgba(15,23,42,.08)}}
*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans","Yu Gothic",Meiryo,sans-serif;color:var(--ink);background:radial-gradient(circle at top left,rgba(29,78,216,.15),transparent 34%),var(--bg)}}
a{{color:var(--blue);font-weight:800;text-decoration:none}}a:hover{{text-decoration:underline}}
.app{{display:grid;grid-template-columns:270px 1fr;min-height:100vh}}
aside{{padding:22px;border-right:1px solid var(--line);background:rgba(255,255,255,.75);position:sticky;top:0;height:100vh}}
.brand{{font-weight:950;font-size:22px;letter-spacing:-.04em;line-height:1.12;margin-bottom:4px}}.owner{{font-size:13px;color:var(--muted);font-weight:800;margin-bottom:22px}}
select{{width:100%;border:1px solid var(--line);border-radius:12px;padding:10px;background:#fff;font-weight:800;margin-bottom:14px}}
.nav button{{width:100%;text-align:left;border:0;border-radius:12px;padding:11px 12px;background:transparent;cursor:pointer;font-weight:850;color:#334155;margin:3px 0}}.nav button:hover{{background:#dbeafe;color:#1e40af}}
.sidebox{{margin-top:18px;border:1px solid var(--line);border-radius:14px;padding:12px;background:#fff}}.sidebox h4{{margin:0 0 8px;font-size:13px;color:#334155}}
.tag{{display:inline-block;font-size:12px;font-weight:850;border:1px solid #e2e8f0;background:#f8fafc;padding:5px 8px;border-radius:999px;margin:3px}}
main{{padding:26px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:18px}}
.eyebrow{{font-size:13px;color:#1d4ed8;font-weight:950;letter-spacing:.06em}}h1{{font-size:42px;line-height:1;margin:4px 0 8px;letter-spacing:-.055em}}.subtitle{{color:#475569;font-weight:700}}
.status{{display:grid;gap:8px;min-width:270px}}.pill{{border:1px solid var(--line);background:#fff;border-radius:999px;padding:9px 13px;font-size:13px;font-weight:850;box-shadow:0 8px 22px rgba(15,23,42,.04)}}
.grid{{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}}.panel{{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:var(--shadow);margin-bottom:14px}}
.panel-title{{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:13px 16px;border-bottom:1px solid var(--line);font-weight:950}}.panel-title small{{color:var(--muted);font-weight:800}}.body{{padding:16px}}
.news{{display:grid;gap:12px}}.item{{border:1px solid #e5eaf3;border-radius:14px;padding:14px;background:#fff}}.item-head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}.item h3{{margin:0 0 6px;font-size:18px;letter-spacing:-.02em}}.item p{{margin:7px 0;line-height:1.65}}.cat{{font-size:12px;color:#1d4ed8;font-weight:950;margin-bottom:4px}}
.quote{{border-left:4px solid #93c5fd;background:#eff6ff;border-radius:10px;padding:10px 12px;font-weight:800;margin:9px 0}}.score{{min-width:76px;text-align:center;border-radius:12px;padding:8px;background:#f8fafc;border:1px solid #e2e8f0;font-weight:950}}.score b{{font-size:24px;display:block}}.high b{{color:var(--red)}}.mid b{{color:var(--orange)}}.low b{{color:var(--green)}}.source{{font-size:12px;color:var(--muted);font-weight:700}}
ul{{line-height:1.7;margin:0;padding-left:1.2em}}textarea{{width:100%;min-height:150px;border:1px solid var(--line);border-radius:14px;padding:12px;font:inherit;line-height:1.6;resize:vertical;background:#fff}}.btn{{border:0;border-radius:12px;background:#1d4ed8;color:white;padding:10px 13px;font-weight:900;cursor:pointer;margin-top:8px}}
@media(max-width:980px){{.app{{grid-template-columns:1fr}}aside{{position:relative;height:auto}}.grid{{grid-template-columns:1fr}}header{{display:block}}.status{{margin-top:14px}}h1{{font-size:34px}}}}
</style>
</head>
<body>
<div class="app">
<aside>
  <div class="brand">森崎さん専用<br>AI経営ダッシュボード</div>
  <div class="owner">Morning AI Brief / Auto Updated</div>
  <select id="dateSelect" onchange="render(this.value)"></select>
  <div class="nav">
    <button onclick="scrollToId('news')">重要ニュース</button>
    <button onclick="scrollToId('asahi')">朝日新聞社視点</button>
    <button onclick="scrollToId('alfasado')">アルファサード視点</button>
    <button onclick="scrollToId('actions')">経営アクション</button>
    <button onclick="scrollToId('memo')">メモ</button>
  </div>
  <div class="sidebox"><h4>追跡テーマ</h4><span class="tag">AI検索</span><span class="tag">メディアDX</span><span class="tag">CMS</span><span class="tag">RAG</span><span class="tag">AIエージェント</span></div>
</aside>
<main>
<header>
  <div>
    <div class="eyebrow">EXECUTIVE AI INTELLIGENCE</div>
    <h1 id="headline">Morning AI Brief</h1>
    <div class="subtitle" id="oneLiner"></div>
  </div>
  <div class="status">
    <div class="pill" id="datePill"></div>
    <div class="pill">⏱ 想定読了：5分</div>
    <div class="pill">🎯 Focus：朝日新聞社 / アルファサード / 経営判断</div>
  </div>
</header>
<div class="grid">
  <div>
    <section class="panel" id="news"><div class="panel-title">重要ニュース <small>クリック可能リンク付き</small></div><div class="body news" id="newsList"></div></section>
  </div>
  <div>
    <section class="panel" id="asahi"><div class="panel-title">朝日新聞社視点</div><div class="body"><ul id="asahiList"></ul></div></section>
    <section class="panel" id="alfasado"><div class="panel-title">アルファサード視点</div><div class="body"><ul id="alfasadoList"></ul></div></section>
    <section class="panel" id="actions"><div class="panel-title">今日の経営アクション</div><div class="body"><ul id="actionList"></ul></div></section>
    <section class="panel" id="memo"><div class="panel-title">森崎さんメモ <small>ブラウザ内保存</small></div><div class="body"><textarea id="memoText"></textarea><br><button class="btn" onclick="saveMemo()">保存</button></div></section>
  </div>
</div>
</main>
</div>
<script>
const briefs = {data_json};
const dates = Object.keys(briefs).sort().reverse();
const select = document.getElementById("dateSelect");
dates.forEach(d => {{
  const opt = document.createElement("option");
  opt.value = d; opt.textContent = d;
  select.appendChild(opt);
}});
function esc(s){{return String(s ?? "").replace(/[&<>"']/g,m=>({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}}[m]));}}
function scoreClass(score){{score=Number(score||0);return score>=85?"high":score>=70?"mid":"low";}}
function render(dateKey){{
  const b = briefs[dateKey];
  document.getElementById("headline").textContent = b.headline || "Morning AI Brief";
  document.getElementById("oneLiner").textContent = b.one_liner || "";
  document.getElementById("datePill").textContent = "📅 " + dateKey;
  document.getElementById("newsList").innerHTML = (b.items||[]).map(item => `
    <article class="item">
      <div class="item-head">
        <div>
          <div class="cat">${{esc(item.category)}}</div>
          <h3>${{esc(item.title)}}</h3>
          <p>${{esc(item.summary)}}</p>
        </div>
        <div class="score ${{scoreClass(item.importance_score)}}"><span>重要度</span><b>${{esc(item.importance_score)}}</b></div>
      </div>
      <div class="quote">${{esc(item.quote)}}</div>
      <div class="source">出典・参考：<a href="${{esc(item.url)}}" target="_blank" rel="noopener">${{esc(item.source || "記事を開く")}}</a></div>
    </article>
  `).join("");
  document.getElementById("asahiList").innerHTML = (b.asahi_insights||[]).map(x=>`<li>${{esc(x)}}</li>`).join("");
  document.getElementById("alfasadoList").innerHTML = (b.alfasado_insights||[]).map(x=>`<li>${{esc(x)}}</li>`).join("");
  document.getElementById("actionList").innerHTML = (b.actions||[]).map(x=>`<li>${{esc(x)}}</li>`).join("");
  document.getElementById("memoText").value = localStorage.getItem("memo-"+dateKey) || "";
}}
function scrollToId(id){{document.getElementById(id).scrollIntoView({{behavior:"smooth",block:"start"}})}}
function saveMemo(){{localStorage.setItem("memo-"+select.value, document.getElementById("memoText").value);}}
render(dates[0] || "{latest}");
</script>
</body>
</html>"""

    Path("public").mkdir(exist_ok=True)
    Path("public/index.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
