# 🚀 Railwayデプロイ完全ガイド

このガイドに従えば、5分でRailway上に不死身のBotをデプロイできます。

## 📋 事前準備

### 1. 必要なアカウント

- ✅ GitHubアカウント
- ✅ Railwayアカウント（https://railway.app/）
- ✅ Anthropic APIキー（https://console.anthropic.com/）
- ✅ Discord Webhook URL

### 2. 必要なツール

```bash
# GitHub CLIがインストールされているか確認
gh --version

# 未インストールの場合
# macOS:
brew install gh

# Linux:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update
sudo apt install gh
```

## 🔑 API Key & Webhook URL取得

### Anthropic API Key

1. https://console.anthropic.com/ にアクセス
2. 「Get API Keys」→「Create Key」
3. 名前を入力（例: `investment-bot`）
4. キーをコピー（`sk-ant-api03-...`）

### Discord Webhook URL

1. Discordで通知を受け取りたいサーバー/チャンネルを開く
2. チャンネル設定（⚙️）→「連携サービス」→「ウェブフック」
3. 「新しいウェブフック」をクリック
4. 名前を設定（例: `Investment Bot`）
5. 「ウェブフックURLをコピー」

## 📦 Step 1: プロジェクトをGitHubにプッシュ

### 1-1. GitHub CLIでログイン

```bash
# まだログインしていない場合
gh auth login

# プロンプトに従って認証
# → GitHub.com
# → HTTPS
# → Login with a web browser
```

### 1-2. Gitリポジトリを初期化

```bash
# プロジェクトディレクトリに移動
cd investment-monitor-bot

# Gitを初期化
git init

# 全ファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit: Immortal Investment Monitor Bot

- Crash-resistant architecture
- Claude 3.5 Sonnet integration
- Discord notifications
- RSS news fetching
- Duplicate filtering
"
```

### 1-3. GitHubリポジトリを作成してプッシュ

```bash
# リポジトリを作成（public）
gh repo create investment-monitor-bot --public --source=. --push

# または private で作成したい場合
gh repo create investment-monitor-bot --private --source=. --push
```

成功すると以下のように表示されます：
```
✓ Created repository yourname/investment-monitor-bot on GitHub
✓ Added remote https://github.com/yourname/investment-monitor-bot.git
✓ Pushed commits to https://github.com/yourname/investment-monitor-bot.git
```

## 🚂 Step 2: Railwayでデプロイ

### 2-1. Railwayプロジェクト作成

1. https://railway.app/ にアクセス
2. 「Start a New Project」をクリック
3. 「Deploy from GitHub repo」を選択
4. リポジトリ一覧から `investment-monitor-bot` を選択
5. 「Deploy Now」をクリック

### 2-2. 環境変数を設定

1. デプロイされたプロジェクトを開く
2. 「Variables」タブをクリック
3. 「New Variable」で以下を1つずつ追加：

#### 必須変数

```
ANTHROPIC_API_KEY
sk-ant-api03-あなたのキーをここに貼り付け
```

```
DISCORD_WEBHOOK_URL
https://discord.com/api/webhooks/あなたのWebhook URLをここに貼り付け
```

#### オプション変数（推奨）

```
INTERVAL_SECONDS
60
```

```
MONITOR_KEYWORDS
半導体,決算,上方修正,NVDA,トヨタ,AI,EV,自動運転
```

```
CLAUDE_TIMEOUT
10
```

```
HTTP_TIMEOUT
10
```

### 2-3. 自動デプロイ実行

- 環境変数を保存すると、自動的に再デプロイが始まります
- 「Deployments」タブでログを確認してください

## ✅ Step 3: 動作確認

### 3-1. ログ確認

Railwayの「Deployments」→「View Logs」で以下が表示されればOK：

```
============================================================
🤖 Investment Monitor Bot - Initializing...
============================================================
✓ All components initialized
Config(
    INTERVAL_SECONDS=60,
    CLAUDE_TIMEOUT=10,
    ...
)
🚀 Starting immortal loop...
🔄 Loop #1 started at 2024-02-14 23:45:00
```

### 3-2. Discord通知確認

起動直後にDiscordチャンネルに以下のメッセージが届きます：

```
🤖 Investment Monitor Bot Started

✅ Monitoring interval: 60s
✅ Keywords: 半導体, 決算, 上方修正, NVDA, トヨタ
✅ RSS feeds: 2

🚀 Bot is now running on Railway!
```

### 3-3. 初回ニュース通知

最大60秒（設定した間隔）後に、キーワードに合致するニュースがあれば通知されます：

```
📈 買い | エヌビディア、予想上回る決算発表

AI向け半導体の需要が予想を大きく上回り、
株価にポジティブな影響が期待されます。

判断: 買い

Powered by Claude 3.5 Sonnet
```

## 🔧 Troubleshooting

### ❌ エラー: `ANTHROPIC_API_KEY is not set`

**原因**: 環境変数が設定されていない

**解決策**:
1. Railwayの「Variables」タブを開く
2. `ANTHROPIC_API_KEY` が正しく設定されているか確認
3. 値を再入力して保存

### ❌ エラー: `Discord webhook returned 404`

**原因**: Webhook URLが間違っている、または削除された

**解決策**:
1. Discordでウェブフックを再作成
2. 新しいURLをRailwayの環境変数に設定

### ❌ ニュースが全く通知されない

**原因**: キーワードが厳しすぎる、またはRSSフィードに問題

**解決策**:
1. `MONITOR_KEYWORDS` を空にして全ニュースを受信（テスト用）
2. ログで `Fetched N items` が0でないか確認
3. キーワードを広げる（例: `株,決算,業績`）

### ❌ `Claude API timeout`

**原因**: ネットワーク遅延またはAPI過負荷

**解決策**:
1. `CLAUDE_TIMEOUT` を20に延長
2. `INTERVAL_SECONDS` を120に延長（リクエスト頻度を下げる）

## 📊 運用ベストプラクティス

### 1. 監視間隔の推奨設定

- **開発/テスト**: 30秒（素早く確認）
- **本番運用**: 60-120秒（APIコスト削減）
- **低頻度**: 300秒（5分間隔）

### 2. キーワード設定のコツ

```bash
# 広すぎる例（通知が多すぎる）
MONITOR_KEYWORDS=株,投資,経済

# 狭すぎる例（通知が来ない）
MONITOR_KEYWORDS=エヌビディアの半導体事業部門の決算上方修正

# バランスの良い例（推奨）
MONITOR_KEYWORDS=半導体,決算,上方修正,NVDA,AMD,Intel,TSMC,AI,EV,トヨタ,テスラ
```

### 3. ログの見方

```bash
# 正常動作のログパターン
🔄 Loop #N started           # ループ開始
✓ Fetched 3 items           # ニュース取得成功
✓ Analysis complete: 買い   # AI分析成功
✓ Discord notification sent # 通知成功
📊 Stats: Loops=N, ...      # 統計情報

# エラー発生時のログパターン
✗ Failed to fetch RSS       # RSS取得失敗（次のループで再試行）
Claude API timeout          # タイムアウト（次のループで再試行）
Discord rate limit hit      # レート制限（通知スキップ）
```

## 🎯 次のステップ

### カスタマイズ例

#### 1. RSS Feedを追加

`src/fetcher.py` の `RSS_FEEDS` リストに追加：

```python
self.RSS_FEEDS = [
    "https://www.reuters.com/news/archive/businessNews?format=xml",
    "https://feeds.bloomberg.com/markets/news.rss",  # 追加
    "https://yourfeed.com/rss"  # 追加
]
```

#### 2. 分析プロンプトを調整

`src/analyzer.py` の `_build_prompt()` メソッドを編集：

```python
# より詳細な分析が欲しい場合
return f"""あなたは経験豊富な投資アナリストです。
以下のニュースを分析し、投資判断と根拠を提示してください。

【ニュース】
{title}
{summary}

【分析項目】
1. 株価への影響（上昇/下降/中立）
2. 影響度（大/中/小）
3. 推奨アクション（買い/売り/様子見）
4. 理由（2-3文で詳細に）
"""
```

#### 3. 通知フォーマットをカスタマイズ

`src/notifier.py` の `send_analysis_alert()` メソッドを編集

## 🆘 サポート

問題が解決しない場合：

1. GitHubリポジトリのIssuesに報告
2. Railwayコミュニティで質問（https://discord.gg/railway）
3. Anthropic公式ドキュメント（https://docs.anthropic.com/）

---

**Happy Monitoring! 📈**
