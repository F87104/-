# B07 DTS — USDJPY TVスモーク（TV-OHLC Python）

件数: **2**

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
| 2020-07-02 18:00:00 | 2020-07-02 22:00:00 | 107.63 | 107.27689266471046 | 108.1596610029343 | -1.0283200007493225 |
| 2025-05-28 22:00:00 | 2025-05-29 02:00:00 | 144.916 | 143.71392606540408 | 146.71911090189388 | -1.0083189558580292 |

## TZ確認（1件目）

- signal_time (index): `2020-07-02 09:00:00`
- signal_time_tv: `2020-07-02 18:00:00`