# H4 Low-Stagnation Short Pine Parity Audit

Status: Pine変換監査用。Python検証を正として、TradingView Pine strategyが同じシグナルを出すか確認する。

## 重要結論

- Pineのストラテジーテスター成績は、Pythonの期待シグナルと一致するまで採用判断に使わない。
- TradingView側はデータ提供元、タイムゾーン、過去データ開始日、年末年始除外、コスト処理がPythonと違う可能性がある。
- まずは単体通貨で `entry_time` と件数が一致するかだけを見る。PFや勝率はその後。
- 2026-05-29時点で、TradingView GBPJPY H4はPython期待4件に対してPine側7件が出る不一致を確認。`勝ちトレード57.14% / PF 2.447` は採用しない。

## Pine設定

- チャート: H4
- 検証開始: 2015-01-01
- 検証終了: 2026-12-31
- 12/15-1/10除外: ON
- core4のみ: ON
- entryMode: `実戦候補` または `厳選候補`
- default quantityは成績比較用ではなく、まずシグナル一致確認用。
- strategy版には `PY期待`, `一致`, `余計` マーカーを追加済み。GBPJPYでは `Matched=4 / Extra=0` になるまで不一致扱い。

## 期待サマリー

| case | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primary all | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| Primary core4 candidate | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| Primary core4 practical | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| Primary core4 strict | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| GBPJPY practical | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 | 0 | GBPJPY |

## GBPJPY 期待シグナル

TradingViewのGBPJPY H4で、まずこの4件に近い場所だけが出るか確認する。
時刻はPythonデータのindexで、TradingView表示タイムゾーンとはずれる場合がある。

| symbol | signal_time | entry_time | base_exit_time | base_exit_reason | trigger_type | lookback_bars | support_age_bars | prior_low | zone_low | zone_high | break_depth_atr | break_close_location | risk_atr_at_signal | base_target_2r | base_r_after_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 2016-10-10 00:00:00 | 2016-10-10 04:00:00 | 2016-10-11 16:00:00 | TP | stagnation | 120 | 48 | 129.65 | 127.93 | 128.59 | 0.43 | 0.11 | 1.38 | 124.94 | 1.98 |
| GBPJPY | 2018-05-25 04:00:00 | 2018-05-25 08:00:00 | 2018-05-29 04:00:00 | TP | stagnation | 120 | 68 | 147.01 | 146.07 | 146.69 | 0.17 | 0.23 | 1.40 | 144.21 | 1.98 |
| GBPJPY | 2023-12-13 08:00:00 | 2023-12-13 12:00:00 | 2023-12-13 16:00:00 | TP | stagnation | 120 | 73 | 184.45 | 182.48 | 183.09 | 0.21 | 0.23 | 1.42 | 180.46 | 1.98 |
| GBPJPY | 2025-01-15 04:00:00 | 2025-01-15 08:00:00 | 2025-01-17 04:00:00 | TP | stagnation | 120 | 3 | 192.20 | 192.28 | 192.99 | 0.42 | 0.49 | 1.49 | 189.36 | 1.98 |

## 通貨別 実戦候補 件数

| symbol | trades | total_r |
| --- | --- | --- |
| CHFJPY | 3 | 2.83 |
| EURJPY | 1 | 1.98 |
| GBPJPY | 4 | 7.92 |
| XAUUSD | 1 | 1.94 |

## 出力CSV

- `expected_primary_all.csv`
- `expected_core4_candidate.csv`
- `expected_core4_practical.csv`
- `expected_core4_strict.csv`
- `expected_gbpjpy_practical.csv`
