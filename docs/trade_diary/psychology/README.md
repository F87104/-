# リアルタイム心理記録（psychology）

エントリー**前**の心理ラベル（STOP / WAIT / CHECK）を記録する領域です。  
プロトコル詳細は [トレード心理 最適エントリー研究](../../research/trade_psychology_optimal_entry_pattern_research_2026-05-31.md) を参照。

[← トレード日誌トップ](../README.md)

> **シグナルが出たら:** エントリー前に [シグナルレビュー・プロトコル](../reference/signal_review_protocol.md) に従い、チャート SS を共有して判断を受ける。

---

## ファイル

| ファイル | 内容 |
|---|---|
| [realtime_log_template.csv](realtime_log_template.csv) | 記録用テンプレート（列定義の見本） |
| [logs/](logs/) | 運用中のログ CSV をここに追記 |

## 記録する列

`date_time`, `pair`, `timeframe`, `label`, `emotion`, `action`, `result`, `note`

## 使い方

1. `realtime_log_template.csv` を `logs/YYYY-MM.csv` などにコピー
2. サインが出るたびに1行追加（入ったかより「STOPで待てたか」を先に評価）
