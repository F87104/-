# H1 Lower-High Rebreak Filter Study

Status: 検証途中。H4安値停滞ショートに対して、H1で戻り高値切り下げと再下落が確認できるかを検証。

## 検証した使い方

- `lh_confirm`: H1で 高値 -> 安値 -> 低い高値 が確定。
- `lh_rebreak`: その後、H1終値が中間安値を下抜き。戻り売り再開の確認。
- `after_break_full`: H1の最初の戻り高値から再下落までが、H4安値ブレイク後に作られたもの。
- `after_break_confirm`: H1イベントの確定が、H4安値ブレイク後からH4シグナル前までに起きたもの。

## 重要な実装注意

- H1ピボットは右側 `pivot_len` 本後に確定するため、確定済みイベントだけを使用。
- H4の `break_i` をH4足の日時へ戻し、H1側ではその時刻以降のイベントだけを検証。
- `lh_rebreak` は、低い高値の確定後 `max_rebreak_bars` 本以内に中間安値を終値で下抜く必要がある。

## ベースライン

| sample | lh_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 7 | 7 | 100.00 | 85.71 | 0.00 | 10.72 | 0.00 | 1.53 | 11.50 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 18 | 18 | 100.00 | 61.11 | 0.00 | 13.61 | 0.00 | 0.76 | 2.78 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 6 | 6 | 100.00 | 83.33 | 0.00 | 8.71 | 0.00 | 1.45 | 9.18 | 0.00 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | baseline | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## サンプル別 改善候補

PFと勝率がベースライン以上、かつ3件以上の条件だけを表示。

| sample | lh_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_LOW0.25_SW1_BUF0.05_EXP12 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0.05_EXP24 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0.05_EXP48 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0_EXP12 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0_EXP24 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0_EXP48 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P2_LOW0.25_SW0.5_BUF0.05_EXP12 | lh_confirm_after_break_full | 26 | 17 | 65.38 | 52.94 | 10.63 | 9.47 | 3.30 | 0.56 | 2.14 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P2_LOW0.25_SW0.5_BUF0.05_EXP24 | lh_confirm_after_break_full | 26 | 17 | 65.38 | 52.94 | 10.63 | 9.47 | 3.30 | 0.56 | 2.14 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW1_BUF0.05_EXP48 | lh_rebreak_24 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.80 | 3.43 | 0.69 | 2.57 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW1_BUF0_EXP48 | lh_rebreak_24 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.80 | 3.43 | 0.69 | 2.57 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0_SW1_BUF0.05_EXP48 | lh_rebreak_24 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.80 | 3.43 | 0.69 | 2.57 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0_SW1_BUF0_EXP48 | lh_rebreak_24 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.80 | 3.43 | 0.69 | 2.57 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_rebreak_24 | 37 | 20 | 54.05 | 55.00 | 11.76 | 11.63 | 3.27 | 0.58 | 2.21 | 2.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_rebreak_24 | 37 | 20 | 54.05 | 55.00 | 11.76 | 11.63 | 3.27 | 0.58 | 2.21 | 2.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_rebreak_48 | 37 | 32 | 86.49 | 46.88 | 3.63 | 10.86 | 2.49 | 0.34 | 1.60 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_48 | 37 | 32 | 86.49 | 46.88 | 3.63 | 10.86 | 2.49 | 0.34 | 1.60 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0.05_EXP12 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0.05_EXP24 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0.05_EXP48 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP12 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP48 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.25_SW0.5_BUF0.05_EXP12 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOW0.25_SW0.5_BUF0.05_EXP24 | no_lh_rebreak_after_break_full | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.1_SW1_BUF0.05_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.1_SW1_BUF0_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.25_SW0.5_BUF0.05_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.25_SW0.5_BUF0_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.25_SW1_BUF0.05_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_LOW0.25_SW1_BUF0_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0.05_EXP48 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0_EXP12 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0_EXP24 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW1_BUF0_EXP48 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.25_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.25_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP48 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP48 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.25_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.25_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |

## Pineでまず試す候補

成績順だけではなく、実装しやすさと売買ロジックの自然さで候補を整理。

| candidate | sample | lh_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A 実戦本線: Core4でH4ブレイク後のH1戻り高値切り下げ | practical_core4 | P3_LOW0.25_SW1_BUF0_EXP24 | lh_confirm_after_break_full | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| B 実戦補助: Core4で直近24本以内のH1再下落 | practical_core4 | P2_LOW0.1_SW1_BUF0_EXP48 | lh_rebreak_24 | 26 | 12 | 46.15 | 58.33 | 16.03 | 8.56 | 2.40 | 0.71 | 2.63 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| C 広め確認: AUD/USD除外で直近24本以内のH1再下落 | practical_no_AUD_USD | P2_LOW0.1_SW1_BUF0_EXP48 | lh_rebreak_24 | 37 | 17 | 45.95 | 58.82 | 15.58 | 11.80 | 3.43 | 0.69 | 2.57 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| D Primary厳選: Core4品質条件でH1切り下げ確認 | primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| E Primary広め: 直近72本以内のH1再下落 | primary_all | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_72 | 18 | 14 | 77.78 | 71.43 | 10.32 | 14.81 | 1.20 | 1.06 | 4.31 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |

## Pine化時の本線案

- H4の既存シグナルを先に作る。
- H4の安値ブレイク後に、H1で `高値 -> 安値 -> 低い高値` が確定しているかを見る。
- まずは `pivot=3`, `切り下げ>=0.25ATR`, `左右の波>=1ATR` を本線にする。
- H1の中間安値再下落はエントリー必須ではなく、最初は確認タグとして使う。必須化するとPFは上がるが件数と総Rが削られやすい。
- `no_lh_rebreak` 系は数字が良く見える箇所があるが、売り根拠として逆向きなので実装本線にはしない。

## H1 lower-high 系だけを見る

| sample | lh_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_LOW0.1_SW1_BUF0.05_EXP24 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW1_BUF0.05_EXP48 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW1_BUF0_EXP12 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW1_BUF0_EXP24 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW1_BUF0_EXP48 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0.05_EXP24 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0.05_EXP48 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.25_SW1_BUF0_EXP12 | lh_rebreak_after_break_full | 26 | 4 | 15.38 | 75.00 | 32.69 | 4.93 | -1.24 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0.05_EXP24 | lh_rebreak_after_break_full | 37 | 4 | 10.81 | 75.00 | 31.76 | 4.93 | -3.44 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0.05_EXP48 | lh_rebreak_after_break_full | 37 | 4 | 10.81 | 75.00 | 31.76 | 4.93 | -3.44 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0_EXP12 | lh_rebreak_after_break_full | 37 | 4 | 10.81 | 75.00 | 31.76 | 4.93 | -3.44 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0_EXP24 | lh_rebreak_after_break_full | 37 | 4 | 10.81 | 75.00 | 31.76 | 4.93 | -3.44 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0_EXP48 | lh_rebreak_after_break_full | 37 | 4 | 10.81 | 75.00 | 31.76 | 4.93 | -3.44 | 1.23 | 5.86 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW1_BUF0.05_EXP12 | lh_rebreak_after_break_full | 37 | 3 | 8.11 | 66.67 | 23.42 | 2.95 | -5.42 | 0.98 | 3.91 | 1.01 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW0.5_BUF0.05_EXP12 | lh_rebreak_after_break_full | 37 | 5 | 13.51 | 60.00 | 16.76 | 3.90 | -4.46 | 0.78 | 2.92 | 2.03 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.25_SW0.5_BUF0.05_EXP24 | lh_rebreak_after_break_full | 37 | 5 | 13.51 | 60.00 | 16.76 | 3.90 | -4.46 | 0.78 | 2.92 | 2.03 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0.05_EXP24 | lh_rebreak_after_break_confirm | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0.05_EXP24 | lh_rebreak_48 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0.05_EXP48 | lh_rebreak_after_break_confirm | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0.05_EXP48 | lh_rebreak_48 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0_EXP24 | lh_rebreak_after_break_confirm | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0_EXP24 | lh_rebreak_48 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0_EXP48 | lh_rebreak_after_break_confirm | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P2_LOW0.25_SW1_BUF0_EXP48 | lh_rebreak_48 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.87 | -2.85 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0_EXP12 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.25_SW0.5_BUF0.05_EXP12 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P2_LOW0.25_SW0.5_BUF0.05_EXP24 | lh_rebreak_after_break_full | 18 | 3 | 16.67 | 100.00 | 38.89 | 5.86 | -7.75 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0_EXP12 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.25_SW0.5_BUF0.05_EXP12 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P2_LOW0.25_SW0.5_BUF0.05_EXP24 | lh_rebreak_after_break_full | 11 | 3 | 27.27 | 100.00 | 27.27 | 5.86 | -6.70 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0.05_EXP48 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.1_SW1_BUF0_EXP48 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.25_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P2_LOW0.25_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_full | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0.05_EXP48 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0_EXP12 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW0.5_BUF0_EXP48 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW1_BUF0.05_EXP12 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P2_LOW0.1_SW1_BUF0.05_EXP24 | lh_confirm_after_break_confirm | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## まず見る標準候補

`pivot=3`, `切り下げ>=0.1ATR`, `左右の波>=0.5ATR`, `再下落期限24本`, `buffer=0`。

| sample | lh_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 26 | 16 | 61.54 | 50.00 | 7.69 | 7.49 | 1.33 | 0.47 | 1.91 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 26 | 5 | 19.23 | 60.00 | 17.69 | 3.90 | -2.26 | 0.78 | 2.92 | 2.03 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_confirm | 26 | 25 | 96.15 | 40.00 | -2.31 | 4.19 | -1.97 | 0.17 | 1.27 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_confirm | 26 | 17 | 65.38 | 47.06 | 4.75 | 6.49 | 0.33 | 0.38 | 1.70 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_no_rebreak | 26 | 8 | 30.77 | 25.00 | -17.31 | -2.30 | -8.47 | -0.29 | 0.63 | 5.14 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_24 | 26 | 10 | 38.46 | 40.00 | -2.31 | 1.65 | -4.51 | 0.16 | 1.26 | 2.07 | EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_48 | 26 | 19 | 73.08 | 36.84 | -5.47 | 1.41 | -4.75 | 0.07 | 1.11 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | no_lh_rebreak_after_break_full | 26 | 21 | 80.77 | 38.10 | -4.21 | 2.26 | -3.90 | 0.11 | 1.17 | 3.20 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 37 | 23 | 62.16 | 43.48 | 0.24 | 5.34 | -3.02 | 0.23 | 1.38 | 6.03 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 37 | 6 | 16.22 | 50.00 | 6.76 | 2.84 | -5.52 | 0.47 | 1.92 | 2.03 | EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_confirm | 37 | 35 | 94.59 | 40.00 | -3.24 | 4.53 | -3.84 | 0.13 | 1.20 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_confirm | 37 | 27 | 72.97 | 44.44 | 1.20 | 6.89 | -1.47 | 0.26 | 1.42 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_no_rebreak | 37 | 9 | 24.32 | 33.33 | -9.91 | -0.50 | -8.86 | -0.06 | 0.92 | 5.14 | CHFJPY,EURJPY,GBPJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_24 | 37 | 15 | 40.54 | 46.67 | 3.42 | 4.88 | -3.48 | 0.33 | 1.57 | 2.07 | EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_48 | 37 | 28 | 75.68 | 42.86 | -0.39 | 6.04 | -2.33 | 0.22 | 1.36 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOW0.1_SW0.5_BUF0_EXP24 | no_lh_rebreak_after_break_full | 37 | 31 | 83.78 | 41.94 | -1.31 | 5.52 | -2.84 | 0.18 | 1.28 | 3.70 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | baseline | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 11 | 7 | 63.64 | 85.71 | 12.99 | 10.72 | -1.83 | 1.53 | 10.97 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 11 | 2 | 18.18 | 100.00 | 27.27 | 3.96 | -8.59 | 1.98 | inf | 0.00 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_confirm | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_confirm | 11 | 8 | 72.73 | 75.00 | 2.27 | 9.72 | -2.84 | 1.21 | 5.59 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_no_rebreak | 11 | 3 | 27.27 | 66.67 | -6.06 | 2.84 | -9.72 | 0.95 | 3.73 | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_24 | 11 | 5 | 45.45 | 60.00 | -12.73 | 3.78 | -8.77 | 0.76 | 2.79 | 1.08 | EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_48 | 11 | 8 | 72.73 | 75.00 | 2.27 | 9.72 | -2.84 | 1.21 | 5.59 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOW0.1_SW0.5_BUF0_EXP24 | no_lh_rebreak_after_break_full | 11 | 9 | 81.82 | 66.67 | -6.06 | 8.59 | -3.96 | 0.95 | 3.72 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_full | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.80 | -2.87 | 1.97 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_full | 9 | 2 | 22.22 | 100.00 | 11.11 | 3.96 | -10.71 | 1.98 | inf | 0.00 | EURJPY,GBPJPY | oos_2025_2026,test_2021_2024 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_confirm | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_after_break_confirm | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.83 | -2.84 | 1.97 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_confirm_after_break_no_rebreak | 9 | 3 | 33.33 | 66.67 | -22.22 | 2.84 | -11.83 | 0.95 | 3.73 | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_24 | 9 | 3 | 33.33 | 100.00 | 11.11 | 5.90 | -8.77 | 1.97 | inf | 0.00 | GBPJPY,XAUUSD | oos_2025_2026,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | lh_rebreak_48 | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.83 | -2.84 | 1.97 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOW0.1_SW0.5_BUF0_EXP24 | no_lh_rebreak_after_break_full | 9 | 7 | 77.78 | 85.71 | -3.17 | 10.71 | -3.96 | 1.53 | 11.31 | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## 暫定解釈

- H&Sよりも、H1の戻り高値切り下げを直接見る方がH4安値停滞ショートとは相性が良い。
- 実戦本線は `practical_core4` の `lh_confirm_after_break_full`。26件から14件に絞り、勝率42.31% -> 57.14%、総R +6.16R -> +9.54R、PF 1.40 -> 2.53。
- H1再下落まで待つ条件は精度確認には有効だが、単独で必須にすると件数がかなり減る。Pineではラベル/色分けでまず比較する。
- 件数が少ない条件はPine表示だけにし、エントリー条件にはまだ入れない。

## 出力CSV

- `annotated_trades.csv`
- `rule_summary.csv`