# 系統B B06/B07 Pine parity エクスポート

作成日: 2026-06-01

## サマリー

| case | trades | win_rate% | total_r | pf |
|------|--------|-----------|---------|-----|
| B06_all | 34 | 58.8 | 15.55 | 2.09 |
| B06_research | 29 | 55.2 | 10.61 | 1.8 |
| B06_oos | 5 | 80.0 | 4.93 | 5.84 |
| B07_all | 9 | 100.0 | 13.35 | inf |
| B07_research | 6 | 100.0 | 8.9 | inf |
| B07_oos | 3 | 100.0 | 4.46 | inf |

- B06↔B07 同一 signal_time ペア: **9**（運用では B06 優先）

## 運用

- 照合完了まで `risk_r=0.25` のみ
- 台帳: `docs/operations/system_b/system_b_forward_trade_log.csv`
