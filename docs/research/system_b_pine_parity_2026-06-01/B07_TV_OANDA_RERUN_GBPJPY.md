# B07 GBPJPY — TV OANDA データでの Python 再実行

## 目的

B07 DTS: D1 Trap 文脈（F87104）+ **H4 は TV OANDA CSV** で再実行。Pine 照合の正は TV-OHLC Python。

## Pine 必須

- ファイル: `pine/research/d1_trap_h4_shelf_strict_strategy.pine`
- strategy: `selected_CURRENT_A30_180_SIGADX30`
- tp_basis: Entry基準
- trap_age: 30–180, signal_adx_max: 30

## 件数

| 系列 | 件数 |
|------|------|
| F87104 export（従来） | **2** |
| TV OANDA H4 CSV（今回） | **3** |
| 同一 signal_time | **0** |
| TVテスターと±2h（entry_time_tv） | **0/3** |

## B06 との重複

同一 `signal_time` の B06/B07 は **9件**（`overlap_b06_b07_signal_times.csv`）。
本番・TV では **B06 優先**（portfolio_slots overlap_resolution）。

**F87104 export のみ:**
- GBPJPY|2016-08-24 08:00:00
- GBPJPY|2024-10-09 08:00:00

**TV-OHLC Python のみ:**
- GBPJPY|2016-11-04 13:00:00
- GBPJPY|2018-07-05 05:00:00
- GBPJPY|2024-10-09 09:00:00

## 次の作業（Pine）

1. `python_expected_b07_tv_oanda_<symbol>.csv` の `signal_time_tv` にラベル
2. tp_basis=Entry基準、strategy 名を上記と一致
3. B06 と同日のシグナルは B06 が先 — B07 ラベルは重複日を確認
4. テスターは `entry_time_tv` と照合

## ファイル

- `python_expected_b07_tv_oanda_gbpjpy.csv`
- `b07_f87104_vs_tv_oanda_gbpjpy.csv`
- `b07_tv_oanda_vs_tester_gbpjpy.csv`（テスターCSVがある場合）

再現: `python3 scripts/run_b07_tv_oanda_parity.py`