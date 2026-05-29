# H4 Low-Stag Short N-Wave Filter Study

Status: 検証途中。ユーザー提供の `Symmetric N-Wave Finder` をPythonへ移植し、H4安値停滞ショートの補助条件として使えるか確認。

## 検証した使い方

- `recent_high`: シグナル前に対称N波が高値で終わる。戻り売りの形が整った候補。
- `recent_low`: シグナル前に対称N波が安値で終わる。下落が一度出尽くした可能性。
- `latest_high_age_le_120/240/480`: 最新のN波が高値終了で、かつ検出から1から4か月相当以内。古すぎるN波を除外。
- `after_break_high`: 1ヶ月安値ブレイク後からシグナル前までに、高値終了N波がある。
- `high_after_break_no_low_24`: ブレイク後に高値終了N波があり、直近24本に安値終了N波がない。

## 重要な実装注意

- Pineのピボットは `pivLen` 本後に確定するため、Pythonでも `confirm_i <= trigger_i` のN波だけを使用。ラベル位置ではなく、確認バー基準でlookaheadを避けた。
- `minAmp` は価格固定だと通貨間比較できないため、検証では `min_leg_atr` を追加してATR換算でも確認。
- 表示用の `nonOverlap=true` は検出をかなり間引くため、戦略フィルタ用には `nonOverlap=false` も同時に検証した。
- 件数が少ないため、N波は現時点では単独エントリー条件ではなく、まず観察タグ・警戒タグ候補。

## ベースライン

| sample | nwave_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 7 | 7 | 100.00 | 85.71 | 0.00 | 10.72 | 0.00 | 1.53 | 11.50 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 18 | 18 | 100.00 | 61.11 | 0.00 | 13.61 | 0.00 | 0.76 | 2.78 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 6 | 6 | 100.00 | 83.33 | 0.00 | 8.71 | 0.00 | 1.45 | 9.18 | 0.00 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_N3_A30_B30_ATR0.5_NOOV | baseline | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## サンプル別 改善候補

PFと勝率がベースライン以上、かつカバー率20から95%の条件だけを表示。

| sample | nwave_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_240 | 26 | 9 | 34.62 | 77.78 | 35.47 | 11.73 | 5.57 | 1.30 | 6.74 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_49_240 | 26 | 9 | 34.62 | 77.78 | 35.47 | 11.73 | 5.57 | 1.30 | 6.74 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_480 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.72 | 4.56 | 1.07 | 4.51 | 2.03 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_49_480 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.72 | 4.56 | 1.07 | 4.51 | 2.03 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0.5_OV | latest_low_age_49_480 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.72 | 4.55 | 1.07 | 4.51 | 2.03 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_OV | latest_low_age_49_480 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.72 | 4.55 | 1.07 | 4.51 | 2.03 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_240 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.69 | 4.53 | 1.07 | 4.47 | 1.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_240 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.69 | 4.53 | 1.07 | 4.47 | 1.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_480 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.55 | 3.19 | 0.68 | 2.50 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_480 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.55 | 3.19 | 0.68 | 2.50 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_le_480 | 37 | 20 | 54.05 | 55.00 | 11.76 | 11.42 | 3.06 | 0.57 | 2.16 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_le_480 | 37 | 20 | 54.05 | 55.00 | 11.76 | 11.42 | 3.06 | 0.57 | 2.16 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_480 | 37 | 15 | 40.54 | 60.00 | 16.76 | 10.79 | 2.42 | 0.72 | 2.62 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_49_480 | 37 | 15 | 40.54 | 60.00 | 16.76 | 10.79 | 2.42 | 0.72 | 2.62 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_240 | 37 | 15 | 40.54 | 60.00 | 16.76 | 10.66 | 2.30 | 0.71 | 2.59 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_240 | 37 | 15 | 40.54 | 60.00 | 16.76 | 10.66 | 2.30 | 0.71 | 2.59 | 4.63 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_NOOV | no_recent_low_24 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.68 | 0.07 | 0.91 | 3.44 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_OV | no_recent_low_24 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.68 | 0.07 | 0.91 | 3.44 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_NOOV | no_recent_low_24 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.68 | 0.07 | 0.91 | 3.44 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_OV | no_recent_low_24 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.68 | 0.07 | 0.91 | 3.44 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_240 | 18 | 10 | 55.56 | 80.00 | 18.89 | 13.04 | -0.57 | 1.30 | 6.59 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_480 | 18 | 10 | 55.56 | 80.00 | 18.89 | 13.04 | -0.57 | 1.30 | 6.59 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_240 | 18 | 10 | 55.56 | 80.00 | 18.89 | 13.04 | -0.57 | 1.30 | 6.59 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_480 | 18 | 10 | 55.56 | 80.00 | 18.89 | 13.04 | -0.57 | 1.30 | 6.59 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N3_A45_B45_ATR0.5_NOOV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.62 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N3_A45_B45_ATR0.5_OV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.62 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N3_A45_B45_ATR0_NOOV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.62 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N3_A45_B45_ATR0_OV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.62 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0.5_OV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0_OV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N4_A45_B45_ATR0.5_NOOV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N4_A45_B45_ATR0.5_OV | no_recent_low_24 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.94 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_OV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_OV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |

## 本命 primary_core4_quality の候補

| sample | nwave_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_OV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_OV | no_recent_low_24 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.73 | -0.94 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_25_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_49_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_25_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_49_240 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_49_480 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.82 | -4.85 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |

## 警戒タグ候補

安値で終わるN波は、下落が一度出尽くした可能性として確認。件数が少ないものは即採用しない。

| sample | nwave_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_N3_A45_B45_ATR0.5_NOOV | recent_low_24 | 26 | 3 | 11.54 | 33.33 | -8.97 | -0.13 | -6.29 | -0.04 | 0.94 | 1.07 | CHFJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0.5_OV | recent_low_24 | 26 | 3 | 11.54 | 33.33 | -8.97 | -0.13 | -6.29 | -0.04 | 0.94 | 1.07 | CHFJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_NOOV | recent_low_24 | 26 | 3 | 11.54 | 33.33 | -8.97 | -0.13 | -6.29 | -0.04 | 0.94 | 1.07 | CHFJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_N3_A45_B45_ATR0_OV | recent_low_24 | 26 | 3 | 11.54 | 33.33 | -8.97 | -0.13 | -6.29 | -0.04 | 0.94 | 1.07 | CHFJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_N4_A45_B45_ATR0.5_OV | latest_low_age_le_240 | 26 | 6 | 23.08 | 33.33 | -8.97 | -0.23 | -6.40 | -0.04 | 0.94 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N4_A45_B45_ATR0_OV | latest_low_age_le_240 | 26 | 6 | 23.08 | 33.33 | -8.97 | -0.23 | -6.40 | -0.04 | 0.94 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N4_A45_B45_ATR0.5_NOOV | latest_low_age_le_240 | 26 | 6 | 23.08 | 33.33 | -8.97 | -0.23 | -6.39 | -0.04 | 0.95 | 2.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N4_A45_B45_ATR0_NOOV | latest_low_age_le_240 | 26 | 6 | 23.08 | 33.33 | -8.97 | -0.23 | -6.39 | -0.04 | 0.95 | 2.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0.5_NOOV | latest_low_age_le_240 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.32 | -10.68 | -1.16 | 0.00 | 1.02 | SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0.5_OV | latest_low_age_le_240 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.32 | -10.68 | -1.16 | 0.00 | 1.02 | SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0_NOOV | latest_low_age_le_240 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.32 | -10.68 | -1.16 | 0.00 | 1.02 | SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0_OV | latest_low_age_le_240 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.32 | -10.68 | -1.16 | 0.00 | 1.02 | SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0.5_NOOV | latest_low_age_le_120 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.06 | -10.42 | -1.03 | 0.00 | 1.04 | EURJPY,SILVER | oos_2025_2026,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0_NOOV | latest_low_age_le_120 | 37 | 2 | 5.41 | 0.00 | -43.24 | -2.06 | -10.42 | -1.03 | 0.00 | 1.04 | EURJPY,SILVER | oos_2025_2026,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0.5_NOOV | latest_low_age_le_240 | 37 | 5 | 13.51 | 20.00 | -23.24 | -2.40 | -10.76 | -0.48 | 0.45 | 3.36 | EURJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0_NOOV | latest_low_age_le_240 | 37 | 5 | 13.51 | 20.00 | -23.24 | -2.40 | -10.76 | -0.48 | 0.45 | 3.36 | EURJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_le_120 | 7 | 4 | 57.14 | 75.00 | -10.71 | 4.83 | -5.89 | 1.21 | 5.73 | 1.02 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0.5_OV | latest_low_age_le_120 | 7 | 4 | 57.14 | 75.00 | -10.71 | 4.83 | -5.89 | 1.21 | 5.73 | 1.02 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_le_120 | 7 | 4 | 57.14 | 75.00 | -10.71 | 4.83 | -5.89 | 1.21 | 5.73 | 1.02 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0_OV | latest_low_age_le_120 | 7 | 4 | 57.14 | 75.00 | -10.71 | 4.83 | -5.89 | 1.21 | 5.73 | 1.02 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_le_240 | 7 | 6 | 85.71 | 83.33 | -2.38 | 8.78 | -1.94 | 1.46 | 9.60 | 1.02 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0.5_OV | latest_low_age_le_240 | 7 | 6 | 85.71 | 83.33 | -2.38 | 8.78 | -1.94 | 1.46 | 9.60 | 1.02 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_le_240 | 7 | 6 | 85.71 | 83.33 | -2.38 | 8.78 | -1.94 | 1.46 | 9.60 | 1.02 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_N3_A45_B45_ATR0_OV | latest_low_age_le_240 | 7 | 6 | 85.71 | 83.33 | -2.38 | 8.78 | -1.94 | 1.46 | 9.60 | 1.02 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_all | P3_N4_A45_B45_ATR0.5_OV | latest_low_age_le_240 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.39 | -14.00 | -0.13 | 0.84 | 2.37 | GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_N4_A45_B45_ATR0_OV | latest_low_age_le_240 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.39 | -14.00 | -0.13 | 0.84 | 2.37 | GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_NOOV | recent_low_24 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.07 | -13.68 | -0.02 | 0.97 | 1.04 | AUDJPY,CHFJPY,GBPJPY | train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0.5_OV | recent_low_24 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.07 | -13.68 | -0.02 | 0.97 | 1.04 | AUDJPY,CHFJPY,GBPJPY | train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_NOOV | recent_low_24 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.07 | -13.68 | -0.02 | 0.97 | 1.04 | AUDJPY,CHFJPY,GBPJPY | train_2015_2020 |
| primary_all | P3_N3_A45_B45_ATR0_OV | recent_low_24 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.07 | -13.68 | -0.02 | 0.97 | 1.04 | AUDJPY,CHFJPY,GBPJPY | train_2015_2020 |
| primary_all | P3_N3_A30_B30_ATR0.5_NOOV | latest_low_age_le_240 | 18 | 2 | 11.11 | 50.00 | -11.11 | 0.69 | -12.92 | 0.34 | 1.53 | 1.29 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| primary_all | P3_N3_A30_B30_ATR0.5_OV | latest_low_age_le_240 | 18 | 2 | 11.11 | 50.00 | -11.11 | 0.69 | -12.92 | 0.34 | 1.53 | 1.29 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0.5_OV | latest_low_age_le_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.86 | -11.70 | 0.43 | 1.82 | 1.04 | CHFJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0.5_OV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.86 | -11.70 | 0.43 | 1.82 | 1.04 | CHFJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0_OV | latest_low_age_le_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.86 | -11.70 | 0.43 | 1.82 | 1.04 | CHFJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N3_A45_B45_ATR0_OV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.86 | -11.70 | 0.43 | 1.82 | 1.04 | CHFJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N4_A45_B45_ATR0.5_NOOV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.90 | -11.65 | 0.45 | 1.84 | 1.08 | GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N4_A45_B45_ATR0.5_OV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.90 | -11.65 | 0.45 | 1.84 | 1.08 | GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N4_A45_B45_ATR0_NOOV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.90 | -11.65 | 0.45 | 1.84 | 1.08 | GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_N4_A45_B45_ATR0_OV | latest_low_age_le_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.90 | -11.65 | 0.45 | 1.84 | 1.08 | GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | recent_low_24 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.94 | -13.73 | 0.47 | 1.90 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_OV | recent_low_24 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.94 | -13.73 | 0.47 | 1.90 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | recent_low_24 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.94 | -13.73 | 0.47 | 1.90 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_OV | recent_low_24 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.94 | -13.73 | 0.47 | 1.90 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_OV | latest_low_age_le_120 | 9 | 4 | 44.44 | 75.00 | -13.89 | 4.81 | -9.86 | 1.20 | 5.64 | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_OV | latest_low_age_le_120 | 9 | 4 | 44.44 | 75.00 | -13.89 | 4.81 | -9.86 | 1.20 | 5.64 | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0.5_NOOV | latest_low_age_le_120 | 9 | 5 | 55.56 | 80.00 | -8.89 | 6.80 | -7.87 | 1.36 | 7.55 | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N3_A45_B45_ATR0_NOOV | latest_low_age_le_120 | 9 | 5 | 55.56 | 80.00 | -8.89 | 6.80 | -7.87 | 1.36 | 7.55 | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P8_N3_A45_B45_ATR0.5_NOOV | latest_low_age_le_240 | 6 | 2 | 33.33 | 100.00 | 16.67 | 3.84 | -4.87 | 1.92 | inf | 0.00 | CHFJPY,XAUUSD | train_2015_2020 |
| primary_support60_119 | P8_N3_A45_B45_ATR0_NOOV | latest_low_age_le_240 | 6 | 2 | 33.33 | 100.00 | 16.67 | 3.84 | -4.87 | 1.92 | inf | 0.00 | CHFJPY,XAUUSD | train_2015_2020 |

## 古すぎる可能性がある条件

`latest_is_high_unbounded` は見た目の成績が良くても、検出から数百から数千本後のトレードを含むため、実戦条件にはしない。

| sample | nwave_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P5_N3_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 26 | 12 | 46.15 | 50.00 | 7.69 | 5.69 | -0.48 | 0.47 | 1.92 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P5_N3_A30_B30_ATR0_NOOV | latest_is_high_unbounded | 26 | 12 | 46.15 | 50.00 | 7.69 | 5.69 | -0.48 | 0.47 | 1.92 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A30_B30_ATR0.5_OV | latest_is_high_unbounded | 26 | 10 | 38.46 | 50.00 | 7.69 | 4.73 | -1.43 | 0.47 | 1.92 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A30_B30_ATR0_OV | latest_is_high_unbounded | 26 | 10 | 38.46 | 50.00 | 7.69 | 4.73 | -1.43 | 0.47 | 1.92 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_N3_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 26 | 10 | 38.46 | 50.00 | 7.69 | 4.72 | -1.44 | 0.47 | 1.91 | 2.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0.5_OV | latest_is_high_unbounded | 37 | 16 | 43.24 | 56.25 | 13.01 | 9.98 | 1.62 | 0.62 | 2.36 | 2.20 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0_OV | latest_is_high_unbounded | 37 | 16 | 43.24 | 56.25 | 13.01 | 9.98 | 1.62 | 0.62 | 2.36 | 2.20 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 37 | 13 | 35.14 | 53.85 | 10.60 | 7.55 | -0.82 | 0.58 | 2.23 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_N3_A30_B30_ATR0_NOOV | latest_is_high_unbounded | 37 | 13 | 35.14 | 53.85 | 10.60 | 7.55 | -0.82 | 0.58 | 2.23 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_N3_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 37 | 14 | 37.84 | 50.00 | 6.76 | 6.27 | -2.10 | 0.45 | 1.85 | 2.25 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 18 | 10 | 55.56 | 80.00 | 18.89 | 12.95 | -0.66 | 1.29 | 6.34 | 2.42 | AUDJPY,CHFJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_N4_A30_B30_ATR0.5_OV | latest_is_high_unbounded | 18 | 10 | 55.56 | 80.00 | 18.89 | 12.95 | -0.66 | 1.29 | 6.34 | 2.42 | AUDJPY,CHFJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_N4_A30_B30_ATR0_NOOV | latest_is_high_unbounded | 18 | 10 | 55.56 | 80.00 | 18.89 | 12.95 | -0.66 | 1.29 | 6.34 | 2.42 | AUDJPY,CHFJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_N4_A30_B30_ATR0_OV | latest_is_high_unbounded | 18 | 10 | 55.56 | 80.00 | 18.89 | 12.95 | -0.66 | 1.29 | 6.34 | 2.42 | AUDJPY,CHFJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P5_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 18 | 12 | 66.67 | 75.00 | 13.89 | 13.91 | 0.30 | 1.16 | 5.05 | 2.42 | AUDJPY,CHFJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 11 | 6 | 54.55 | 100.00 | 27.27 | 11.79 | -0.76 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_N4_A30_B30_ATR0.5_OV | latest_is_high_unbounded | 11 | 6 | 54.55 | 100.00 | 27.27 | 11.79 | -0.76 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_N4_A30_B30_ATR0_NOOV | latest_is_high_unbounded | 11 | 6 | 54.55 | 100.00 | 27.27 | 11.79 | -0.76 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_N4_A30_B30_ATR0_OV | latest_is_high_unbounded | 11 | 6 | 54.55 | 100.00 | 27.27 | 11.79 | -0.76 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P8_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 11 | 5 | 45.45 | 100.00 | 27.27 | 9.82 | -2.73 | 1.96 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.79 | -2.88 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_N4_A30_B30_ATR0.5_OV | latest_is_high_unbounded | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.79 | -2.88 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_N4_A30_B30_ATR0_NOOV | latest_is_high_unbounded | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.79 | -2.88 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_N4_A30_B30_ATR0_OV | latest_is_high_unbounded | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.79 | -2.88 | 1.97 | inf | 0.00 | CHFJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_N4_A30_B30_ATR0.5_NOOV | latest_is_high_unbounded | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.89 | -4.78 | 1.98 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |

## Pineでまず試す条件

1. N波設定は `pivLen=3`, `nWaves=3`, `ampTol=45`, `barTol=45`, `minLegAtr=0.5`, `nonOverlap=true` を最初の本線にする。
2. 強い観察タグは `latest_low_age_49_240`: 最新N波が安値終了で、検出から49から240本経過。広いPractical core4では 9 trades / 77.78% / +11.73R / PF 6.74。
3. 注意タグは `recent_low_24`: 最新または直近の安値終了N波が24本以内。これは下落直後すぎて戻りリスクがあり、Practical core4では 3 trades / -0.13R / PF 0.94。
4. `latest_high` 系は高値終了の戻り売りタグとして期待したが、年齢制限なしでは古すぎ、年齢制限ありでは件数不足または悪化。現段階では採用しない。
5. `support_age 60-119` は単体で強く、N波でさらに良くなるというより、別々の強い観察タグとして並べて見る。

## 暫定解釈

- まず見るべきは、`primary_core4_quality` と `practical_core4` の両方で悪化しない条件。
- `latest_is_high_unbounded` は古すぎる検出を含むため、採用するなら必ず年齢制限を付ける。
- `recent_low` 系が弱ければ、エントリー除外ではなく半ロット・注意表示から試す。
- `after_break_high` 系は件数が足りない場合、エントリー条件にせずPine表示だけに留める。

## 出力CSV

- `annotated_trades.csv`
- `rule_summary.csv`
- `../../../pine/visual/h4_nwave_filter_probe.pine`