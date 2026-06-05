# B06 — TV OANDA 照合 最終判定

更新: 2026-05-31（TV CSV 再検証 — [B06_TV_RERUN_SUMMARY_ja.md](B06_TV_RERUN_SUMMARY_ja.md)）

## 結論

**B06 VIS PRECALM — Pine照合: USDJPY9・EURJPY9・GBPJPY5・AUDJPY11 = 34件執行正。Python合算37件（GBPJPY+3は研究のみ）**

| 銘柄 | 件数 | テスター照合 | 執行 |
|------|------|--------------|------|
| USDJPY | 9 | OK | **可** |
| GBPJPY | **5**（Pine正） | **TVテスター5=確定**・Python8は過検出3 | 0.25R（**Pine5件のみ執行**） |
| EURJPY | 9 | **OK（Pine CSV列 9/9）** | **可** |
| AUDJPY | 11 | OK（11/11 hour_gap=0） | **可** |

## 執行の正

- チャート: **OANDA** 4H + `h4_v_initial_shelf_breakout_strategy.pine`
- 期待値: `python_expected_b06_tv_oanda_{symbol}.csv` / 合算 `python_expected_b06_tv_oanda_all.csv`（`*_tv` 列 = テスター表示時刻 UTC+9）
- 再検証: `python3 scripts/run_b06_tv_oanda_parity.py`
- ログ: `parity_log_b06_tv_oanda_confirmed.csv`（37件）
- リスク: **0.25R**（フォワード継続）

## 使わないもの

- 旧 F87104 `python_expected_b06_vis_precalm_all.csv`（34件）

## 次フェーズ

**B07 DTS** — **退役**（2026-06-01）。B06とH4重複のため本番から外した。記録は `DECISION_b07_tv_oanda_parity.md` に残置。
