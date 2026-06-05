# B07 DTS — AUDJPY TVスモーク（TV-OHLC Python）

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
| 2018-11-01 10:00:00 | 2018-11-01 14:00:00 | 80.472 | 79.75441987270598 | 81.54837019094101 | 1.482580342564494 |
| 2019-07-22 18:00:00 | 2019-07-22 22:00:00 | 76.11 | 75.77287296883932 | 76.615690546741 | -1.0370780116828753 |
| 2023-07-25 10:00:00 | 2023-07-25 14:00:00 | 95.594 | 94.78192087807004 | 96.81211868289492 | -1.015392588803763 |

## TZ確認（1件目）

- signal_time (index): `2018-11-01 01:00:00`
- signal_time_tv: `2018-11-01 10:00:00`