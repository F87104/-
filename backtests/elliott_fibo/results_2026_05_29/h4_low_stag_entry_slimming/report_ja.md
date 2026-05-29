# H4 Low Stag Entry Slimming Study

Status: 検証途中。エントリー精度を上げるため、余計な短期lookback候補を削る研究。

## 結論

- 現行の `D1 RSI35-55 + H4厳選` の負け3件は、すべて `lookback=60` に集中していた。
- 90本以上のlookbackは今回の実戦本線サンプルでは負けが出ていない。
- ただし60本を全除外すると勝ちも2件落とすため、60本だけ条件を強くするのがよい。
- 推奨追加条件: `lookback != 60 or (support_age <= 24 and break_depth_atr >= 0.25)`。

## ルール比較

| sample | rule | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_no_AUD_USD | D1_RSI35_55_strict_L60_guard_age24_depth0.25 | 11 | 100.00 | 21.24 | 1.93 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | D1_RSI35_55_strict_L60_guard_age24_depth0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | D1_RSI35_55_strict_L60_guard_age24_depth0.20 | 12 | 91.67 | 20.17 | 1.68 | 19.89 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | D1_RSI35_55_strict_no_L60 | 9 | 100.00 | 17.40 | 1.93 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_core4 | D1_RSI35_55_strict_L60_guard_age24_depth0.25 | 8 | 100.00 | 15.70 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_core4 | D1_RSI35_55_strict_L60_guard_age24_depth0.30 | 8 | 100.00 | 15.70 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_core4 | D1_RSI35_55_strict_no_L60 | 7 | 100.00 | 13.72 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_core4 | D1_RSI35_55_strict_L60_guard_age24_depth0.20 | 9 | 88.89 | 14.63 | 1.63 | 14.71 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_no_AUD_USD | D1_RSI35_55_strict_current | 14 | 78.57 | 18.14 | 1.30 | 6.84 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | D1_RSI35_55_quality | 16 | 75.00 | 18.90 | 1.18 | 5.56 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_core4 | D1_RSI35_55_strict_current | 11 | 72.73 | 12.60 | 1.15 | 5.06 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_core4 | D1_RSI35_55_quality | 12 | 66.67 | 11.56 | 0.96 | 3.79 | 1.07 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| practical_no_AUD_USD | baseline | 37 | 43.24 | 8.36 | 0.23 | 1.37 | 4.76 | 4 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_core4 | baseline | 26 | 42.31 | 6.16 | 0.24 | 1.40 | 3.08 | 3 | CHFJPY,EURJPY,GBPJPY,XAUUSD |

## 60本lookback条件スイープ

| max_l60_age | min_l60_depth_atr | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | 0.25 | 11 | 100.00 | 21.24 | 1.93 | inf | 0.00 |
| 30 | 0.25 | 11 | 100.00 | 21.24 | 1.93 | inf | 0.00 |
| 36 | 0.25 | 11 | 100.00 | 21.24 | 1.93 | inf | 0.00 |
| 48 | 0.25 | 11 | 100.00 | 21.24 | 1.93 | inf | 0.00 |
| 18 | 0.25 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 18 | 0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 18 | 0.35 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 18 | 0.40 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 24 | 0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 24 | 0.35 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 24 | 0.40 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 30 | 0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 30 | 0.35 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 30 | 0.40 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 36 | 0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 36 | 0.35 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 36 | 0.40 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 48 | 0.30 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 48 | 0.35 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |
| 48 | 0.40 | 10 | 100.00 | 19.38 | 1.94 | inf | 0.00 |

## 現行D1厳選の勝敗監査

| outcome | keep_with_l60_guard | symbol | entry_time | base_r_after_cost | lookback_bars | support_age_bars | break_depth_atr | break_close_location | prev_d1_rsi14 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loss | False | GBPJPY | 2018-11-16 20:00:00 | -1.02 | 60 | 60 | 0.29 | 0.00 | 42.03 |
| loss | False | CHFJPY | 2020-01-28 12:00:00 | -1.07 | 60 | 1 | 0.20 | 0.06 | 46.11 |
| loss | False | EURJPY | 2020-04-02 12:00:00 | -1.02 | 60 | 55 | 0.15 | 0.17 | 39.12 |
| win | True | XAUUSD | 2015-06-05 12:00:00 | 1.94 | 120 | 111 | 0.21 | 0.24 | 37.17 |
| win | True | SILVER | 2015-11-03 12:00:00 | 1.77 | 120 | 1 | 0.32 | 0.37 | 42.91 |
| win | True | GBPJPY | 2016-09-19 12:00:00 | 1.97 | 90 | 84 | 0.12 | 0.08 | 40.33 |
| win | True | SILVER | 2016-11-16 12:00:00 | 1.90 | 180 | 3 | 0.22 | 0.07 | 36.23 |
| win | True | CHFJPY | 2019-04-22 16:00:00 | 1.90 | 120 | 114 | 0.18 | 0.41 | 37.61 |
| win | True | EURJPY | 2022-03-03 12:00:00 | 1.98 | 120 | 116 | 0.15 | 0.00 | 37.99 |
| win | True | SILVER | 2023-06-21 08:00:00 | 1.86 | 60 | 19 | 0.26 | 0.01 | 38.76 |
| win | True | GBPJPY | 2023-12-13 12:00:00 | 1.98 | 120 | 73 | 0.21 | 0.23 | 40.55 |
| win | True | EURJPY | 2024-07-22 04:00:00 | 1.98 | 60 | 17 | 0.59 | 0.03 | 45.91 |
| win | True | CHFJPY | 2024-11-29 00:00:00 | 1.97 | 120 | 1 | 0.26 | 0.41 | 35.58 |
| win | True | GBPJPY | 2025-01-15 08:00:00 | 1.98 | 120 | 3 | 0.42 | 0.49 | 43.44 |

## 推奨ルールの内訳

| group | value | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lookback_bars | 120 | 7 | 100.00 | 13.52 | 1.93 | inf | 0.00 |
| lookback_bars | 60 | 2 | 100.00 | 3.85 | 1.92 | inf | 0.00 |
| lookback_bars | 90 | 1 | 100.00 | 1.97 | 1.97 | inf | 0.00 |
| lookback_bars | 180 | 1 | 100.00 | 1.90 | 1.90 | inf | 0.00 |
| period | test_2021_2024 | 5 | 100.00 | 9.77 | 1.95 | inf | 0.00 |
| period | train_2015_2020 | 5 | 100.00 | 9.48 | 1.90 | inf | 0.00 |
| period | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| symbol | GBPJPY | 3 | 100.00 | 5.94 | 1.98 | inf | 0.00 |
| symbol | SILVER | 3 | 100.00 | 5.54 | 1.85 | inf | 0.00 |
| symbol | EURJPY | 2 | 100.00 | 3.96 | 1.98 | inf | 0.00 |
| symbol | CHFJPY | 2 | 100.00 | 3.87 | 1.93 | inf | 0.00 |
| symbol | XAUUSD | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |

## 実装案

1. H4安値停滞の基本条件、ADX、risk、BB幅、H4品質、前日D1 RSI 35-55 は維持。
2. `lookback=60` だけは、`support_age <= 24` かつ `break_depth_atr >= 0.25` を追加。
3. これにより、短期の浅いだまし割れや、60本に見えるだけの中途半端な戻り売りを削る。
4. 90本以上は現在の本線では残す。ここをさらに削ると件数が少なすぎる。

## 注意

- 11件・全勝は強すぎる数字なので、過信しない。これは本番化ではなく、Pine照合とフォワード監視用の厳選案。
- 60本lookbackは短期の支持線割れなので、長いレンジ割れよりもだましが増えやすい、という解釈が自然。
