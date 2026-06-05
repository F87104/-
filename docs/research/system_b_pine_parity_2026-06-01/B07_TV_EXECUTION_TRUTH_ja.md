# B07 DTS — TV 執行の正

## 正とする系列

| 項目 | 値 |
|------|-----|
| データ | 既存4ファイル `tv_{usdjpy,eurjpy,gbpjpy,audjpy}_h4.csv`（B06と同じ） |
| Python | `scripts/run_b07_tv_oanda_parity.py` |
| 期待値 | `python_expected_b07_tv_oanda_all.csv`（**12件**） |
| D1 Trap 文脈 | F87104 `trap_false_break_reaction/events.csv`（H4のみTV） |
| Pine | `pine/research/d1_trap_h4_shelf_strict_strategy.pine` |
| strategy | `selected_CURRENT_A30_180_SIGADX30` |
| tp_basis | **Entry基準**（B06は Signal基準） |

## 時刻の見方

- `signal_time` / `entry_time` … TV CSV のバー index（UTC相当）
- `signal_time_tv` / `entry_time_tv` … チャート・テスター表示（**+9h**）

## 旧 export（9件）について

`python_expected_b07_dts_all.csv` は F87104 H1→H4 のため **TV と signal_time が一致しない**（0/9）。
entry ±4h で近いのは EURJPY 2016-10、GBPJPY 2024-10 の **2件のみ**（`b07_export_entry_vs_tv_oanda.csv`）。

**Pine 照合は 12件の TV-OHLC Python を正とする。**

## B06 との重複

TV-OHLC 上で B06∩B07 同一 signal_time は **12件**（B07の全件）。
本番・overlap ルールでは **B06 優先** → 一覧は `overlap_b06_b07_tv_signal_times.csv`。

## テスター

B06 用 `tv_strategy_trades_*.csv` は **流用しない**。
B07 Pine を載せたうえで `tv_strategy_trades_b07_{symbol}.csv` を別途エクスポートする。

## 再現

```bash
python3 scripts/run_b07_tv_oanda_parity.py
```
