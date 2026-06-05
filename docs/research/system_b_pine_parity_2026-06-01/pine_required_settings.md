# 系統B Pine 照合 — 必須プリセット

Python CSV を正とする。**件数・signal_time が一致するまでストラテジー成績は使わない。**

## B06 VIS PRECALM

| 入力 | 値 |
|------|-----|
| チャート | H4 |
| 銘柄フィルタ | 4通貨のみ |
| H4のみ | ON |
| 2015〜2026 | ON |
| 12/15〜1/10停止 | ON |
| **TP計算** | **Signal基準(36d90e6再現)** ← CSVのtargetと一致 |
| TP RR | 1.5 |
| 棚の本数 | 6 |
| V前PRECALM | ON |

## B07 DTS SIGADX30

| 入力 | 値 |
|------|-----|
| チャート | H4 |
| 戦略 | selected_CURRENT_A30_180_SIGADX30 相当 |
| Trap age | 30–180 日 |
| Signal ADX max | 30 |
| **TP計算** | **Entry基準** ← chosen_trades の target |
| TP RR | 1.5 |

## B06↔B07 重複

同一 signal_time が9ペア。運用では B06 優先（B07はログで suppressed 可）。