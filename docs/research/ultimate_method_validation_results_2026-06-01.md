# 究極手法 v1.0 — 実検証結果（2026-06-01 再実行）

作成日: 2026-06-01  
データ: `F87104_test`（2015–2024 主期間、一部 2025–2026 OOS）  
実行環境: Python 3 + pandas 2.3.0、ローカル OHLC シンボリックリンク経由

> 本レポートは [ultimate_method_v1_2026-06-01.md](./ultimate_method_v1_2026-06-01.md) の数値根拠を、**同一マシンでスクリプトを再実行**して確認した記録です。

---

## 実行サマリー

| 層 | コード | スクリプト | 状態 | 主要指標 |
|---|---|---|---|---|
| **本番エンジン** | TB | `backtests/trendbreak_v1/run_trendbreak_v1_eval.py` | ✅ | 全モード合算 1501t / +551R（参考） |
| **本番エンジン** | TB baseline | `backtests/trendbreak_v1/run_fakeout_before_after.py` | ✅ | **461t / +191.5R / PF1.62** |
| **本番エンジン** | T5 practical | `backtests/elliott_fibo/run_t5_practical_robustness_audit.py` | ✅ | **23t / +22.4R / PF4.59**（Full strict） |
| **本番アンサンブル** | TB+T5 | `backtests/ensemble/run_trendbreak_t5_practical_combo.py` | ✅ | **411t / +219.9R / PF1.86**（6通貨・AUDJPY除外） |
| **準本番** | SQZ | `backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py` | ✅ | **43t / +24.7R / PF2.21**（GBPJPY除外） |
| **準本番** | VIS | `backtests/elliott_fibo/run_h4_v_initial_shelf_deep_dive.py` | ✅ | **34t / +15.5R / PF2.09** |
| **準本番** | LSS | `backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py` | ✅ | **8t / +15.7R / 100%WR**（core4 strict・小样本） |
| **準本番** | DTS | `backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py` | ✅ | **9t / +13.4R / 100%WR**（selected SIGADX30・小样本） |
| 参考 | T5 strict grid | `backtests/elliott_fibo/run_t5_macd_bb_vshape_validation.py` | ✅ | 92t / +56.7R / PF2.56 |
| — | T5 failure filter | `run_t5_failure_filter_validation.py` | ❌ | スクリプト未存在 |

---

## 1. 本番2柱 — TrendBreakV1 HYBRID baseline

**Pine:** `pine/production/TrendBreakV1_Final.pine`  
**出力:** `backtests/trendbreak_v1/fakeout_before_after_2015_2024/`

| 指標 | 値 |
|---|---|
| トレード数 | 461 |
| 勝率 | 36.9% |
| 総R（コスト込み） | **+191.5R** |
| PF | 1.62 |
| 最大DD | 17.95R |

**読み取り:** 現行 HYBRID（追加の騙し回避なし）が live 仕様。body60 フィルタ等は DD は縮むが総Rも減るため、本番採用は baseline のまま。

---

## 2. 本番2柱 — H4 T5 + MACD + BB（実戦用フィルタ）

**Pine:** `pine/production/h4_t5_macd_bb_live_ready.pine`  
**出力:** `backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/`

| ケース | trades | win_rate | total_r | PF | max_dd_r |
|---|---|---|---|---|---|
| Broad T5 universe | 303 | 45.5% | +47.9R | 1.31 | 13.18R |
| **Full strict practical** | **23** | **69.6%** | **+22.4R** | **4.59** | **2.15R** |
| OOS 2025–2026（Full strict） | 4 | 100% | +4.7R | inf | 0.0R |

**読み取り:** V候補は環境認識。実エントリーは stagnation / rebreak 確認後。LOO 監査では `recovery<=16`・`MACD>0`・`BB幅<=4ATR` 外しで悪化大 → 実戦フィルタは過剰適合ではない。

---

## 3. 本番アンサンブル — TrendBreak + T5（6通貨・AUDJPY除外）

**出力:** `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/`

| scenario | trades | win_rate | total_r | PF | max_dd_r |
|---|---|---|---|---|---|
| trendbreak_only | 381 | 39.4% | +194.6R | 1.79 | 11.94R |
| t5_practical_only | 30 | 60.0% | +25.3R | 3.43 | 4.35R |
| **all_trades** | **411** | **40.9%** | **+219.9R** | **1.86** | **11.94R** |
| trendbreak_priority_add_t5_when_free | 399 | 40.1% | +206.4R | 1.82 | 11.94R |
| same_symbol_first_wins | 399 | 40.9% | +212.7R | 1.86 | 11.94R |

**読み取り:** 究極手法 v1.0 の中核数値 **+219.9R / PF1.86 / 411 trades** を再現確認。T5 は取引数が少ない補助エンジン。同一通貨重複時は TrendBreak 優先が自然。

---

## 4. 準本番 tier-2（昇格待ち）

### SQZ — Market Psychology Squeeze Strict（GBPJPY除外）

**出力:** `backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/`

| label | trades | win_rate | total_r | PF | max_dd_r | oos_total_r |
|---|---|---|---|---|---|---|
| SQZ_STRICT_RR2（全通貨） | 51 | 47.1% | +18.1R | 1.65 | 4.11R | +7.9R |
| **SQZ_STRICT_RR2（GBPJPY除外）** | **43** | **53.5%** | **+24.7R** | **2.21** | **3.09R** | **+8.9R** |

**昇格条件:** Pine vs Python parity on TV、フォワード 0.25R × 30t。

### VIS — H4 V Initial Shelf Breakout（PRECALM）

**出力:** `backtests/elliott_fibo/results_2026_05_30/h4_v_initial_shelf_deep_dive/`

| label | trades | win_rate | total_r | PF | max_dd_r | oos_total_r |
|---|---|---|---|---|---|---|
| **current_selected** | **34** | **58.8%** | **+15.5R** | **2.09** | **5.11R** | **+4.9R** |

### LSS — H4 1-month low → stagnation break short

**出力:** `backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/`

| rule | trades | win_rate | total_r | PF | max_dd_r |
|---|---|---|---|---|---|
| **base_core4_strict / fixed_2R** | **8** | **100%** | **+15.7R** | **inf** | **0.0R** |

**注意:** 8t は統計的に薄い。Pine parity 未解決（`pine_parity_issue_h4_low_stag_short_2026-05-29.md`）の間は live 不可。

### DTS — D1 Trap Delayed H4 Shelf

**出力:** `backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/`

| label | trades | win_rate | total_r | PF | max_dd_r | oos_total_r |
|---|---|---|---|---|---|---|
| **selected_CURRENT_A30_180_SIGADX30** | **9** | **100%** | **+13.4R** | **inf** | **0.0R** | **+4.5R** |

**注意:** 9t。昇格前に walk-forward と TV parity が必要。

---

## 5. ゲート層（心理フィルタ）— バックテスト外

850件失敗理由研究・F1 節目追い抑制は **エンジンではなくゲート** として v1.0 に組み込み済み。

| ゲート | 根拠 | バックテスト |
|---|---|---|
| F1 節目追い抑制 | 850件 P01 節目抜け・ブレイク | F1 試験ログ（別 CSV） |
| STOP/SL 遅れ | 850件 P07/P08 | 台帳分類のみ |
| visual Pine 禁止 | 2026-06-01 USDJPY repaint 疑い | 運用ルール |

TrendBreak Pine への F1 移植は v1.1 タスク（未実装）。

---

## 6. 判定マトリクス（v1.0 時点）

| 層 | 手法 | 再実行 | 本番可 | 次アクション |
|---|---|---|---|---|
| **L1 本番** | TrendBreakV1 HYBRID | ✅ 一致 | ✅ | 通常 1R、F1 ゲート運用 |
| **L1 本番** | H4 T5 MACD BB practical | ✅ 一致 | ✅ | 0.25R フォワード → 0.5R |
| **L1 本番** | TB+T5 アンサンブル | ✅ +219.9R 再現 | ✅ | 重複時 TB 優先 |
| **L2 準本番** | SQZ strict ex-GBPJPY | ✅ PF2.21 | ⏳ | TV parity + 30t forward |
| **L2 準本番** | VIS PRECALM | ✅ PF2.09 | ⏳ | TV parity + 30t forward |
| **L2 準本番** | LSS core4 strict | ✅ 8t | ❌ | Pine parity 修正 |
| **L2 準本番** | DTS SIGADX30 | ✅ 9t | ❌ | 样本拡大 + parity |
| **禁止** | pine/visual/* | — | ❌ | 研究・表示のみ |
| **禁止** | 850件学生パターン直接エントリー | — | ❌ | ゲート・台帳用途のみ |

---

## 7. 再現手順

```bash
cd github_repo_public_top
# F87104_test がシンボリックリンクされていること

python3 backtests/trendbreak_v1/run_trendbreak_v1_eval.py
python3 backtests/trendbreak_v1/run_fakeout_before_after.py
python3 backtests/elliott_fibo/run_t5_practical_robustness_audit.py
python3 backtests/elliott_fibo/run_t5_macd_bb_vshape_validation.py
python3 backtests/ensemble/run_trendbreak_t5_practical_combo.py
python3 backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py
python3 backtests/elliott_fibo/run_h4_v_initial_shelf_deep_dive.py
python3 backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py
python3 backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py
```

---

## 8. 結論

**2026-06-01 再実行で、究極手法 v1.0 の中核数値はすべて再現された。**

- 本番2柱 + アンサンブル: **+219.9R / 411t / PF1.86**（6通貨・AUDJPY除外）
- 準本番 SQZ / VIS: PF2 前後、OOS もプラス方向
- LSS / DTS: 数値は良いが **样本 8–9t** のため live 不可

**今日から触るべきは `pine/production/` の TB + T5 のみ。**  
tier-2 はフォワード検証ログ（`docs/trade_practice_records/near_main_forward_validation_log.csv`）に 0.25R で記録し、30t 到達まで昇格しない。
