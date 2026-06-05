# B06 — TV OANDA 照合 最終判定

更新: 2026-06-05

## 結論

**B06 VIS PRECALM — 4通貨・37件すべて TV 照合完了。`pine_ready: yes`**

| 銘柄 | 件数 | テスター照合 | 執行 |
|------|------|--------------|------|
| USDJPY | 9 | OK | **可** |
| GBPJPY | 8 | OK | **可** |
| EURJPY | 9 | OK | **可** |
| AUDJPY | 11 | OK（11/11 hour_gap=0） | **可** |

## 執行の正

- チャート: **OANDA** 4H + `h4_v_initial_shelf_breakout_strategy.pine`
- 期待値: `python_expected_b06_tv_oanda_{symbol}.csv`（`*_tv` 列 = テスター表示時刻）
- ログ: `parity_log_b06_tv_oanda_confirmed.csv`（37件）
- リスク: **0.25R**（フォワード継続）

## 使わないもの

- 旧 F87104 `python_expected_b06_vis_precalm_all.csv`（34件）

## 次フェーズ

**B07 DTS** — TV-OHLC **12件** baseline 済み（`DECISION_b07_tv_oanda_parity.md`）。Pine 照合中。B06重複は **B06優先**。
