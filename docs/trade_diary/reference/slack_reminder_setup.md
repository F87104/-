# Slack 反省リマインド — セットアップ

トレードの反省点を **定期的に Slack に通知**し、同じ失敗（6/3 アンカーケースなど）を繰り返さないための仕組み。

[← トレード日誌トップ](../README.md)

---

## 何が送られるか

| 項目 | 内容 |
|---|---|
| ローテーション | `docs/trade_diary/lessons/reminders.json` の 10 項目（R01〜R10） |
| 木・金 | 雇用統計週は **E05（指標前整理）** を優先 |
| 建玉 | `practice/index.csv` の `open` 行を末尾に添付 |
| リンク | 6/3 日誌・シグナル判断プロトコル・E01-E09 研究 |

### 通知スケジュール（GitHub Actions）

| 時刻 (JST) | 用途 |
|---|---|
| **08:00** | 東京セッション前の確認 |
| **20:00** | 夜間セッション前の再確認 |

---

## セットアップ手順

### 1. Slack Incoming Webhook を作る

1. [Slack API](https://api.slack.com/messaging/webhooks) でアプリを作成
2. **Incoming Webhooks** を有効化
3. 通知先チャンネル（例: `#trade-reminders`）を選び Webhook URL をコピー

### 2. GitHub リポジトリに Secret を登録

1. リポジトリ → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `SLACK_WEBHOOK_URL`
4. Value: コピーした Webhook URL

### 3. `main` にマージ

ワークフローは `.github/workflows/trade-lesson-slack-reminder.yml` に定義済み。  
`main`（またはデフォルトブランチ）に入ると cron が動き始めます。

### 4. 手動テスト

**Actions** タブ → **Trade Lesson Slack Reminder** → **Run workflow**

任意で `lesson_id` に `R03` などを指定して単発送信できます。

---

## ローカルで試す

```bash
# プレビュー（Slack には送らない）
python scripts/slack_trade_reminder.py --dry-run

# 特定の教訓だけ送る
SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...' \
  python scripts/slack_trade_reminder.py --lesson-id R03
```

### ローカル cron（任意）

GitHub Actions を使わない場合、同じスクリプトを crontab に登録:

```cron
0 8 * * * cd /path/to/repo && SLACK_WEBHOOK_URL=... python scripts/slack_trade_reminder.py
0 20 * * * cd /path/to/repo && SLACK_WEBHOOK_URL=... python scripts/slack_trade_reminder.py
```

---

## 教訓の編集

`docs/trade_diary/lessons/reminders.json` を編集すると、次回以降の通知内容が変わります。

| フィールド | 意味 |
|---|---|
| `title` | 見出し |
| `body` | 本文（反省の要点） |
| `action` | 今日やること（1 行） |
| `pattern` | E01〜E09 などの対応パターン |

新しい反省が出たら、日誌に書いたうえで JSON に 1 行追加する運用がおすすめです。

---

## 関連ファイル

| ファイル | 役割 |
|---|---|
| [scripts/slack_trade_reminder.py](../../../scripts/slack_trade_reminder.py) | 送信スクリプト |
| [lessons/reminders.json](../lessons/reminders.json) | 教訓データ |
| [signal_review_protocol.md](signal_review_protocol.md) | エントリー前判断 |
