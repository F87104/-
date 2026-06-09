# トレード日誌 — トップ

> **実トレード・心理記録・受講生記録を、このフォルダに集約しています。**  
> 新しい記録を追加するときは、下の「どこに書くか」から入ってください。

---

## いま見るべき場所

| やりたいこと | 行き先 |
|---|---|
| **自分の実践トレードを見る・追加する** | 👉 [practice/](practice/) |
| **最新エントリー** | [2026-06-09 CHFJPY 買い v2.1 SQZ](practice/entries/2026-06-09_chfjpy_v21_sqz_signal_buy.md) ／ [2026-06-04 XAUUSD 売り V1](practice/entries/2026-06-04_xauusd_v1_short_signal.md) ／ [2026-06-04 GBPJPY 買い](practice/entries/2026-06-04_gbpjpy_nagekiri_signal_buy.md) ／ [2026-06-03 XAUUSD](practice/entries/2026-06-03_xauusd_h1_alert_buy.md) ／ [2026-06-01 USDJPY](practice/entries/2026-06-01_usdjpy_h4t5_signal_buy.md) |
| **リアルタイム心理を記録する** | [psychology/](psychology/) |
| **受講生トレード記録（137件・研究用）** | [archive/student/](archive/student/) |
| **トレード心理の研究ノート** | [reference/](reference/) |

---

## フォルダ構成

```
docs/trade_diary/
├── README.md                 ← このページ（トップ）
├── practice/                 ← 自分のトレード実践日誌 ⭐
│   ├── index.csv             … 一覧（全エントリー）
│   ├── entries/              … 写真付き Markdown（1トレード1ファイル）
│   └── images/               … スクリーンショット
├── psychology/               ← リアルタイム心理記録
│   ├── realtime_log_template.csv
│   └── logs/                 … 運用ログ（追記用）
├── archive/                  ← 過去データ・アーカイブ
│   └── student/              … 受講生エントリー137件
└── reference/                ← 関連研究・参照ドキュメントへのリンク
```

---

## どこに書くか

| 記録の種類 | 保存先 | 形式 |
|---|---|---|
| 実際に入ったトレード（建玉・決済・写真） | `practice/entries/` + `practice/index.csv` | Markdown + CSV |
| 入る前の心理（STOP / WAIT / CHECK） | `psychology/logs/` | CSV（テンプレ: `realtime_log_template.csv`） |
| 受講生データの分析 | `archive/student/` | 既存 CSV を参照（編集は研究ノート側） |

---

## 実践日誌エントリー一覧

| 日付 | 銘柄 | 方向 | 理由 | 詳細 |
|---|---|---|---|---|
| 2026-06-09 | CHFJPY H4 | 買い | シグナル点灯 @201.368（v2.1 SQZ） | [エントリー](practice/entries/2026-06-09_chfjpy_v21_sqz_signal_buy.md) |
| 2026-06-01 | USDJPY H4 | 買い | 4HT5シグナル点灯 | [エントリー](practice/entries/2026-06-01_usdjpy_h4t5_signal_buy.md) |
| 2026-06-03 | XAUUSD H1 | 買い | 損切り -668,492（投げ切り） | [エントリー](practice/entries/2026-06-03_xauusd_h1_alert_buy.md) |
| 2026-06-04 | XAUUSD H1 | 売り | V1ショートシグナル | [エントリー](practice/entries/2026-06-04_xauusd_v1_short_signal.md) |
| 2026-06-04 | GBPJPY H4 | 買い | 投げ切りシグナル | [エントリー](practice/entries/2026-06-04_gbpjpy_nagekiri_signal_buy.md) |

一覧 CSV: [practice/index.csv](practice/index.csv)

---

## 関連（このリポジトリ内）

| ドキュメント | 内容 |
|---|---|
| [docs/research/RESEARCH_INDEX.md](../research/RESEARCH_INDEX.md) | 全研究台帳 |
| [docs/reference/](../reference/) | FX検証研究ノート（Word） |
| [受講生つまずき研究](../research/student_stumble_clusters_research_2026-05-31.md) | 137件データの分析まとめ |
| [トレード心理 最適エントリー研究](../research/trade_psychology_optimal_entry_pattern_research_2026-05-31.md) | STOP/WAIT/CHECK プロトコル |

---

## 新規エントリーの追加手順（実践日誌）

1. `practice/images/` に写真を保存（例: `YYYY-MM-DD_<symbol>_01_alert.png`）
2. `practice/entries/` に Markdown を作成（写真を `![](../images/...)` で埋め込む）
3. `practice/index.csv` に1行追加
4. この README の「実践日誌エントリー一覧」テーブルに1行追加
