# 大トレンドブレイク（休眠レベル）相性検証

作成日: 2026-06-01

踏み上げ（SQZ）研究は対象外。休眠高値/安値ライン（Pine修正版と同じ窓）と既存シグナルの組み合わせを検証。

## 前提

- H4 / 窓: A=120/30, B=360/90, C=1250/190
- ブレイク余白: 0.05 ATR
- 対象通貨: XAUUSD, USDJPY, EURJPY, CHFJPY, SILVER（GBPJPY・AUDJPY除外）

## 1. 休眠ブレイク単独エントリー（ロング）

シグナル足終値で休眠高値更新 → 次足始値IN、SL=同ティア休眠安値−0.25ATR、TP=2R（Cのみ3Rも比較）。

| strategy | period | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DORM_LONG_ANY | Research_2015_2024 | 170 | 57.10 | 13.88 | 0.08 | 1.33 | 5.28 |
| DORM_LONG_A | Research_2015_2024 | 139 | 56.80 | 11.67 | 0.08 | 1.29 | 5.59 |
| DORM_LONG_B | Research_2015_2024 | 67 | 53.70 | 7.59 | 0.11 | 1.80 | 2.39 |
| DORM_LONG_C | Research_2015_2024 | 26 | 61.50 | 1.02 | 0.04 | 1.42 | 1.28 |
| DORM_LONG_C_RR3 | Research_2015_2024 | 26 | 61.50 | 1.02 | 0.04 | 1.42 | 1.28 |

## 2. TrendBreak ロング × 休眠ゲート

| gate | gate_label | trades | total_r | pf | avg_r | retention_pct |
| --- | --- | --- | --- | --- | --- | --- |
| dormant_break_signal | シグナル足で休眠高値ブレイク(any) | 101 | 79.11 | 2.37 | 0.78 | 61.20 |
| recent_dormant_48 | 直近48本以内に休眠高値ブレイク | 105 | 74.80 | 2.20 | 0.71 | 63.60 |
| recent_dormant_120 | 直近120本以内に休眠高値ブレイク | 113 | 66.47 | 1.94 | 0.59 | 68.50 |
| none | フィルタなし | 165 | 62.73 | 1.56 | 0.38 | 100.00 |
| dormant_break_C_signal | シグナル足でC(1250)休眠高値ブレイク | 8 | 11.43 | 4.62 | 1.43 | 4.80 |

## 3. アンサンブル（TB優先・T5次点・重複スキップ）

| ensemble | period | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TB+T5_baseline | all | 179 | 39.10 | 77.74 | 0.43 | 1.68 | 12.44 |
| TB+T5_baseline | Research_2015_2024 | 179 | 39.10 | 77.74 | 0.43 | 1.68 | 12.44 |
| TB+T5_recent_dormant_48 | all | 107 | 45.80 | 79.00 | 0.74 | 2.28 | 4.80 |
| TB+T5_recent_dormant_48 | Research_2015_2024 | 107 | 45.80 | 79.00 | 0.74 | 2.28 | 4.80 |
| TB+T5_dormant_C_signal | all | 8 | 62.50 | 11.43 | 1.43 | 4.62 | 2.13 |
| TB+T5_dormant_C_signal | Research_2015_2024 | 8 | 62.50 | 11.43 | 1.43 | 4.62 | 2.13 |

## 2b. T5 ロング × 休眠ゲート

| gate | trades | total_r | pf | retention_pct |
| --- | --- | --- | --- | --- |
| none | 21 | 19.42 | 4.04 | 100.00 |
| dormant_break_signal | 0 | 0.00 |  | 0.00 |
| dormant_break_C_signal | 0 | 0.00 |  | 0.00 |
| recent_dormant_48 | 3 | 2.94 | 3.78 | 14.30 |
| recent_dormant_120 | 6 | 3.63 | 2.55 | 28.60 |

T5は停滞リブレイクのため、**シグナル足での休眠同時ブレイクは0件**。ゲートはTB側に載せる。

## 採用結論（要約）

1. **第一推奨**: TrendBreakロング ＋ シグナル足で休眠高値ブレイク → +79R / PF2.37（`DECISION.md` 参照）
2. **アンサンブル**: TB+T5 ＋ 直近48本以内に休眠高値ブレイク → DD 12R→5R 付近まで改善
3. **インジケータ単独トレードは採用しない**（表示・文脈用）

## 解釈メモ

- 大トレンドブレイクは「新しい売買ルール」より **ロングの地合い確認** に効く。
- V後棚ブレイク（`h4_v_kickoff_catalyst`）との併用は別研究だが、同じ休眠窓思想。初動は TB/T5、節目はライン表示が役割分担に近い。

## 成果物

- `docs/research/dormant_synergy_validation_2026-06-01/gate_combo_summary.csv`
- `docs/research/dormant_synergy_validation_2026-06-01/dormant_standalone_summary.csv`
- `docs/research/dormant_synergy_validation_2026-06-01/ensemble_summary.csv`