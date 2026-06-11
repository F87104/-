# TB + T5 アンサンブル検証監査メモ

作成日: 2026-06-02

## 検証対象

- 名称: TrendBreakV1 HYBRID + H4 T5 MACD BB 実戦用フィルタのアンサンブル
- 対象期間: 2015-01-01 から 2024-12-31
- 推奨通貨: XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, SILVER
- 除外通貨: AUDJPY
- R列: TBは `pnl_r_after_cost`、T5は `r_after_cost` を、アンサンブル内では共通列 `r` として使用
- 資金換算: 100万円スタート、1トレード1%リスク

## 入力CSV

### TrendBreakV1 HYBRID

- 入力: `backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv`
- 使用条件: `rule_name == "baseline"`
- baseline件数: 461
- baseline通貨: AUDJPY, CHFJPY, EURJPY, GBPJPY, SILVER, USDJPY, XAUUSD
- entry_time範囲: 2015-02-11 15:00:00 から 2024-12-19 10:00:00

### H4 T5 MACD BB Practical C125

- 入力: `backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv`
- 入力CSV総件数: 114
- `period == "Research_2015_2024"` 件数: 99
- Practical C125適用後件数: 34
- Practical C125通貨: AUDJPY, CHFJPY, EURJPY, GBPJPY, SILVER, USDJPY, XAUUSD
- Practical C125 entry_time範囲: 2015-03-23 04:00:00 から 2024-08-26 08:00:00
- OOS側の同条件件数: 5

T5入力CSVの生成元は、この監査では入力CSV依存とする。アンサンブルスクリプトはT5トレードを再生成せず、上記CSVを読み込んでフィルタする。

## 実行コマンド

```bash
cd github_repo_public_top
python3 backtests/trendbreak_v1/run_fakeout_before_after.py
python3 backtests/ensemble/run_trendbreak_t5_practical_combo.py
```

T5入力CSV `baseline_final_trades_rec120_strict.csv` の生成手順は入力CSV依存。

今回の再確認環境では `python3 -c "import pandas as pd; print(pd.__version__)"` が `2.3.0+4.g1dfc98e16a` を返した。

## アンサンブル処理

実装: `backtests/ensemble/run_trendbreak_t5_practical_combo.py`

1. TB baselineを読み込み、列を `strategy, symbol, direction, signal_time, entry_time, exit_time, entry, exit, r, exit_reason` に正規化。
2. T5入力CSVから `period == "Research_2015_2024"` を抽出。
3. T5 Practical C125を適用。
   - `bb_pos <= 0.95`
   - `signal_recovery_bars <= 16`
   - `trigger_type == "rebreak"` かつ `macd_hist_slope3 <= 0.03` を除外
   - `trigger_type == "rebreak"` かつ `bb_pos > 0.95` を除外。ただし直前条件 `bb_pos <= 0.95` により、この分岐は実質的に重複条件。
4. 5シナリオを作成。
   - `trendbreak_only`
   - `t5_practical_only`
   - `all_trades`
   - `trendbreak_priority_add_t5_when_free`
   - `same_symbol_first_wins`
5. 全通貨版と推奨6通貨版を集計。

## シナリオ定義

- `trendbreak_only`: TB baselineのみ。
- `t5_practical_only`: T5 Practical C125のみ。
- `all_trades`: TBとT5をすべて合算。同一通貨・同時期の重複除去なし。
- `trendbreak_priority_add_t5_when_free`: TBを全採用し、同一通貨でTBポジションと保有期間が重ならないT5だけ追加。
- `same_symbol_first_wins`: TBとT5をentry_time順に並べ、同一通貨で保有期間が重なる後続トレードを除外。同時刻はTB優先。

## 推奨6通貨結果

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| trendbreak_only | 381 | 39.37% | 194.61R | 0.511R | 1.794 | 11.94R | 11 |
| t5_practical_only | 30 | 60.00% | 25.33R | 0.844R | 3.431 | 4.35R | 5 |
| all_trades | 411 | 40.88% | 219.94R | 0.535R | 1.861 | 11.94R | 11 |
| trendbreak_priority_add_t5_when_free | 399 | 40.10% | 206.42R | 0.517R | 1.816 | 11.94R | 11 |
| same_symbol_first_wins | 399 | 40.85% | 212.73R | 0.533R | 1.858 | 11.94R | 11 |

## 全通貨結果

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| trendbreak_only | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13 |
| t5_practical_only | 34 | 61.76% | 29.20R | 0.859R | 3.555 | 4.35R | 5 |
| all_trades | 495 | 38.59% | 220.73R | 0.446R | 1.693 | 14.02R | 13 |
| trendbreak_priority_add_t5_when_free | 481 | 37.63% | 204.32R | 0.425R | 1.646 | 14.02R | 13 |
| same_symbol_first_wins | 481 | 38.67% | 215.59R | 0.448R | 1.698 | 14.02R | 13 |

## TrendBreak優先 + T5追加時の内訳

### 戦略別

| strategy | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| TrendBreakV1 | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13 |
| H4 T5 MACD BB | 20 | 55.00% | 12.79R | 0.640R | 2.412 | 3.02R | 3 |

### 通貨別

| symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | 79 | 45.57% | 58.15R | 0.736R | 2.294 | 6.19R | 6 |
| GBPJPY | 64 | 42.19% | 40.08R | 0.626R | 2.050 | 6.16R | 6 |
| SILVER | 64 | 43.75% | 36.62R | 0.572R | 1.865 | 6.41R | 5 |
| USDJPY | 68 | 38.24% | 31.88R | 0.469R | 1.737 | 9.37R | 9 |
| CHFJPY | 67 | 37.31% | 27.29R | 0.407R | 1.616 | 9.37R | 10 |
| EURJPY | 57 | 31.58% | 12.39R | 0.217R | 1.309 | 7.41R | 7 |
| AUDJPY | 82 | 25.61% | -2.09R | -0.026R | 0.967 | 17.95R | 12 |

## T5 Practical C125 トリガー別

| trigger_type | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| stagnation | 10 | 70.00% | 10.84R | 1.084R | 4.529 | 1.01R | 2 |
| rebreak | 16 | 50.00% | 9.53R | 0.596R | 2.502 | 1.03R | 2 |
| stagnation+rebreak | 8 | 75.00% | 8.82R | 1.103R | 5.383 | 1.01R | 1 |

## 出力ファイル

- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/overall_all_symbols.csv`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/overall_recommended_ex_audjpy.csv`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/all_trades_trades.csv`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/trendbreak_priority_add_t5_when_free_trades.csv`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/same_symbol_first_wins_trades.csv`
- `backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/t5_practical_only_trades.csv`

## 監査上の注意

- T5入力CSVの生成過程は、この報告では入力CSV依存。
- `all_trades` は重複ポジションを許容するため、同一通貨の同時保有制限を置く実運用とは異なる可能性がある。
- `trendbreak_priority_add_t5_when_free` と `same_symbol_first_wins` は同一通貨内の重複だけを制御する。別通貨の同時ポジション制限はこのスクリプトでは制御していない。
- `linear_final_jpy_1pct` と `compound_final_jpy_1pct` は100万円・1%リスク換算の参考値であり、実運用の約定差やスプレッド変動は入力CSV依存。

