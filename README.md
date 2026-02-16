# 🤖 Investment Monitor Bot - 24/7 Immortal System

Railway上で24時間365日稼働する、クラッシュしない投資ニュース監視ボット。
Claude 3.5 Sonnetによる高度な分析で、投資判断を自動通知します。

## 🎯 Features

- ✅ **絶対に落ちない設計**: 全てのエラーをキャッチして継続稼働
- ✅ **AI分析**: Claude 3.5 Sonnetによる投資判断（買い・売り・様子見）
- ✅ **重複排除**: 既読ニュースを記録し、新規のみ通知
- ✅ **Discord通知**: リッチなEmbed形式で結果を通知
- ✅ **カスタマイズ可能**: キーワード・監視間隔を環境変数で調整

## 🏗️ Architecture

```
investment-monitor-bot/
├── Procfile              # Railway起動設定
├── runtime.txt           # Python 3.11.8指定
├── requirements.txt      # 依存ライブラリ
├── .gitignore
└── src/
    ├── main.py          # 不死身のメインループ
    ├── config.py        # 環境変数管理
    ├── fetcher.py       # RSSニュース取得
    ├── analyzer.py      # Claude API分析
    └── notifier.py      # Discord通知
```

## 📦 Components

### 1. `main.py` - The Immortal Loop
- `while True` + 最上位 `try-except` で絶対クラッシュしない
- ループごとに統計情報を記録
- 起動時にDiscord通知テスト

### 2. `fetcher.py` - News Collector
- Google News & Reuters RSSから取得
- キーワードフィルタリング
- 重複URLをメモリ + ファイルで記録
- タイムアウト保護

### 3. `analyzer.py` - The Brain
- Claude 3.5 Sonnetで投資判断
- タイムアウト10秒設定
- レスポンスパース失敗時もフォールバック

### 4. `notifier.py` - The Messenger
- Discord Webhook経由で通知
- リッチEmbed（色分け・絵文字付き）
- レート制限対応

### 5. `config.py` - Configuration Manager
- 環境変数から安全に読み込み
- デフォルト値で起動可能
- センシティブ情報はマスク表示

## 🚀 Deployment Guide

### Step 1: ローカルでプロジェクトを準備

```bash
cd investment-monitor-bot

# .envファイルを作成（テスト用）
cat > .env <<EOF
ANTHROPIC_API_KEY=your_api_key_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
INTERVAL_SECONDS=60
MONITOR_KEYWORDS=半導体,決算,上方修正,NVDA,トヨタ
EOF
```

### Step 2: GitHubリポジトリを作成

```bash
# Gitを初期化
git init
git add .
git commit -m "Initial commit: Immortal Investment Monitor Bot"

# GitHub CLIでリポジトリ作成（未ログインの場合）
gh auth login

# リポジトリを作成してプッシュ
gh repo create investment-monitor-bot --public --source=. --push
```

### Step 3: Railwayでデプロイ

#### 3-1. Railwayアカウント作成
1. https://railway.app/ にアクセス
2. 「Start a New Project」→「Deploy from GitHub repo」
3. 作成した `investment-monitor-bot` を選択

#### 3-2. 環境変数を設定

Railwayのダッシュボードで「Variables」タブを開き、以下を設定：

| Variable Name         | Value (例)                                    |
|-----------------------|-----------------------------------------------|
| `ANTHROPIC_API_KEY`   | `sk-ant-api03-...`                            |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...`        |
| `INTERVAL_SECONDS`    | `60`                                          |
| `MONITOR_KEYWORDS`    | `半導体,決算,上方修正,NVDA,トヨタ,AI,EV`       |

#### 3-3. デプロイ実行

- 環境変数を保存すると自動でデプロイが開始されます
- 「Deployments」タブでログを確認
- `🤖 Investment Monitor Bot Started` がDiscordに届けば成功！

## 🔧 Configuration

### 環境変数一覧

| 変数名                | 必須 | デフォルト値                          | 説明                          |
|-----------------------|------|---------------------------------------|-------------------------------|
| `ANTHROPIC_API_KEY`   | ✅   | -                                     | Claude APIキー                |
| `DISCORD_WEBHOOK_URL` | ✅   | -                                     | Discord Webhook URL           |
| `INTERVAL_SECONDS`    | ❌   | `60`                                  | 監視間隔（秒）                |
| `CLAUDE_TIMEOUT`      | ❌   | `10`                                  | Claude APIタイムアウト（秒）  |
| `HTTP_TIMEOUT`        | ❌   | `10`                                  | HTTPリクエストタイムアウト    |
| `MONITOR_KEYWORDS`    | ❌   | `半導体,決算,上方修正,NVDA,トヨタ`    | 監視キーワード（カンマ区切り）|
| `CLAUDE_MODEL`        | ❌   | `claude-3-5-sonnet-latest`            | 使用するClaudeモデル          |

### Discord Webhook URLの取得方法

1. Discordサーバーで「サーバー設定」→「連携サービス」→「ウェブフック」
2. 「新しいウェブフック」を作成
3. 通知を受け取りたいチャンネルを選択
4. 「ウェブフックURLをコピー」

### Anthropic API Keyの取得方法

1. https://console.anthropic.com/ にアクセス
2. 「API Keys」→「Create Key」
3. キーをコピーして環境変数に設定

## 📊 Monitoring

### ログの確認

Railwayダッシュボードで「Deployments」→「View Logs」

成功時のログ例：
```
2024-02-14 23:45:00 | INFO     | 🔄 Loop #1 started
2024-02-14 23:45:02 | SUCCESS  | ✓ Fetched 3 items from RSS
2024-02-14 23:45:05 | SUCCESS  | ✓ Analysis complete: 買い
2024-02-14 23:45:06 | SUCCESS  | ✓ Discord notification sent
```

### 統計情報

ループごとに以下の統計が記録されます：
- 実行ループ数
- 発見したニュース数
- 分析済みニュース数
- エラー発生回数
- 稼働時間

## 🛠️ Troubleshooting

### Q: Botが起動しない
- Railwayのログで `ANTHROPIC_API_KEY is not set` エラーを確認
- 環境変数が正しく設定されているか確認

### Q: ニュースが通知されない
- キーワード設定を確認（`MONITOR_KEYWORDS`）
- RSSフィードが正常か確認（ログで `Fetched N items` を探す）

### Q: Claude APIがタイムアウトする
- `CLAUDE_TIMEOUT` を20秒に延長
- ログで `Claude API timeout` を確認

### Q: Discord通知が届かない
- Webhook URLが正しいか確認
- Discordサーバーの権限を確認

## 🔒 Security

- `.env` ファイルは `.gitignore` に含まれています
- APIキーは絶対にGitHubにコミットしないでください
- Railway環境変数は暗号化されて保存されます

## 📝 License

MIT License - 自由に改変・商用利用可能

## 🙏 Credits

- **Claude 3.5 Sonnet** by Anthropic
- **Railway** - PaaS Platform
- **feedparser** - RSS/Atom parser
- **loguru** - Beautiful logging

---

**Built with ❤️ by Claude Code**
