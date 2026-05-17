# 森崎さん専用 AI経営ダッシュボード 自動更新構成

毎朝、生成AIニュースを収集し、森崎さん向けに要約・スコアリングして、HTMLダッシュボードとして公開するためのスターター構成です。

## 構成

```text
.
├── .github/workflows/daily.yml   # 毎朝の自動実行
├── src/fetch_news.py              # RSS / Web から記事候補を収集
├── src/generate_brief.py          # AIで要約・分類・スコアリング
├── src/render_dashboard.py        # HTML生成
├── data/briefs.json               # 日次ブリーフの蓄積
├── public/index.html              # 公開用HTML
├── requirements.txt
└── README.md
```

## 実現できること

- 毎朝 7:00 JST に自動実行
- 生成AI、AI検索、メディア、CMS、RAG、AIエージェント関連の記事を収集
- 朝日新聞社視点 / アルファサード視点 / 経営視点で要約
- 重要度、関連度をスコア化
- HTMLダッシュボードを生成
- GitHub Pages で閲覧
- 過去日付をアーカイブ表示

## 推奨構成

### レベル1: GitHub Pages
一番シンプルです。

1. GitHubに新規リポジトリを作成
2. このフォルダ一式をpush
3. GitHubリポジトリの Settings → Pages で `GitHub Actions` を選択
4. Repository Secrets に `OPENAI_API_KEY` を追加
5. 毎朝自動更新

### レベル2: Cloudflare Pages
表示速度や独自ドメイン運用を重視するならこちら。

### レベル3: 社内運用
サーバーや社内Gitに置いて、cronで実行する形も可能です。

## GitHub Secrets

以下を設定してください。

```text
OPENAI_API_KEY=sk-...
```

任意で追加できます。

```text
SLACK_WEBHOOK_URL=...
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

## 収集対象の調整

`src/fetch_news.py` の `RSS_FEEDS` を編集してください。

初期値では以下を想定しています。

- OpenAI
- Google AI
- Anthropic
- Microsoft
- Nieman Lab
- Columbia Journalism Review
- 経産省 AI政策
- デジタル庁
- PR TIMES AI関連検索RSS

## 注意

この雛形は、まず「毎朝HTMLを生成して公開する」ための実装例です。
本番では、記事本文取得、重複除去、著作権配慮、引用量制御、ログ保存、通知連携を調整してください。
