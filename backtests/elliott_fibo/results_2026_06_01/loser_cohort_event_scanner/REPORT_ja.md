# 敗者コホート・イベントスキャナー（2026-06-01）

エントリーなし。各イベント後 **12/24/48/72 H4本** の MFE/MAE/fwd（ATR単位）のみ記録。

## 設計原則

- 最適化しない（SQZ/T5/Trap は既存固定パラメータ）
- 勝率ではなく **cascade方向への median MFE** と **P(MFE48≥3ATR)**
- `RANDOM_H4_BAR` は同数サンプルの対照

## イベント別サマリー（全期間）

| event_type | cascade_direction | events | median_mfe_48_atr | median_mae_48_atr | median_fwd_48_atr | pct_mfe48_ge_3 | pct_hit_1atr_first_24 | pct_mae48_ge_2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3_break_fail_long_trap | down | 843 | 3.03 | 3.33 | -0.44 | 50.40 | 48.40 | 67.50 |
| E4_range_break_up | up | 515 | 3.48 | 2.83 | 0.52 | 54.80 | 51.10 | 62.30 |
| RANDOM_H4_BAR | up | 487 | 3.33 | 2.86 | 0.47 | 54.40 | 48.00 | 64.50 |
| E4_range_break_down | down | 422 | 3.03 | 3.18 | -0.33 | 51.40 | 48.10 | 62.10 |
| E2_v_reaccel | up | 287 | 3.09 | 3.08 | 0.19 | 50.90 | 53.00 | 64.10 |
| E3b_d1_break_fail_long | down | 197 | 2.99 | 3.22 | -0.79 | 49.20 | 52.30 | 67.50 |
| E1_short_squeeze_cascade | up | 165 | 3.47 | 2.41 | 1.11 | 52.70 | 50.90 | 59.40 |
| E1_chain_second_shelf | up | 20 | 2.88 | 3.25 | 0.42 | 45.00 | 55.00 | 60.00 |

## 期間別（Research vs OOS）

| period | event_type | events | median_mfe_48_atr | median_mae_48_atr | median_fwd_48_atr | pct_mfe48_ge_3 | pct_hit_1atr_first_24 | pct_mae48_ge_2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Research_2015_2024 | E3_break_fail_long_trap | 745 | 3.01 | 3.37 | -0.44 | 50.10 | 47.10 | 67.20 |
| Research_2015_2024 | RANDOM_H4_BAR | 450 | 3.20 | 2.94 | 0.33 | 52.90 | 48.70 | 66.70 |
| Research_2015_2024 | E4_range_break_up | 440 | 3.57 | 2.77 | 0.52 | 55.90 | 50.20 | 61.60 |
| Research_2015_2024 | E4_range_break_down | 377 | 3.03 | 3.12 | -0.25 | 51.20 | 48.50 | 60.50 |
| Research_2015_2024 | E2_v_reaccel | 251 | 3.41 | 2.90 | 0.31 | 53.00 | 54.60 | 62.20 |
| Research_2015_2024 | E3b_d1_break_fail_long | 162 | 3.34 | 3.12 | -0.50 | 54.30 | 52.50 | 64.80 |
| Research_2015_2024 | E1_short_squeeze_cascade | 155 | 3.29 | 2.37 | 1.11 | 52.30 | 53.50 | 57.40 |
| OOS_2025_2026 | E3_break_fail_long_trap | 98 | 3.41 | 3.18 | -0.64 | 53.10 | 58.20 | 69.40 |
| OOS_2025_2026 | E4_range_break_up | 75 | 2.74 | 3.09 | 0.42 | 48.00 | 56.00 | 66.70 |
| OOS_2025_2026 | E4_range_break_down | 45 | 3.03 | 3.68 | -0.63 | 53.30 | 44.40 | 75.60 |
| OOS_2025_2026 | RANDOM_H4_BAR | 37 | 4.84 | 1.67 | 2.80 | 73.00 | 40.50 | 37.80 |
| OOS_2025_2026 | E2_v_reaccel | 36 | 2.01 | 3.63 | -0.69 | 36.10 | 41.70 | 77.80 |
| OOS_2025_2026 | E3b_d1_break_fail_long | 35 | 2.02 | 4.42 | -2.32 | 25.70 | 51.40 | 80.00 |
| Research_2015_2024 | E1_chain_second_shelf | 20 | 2.88 | 3.25 | 0.42 | 45.00 | 55.00 | 60.00 |
| OOS_2025_2026 | E1_short_squeeze_cascade | 10 | 3.90 | 3.57 | 1.96 | 60.00 | 10.00 | 90.00 |

## 解釈ガイド

| event_type | 主な敗者 | cascade |
|---|---|---|
| E1_short_squeeze_cascade | ショート・戻り売り | up |
| E2_v_reaccel | V否定後の売り残り | up |
| E3_break_fail_long_trap | 高値ブレイク買い | down |
| E4_range_break_* | レンジ両建て | up/down |

## 再現

```bash
python3 backtests/elliott_fibo/run_loser_cohort_event_scanner.py
```

全イベント件数: **2936**