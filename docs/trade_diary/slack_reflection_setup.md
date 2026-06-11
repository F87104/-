# Slack 反省点リマインド

トレード日誌の `## 反省点` セクションを、Slack の指定スレッドに定期投稿する。

## 前提

- Slack App を作成済み（Bot Token: `xoxb-...`）
- 投稿先チャンネルに App を **Invite**
- スコープ: `chat:write`（スレッド投稿のみならこれで足りる）

## 1. Slack App 設定

1. [Slack API](https://api.slack.com/apps) → 対象 App
2. **OAuth & Permissions** → Bot Token Scopes に `chat:write` を追加
3. **Install to Workspace** → Bot User OAuth Token (`xoxb-...`) を控える
4. 投稿先チャンネルで `/invite @アプリ名`

## 2. チャンネル ID / スレッド ts の取得

### チャンネル ID

チャンネル名を右クリック → **Copy link** → URL 末尾の `C...` が channel ID。

### スレッド ts（新規スレッドを作った場合）

1. 親メッセージ（スレッドの先頭）を右クリック → **Copy link**
2. URL の `p` 以降の数字を `.` 入りに変換  
   例: `.../p1234567890123456` → `1234567890.123456`

または、Bot で初回投稿後に返ってくる `ts` を `thread_ts` に使う。

## 3. GitHub Secrets（推奨）

リポジトリ → **Settings** → **Secrets and variables** → **Actions**:

| Secret | 値 |
|---|---|
| `SLACK_BOT_TOKEN` | `xoxb-...` |
| `SLACK_CHANNEL_ID` | `C...` |
| `SLACK_THREAD_TS` | `1234567890.123456`（任意・スレッド固定時） |

`thread_ts` を空にするとチャンネル直下に投稿される。

## 4. ローカル実行

```bash
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL_ID="C..."
export SLACK_THREAD_TS="1234567890.123456"

# ドライラン（投稿せず内容確認）
python3 scripts/post_trade_reflection_to_slack.py --dry-run

# 特定エントリー
python3 scripts/post_trade_reflection_to_slack.py --entry-id E-2026-06-10-001

# 反省点があるエントリー一覧
python3 scripts/post_trade_reflection_to_slack.py --list
```

任意で `config/slack_reflection.json` を置く（example: `config/slack_reflection.example.json`）:

```bash
cp config/slack_reflection.example.json config/slack_reflection.json
# channel_id / thread_ts を編集
```

## 5. 定期実行

`.github/workflows/slack-reflection-reminder.yml` が **毎日 09:00 JST**（`timezone: Asia/Tokyo`）に実行。

- デフォルト: `entry_filter=open` のエントリーから **日替わりローテーション**
- 手動: Actions タブ → **Slack reflection reminder** → **Run workflow**

## 6. 日誌側のルール

反省点を Slack に載せたいエントリーには Markdown に `## 反省点` セクションを書く。  
現時点で対象: [2026-06-10 XAUUSD 手法外](practice/entries/2026-06-10_xauusd_offstrategy_short.md)
