# 系統B Pine parity 監査（Python再実行）

- B06 export vs rerun: **OK** (34 vs 34 keys)
- B07 export vs rerun: **OK** (9 vs 9 keys)
- B06↔B07 同一 signal_time: **9**

## 次（TradingView）

1. [pine_required_settings.md](pine_required_settings.md) の TP設定を必ず適用
2. [usdjpy_b06_smoke.md](usdjpy_b06_smoke.md) — 13件
3. [usdjpy_b07_smoke.md](usdjpy_b07_smoke.md) — 2件（B06と重複するOOSのみ）
4. 全件完了後 `parity_log_b06_filled.csv` の tv_match を更新
