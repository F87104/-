# B07 DTS — GBPJPY TVスモーク（TV-OHLC Python）

件数: **3**

## Pine 必須設定

- **chart:** `H4`
- **strategy:** `selected_CURRENT_A30_180_SIGADX30`
- **tp_basis:** `Entry基準`
- **trap_age_min:** `30`
- **trap_age_max:** `180`
- **signal_adx_max:** `30`
- **Pineファイル:** `pine/research/d1_trap_h4_shelf_strict_strategy.pine`

## 照合

1. `signal_time_tv` / `entry_time_tv` を TV 表示（JST）と照合
2. B06 と同日シグナルは **B06 優先**（`overlap_b06_b07_tv_signal_times.csv`）
3. 旧 F87104 `python_expected_b07_dts_all.csv`（9件）は **signal_time 不一致** — 使わない

| signal_time_tv | entry_time_tv | entry | stop | target | r |
|----------------|---------------|-------|------|--------|---|
| 2016-11-04 22:00:00 | 2016-11-05 02:00:00 | 129.0925 | 127.8563016636958 | 130.9467975044563 | -1.0161786336485366 |
| 2018-07-05 14:00:00 | 2018-07-05 18:00:00 | 146.432 | 145.45789706308844 | 147.8931544053673 | 1.479468288984537 |
| 2024-10-09 18:00:00 | 2024-10-09 22:00:00 | 194.818 | 193.2428765250687 | 197.18068521239695 | 1.48730258273824 |

## TZ確認（1件目）

- signal_time (index): `2016-11-04 13:00:00`
- signal_time_tv: `2016-11-04 22:00:00`