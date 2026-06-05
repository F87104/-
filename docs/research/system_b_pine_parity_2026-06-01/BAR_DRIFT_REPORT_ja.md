# B06 USDJPY — ローソク足・時刻ずれ解析

Python: F87104_test H1 → H4 (`label=left, closed=left`).
TV: ストラテジーテスター約定時刻・価格（OANDA表示チャート）。

## 1. サマリー

- Pythonシグナル: **13** 件
- TVテスター: **9** 件
- Python signal と TV entry が **1日以内**: **4** 件
- **3日超ずれ**: **9** 件（データ/ピボット差の疑い）

## 2. 価格ずれ（TV約定 vs Python約定）

一致ペア（1日以内）の entry 差:

- 平均 **0.7 pip** / 最大 **8.3 pip**

## 3. 時間ずれ（H4本数）

- 1日以内ペアの TV entry と Py entry の差: 平均 **3.2** 本 / 最大 **4** 本

3日超ずれの Python シグナル（TVに無い）:

- id **8** signal `2016-10-03 20:00:00` nearest TV `2018-11-07 03:00:00` gap **764.29** 日
- id **11** signal `2018-11-12 00:00:00` nearest TV `2018-11-07 03:00:00` gap **4.88** 日
- id **15** signal `2020-11-11 12:00:00` nearest TV `2021-02-01 23:00:00` gap **82.46** 日
- id **18** signal `2021-08-09 16:00:00` nearest TV `2021-11-12 11:00:00` gap **94.79** 日
- id **22** signal `2023-08-01 08:00:00` nearest TV `2023-10-26 02:00:00` gap **85.75** 日
- id **25** signal `2024-02-05 12:00:00` nearest TV `2023-10-26 02:00:00` gap **102.42** 日
- id **28** signal `2024-09-24 04:00:00` nearest TV `2024-06-20 06:00:00` gap **95.92** 日
- id **32** signal `2025-07-07 00:00:00` nearest TV `2025-05-29 02:00:00` gap **38.92** 日
- id **33** signal `2025-09-24 04:00:00` nearest TV `2025-05-29 02:00:00` gap **118.08** 日

## 4. TV約定 vs Python同一時刻の足

`drift_tv_vs_python.csv` の `as_utc_entry_vs_open_pips` / `tv_ui_jst_to_utc_*` を参照。
JST表示をUTCに直すと open との差が縮むペアあり → **時刻解釈が主因**のことが多い。

## 5. TV OHLCを入れた場合

一致インデックス **12539** 本（TVシフト **-1h**）: close中央値ずれ **5.65** pip / 平均 **-0.49** pip / 最大 **368.6** pip
- close が **1 pip 以内** のバー: **10.5%**（同一インデックス照合）
- tv index shifted -1h (min median |close| pip among shifts with n>=500)
- 中央値が数 pip 超なら **H4足の区切り（open時刻）が Python と TV で一致していない** 可能性が高い

## 6. CSV

- `drift_tv_vs_python.csv` — TV各トレードの時刻・価格ずれ
- `drift_python_signals.csv` — Python各シグナルと最寄TV
- `ohlc_diff_per_bar.csv` — TV OHLCあり時のみ

再現: `python3 scripts/analyze_b06_bar_drift.py`