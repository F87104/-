# B07 DTS — USDJPY TVスモーク照合

件数: **2**（Python期待値）

## Pine 必須設定

- **chart:** `H4`
- **strategy:** `selected_CURRENT_A30_180_SIGADX30`
- **tp_basis:** `Entry基準`
- **trap_age_min:** `30`
- **trap_age_max:** `180`
- **signal_adx_max:** `30`
- **Pineファイル:** `pine/research/d1_trap_h4_shelf_strict_strategy.pine`

## 照合手順

1. TVで H4・シンボルを合わせる
2. 下表の `signal_time`（UTC相当）にラベル「棚B」があるか
3. JST表示なら +9h で同じバーを指すか1件目で確認
4. 一致したら `stop` / `target` をラベル表示値と比較
5. `parity_log_*_filled.csv` の `tv_match` を OK / MISS / OFFSET / DATA に更新

## 期待シグナル一覧

| # | period | signal_time (UTC) | entry_time | signal_close | stop | target | r |
|---|--------|-------------------|------------|--------------|------|--------|---|
| 8 | OOS_2025_2026 | 2025-07-07 00:00:00 | 2025-07-07 04:00:00 | 144.833 | 144.0809776124362 | 145.95353358134577 | 1.486649264206239 |
| 9 | OOS_2025_2026 | 2025-09-24 04:00:00 | 2025-09-24 08:00:00 | 148.042 | 147.37495818692463 | 149.04006271961305 | 1.484985927604429 |

## 最初の1件（TZ確認用）

- signal_time: `2025-07-07 00:00:00`
- TVがJSTなら表示目安: `2025-07-07 09:00:00`（要1件目視確認）
- entry_time: `2025-07-07 04:00:00`（次のH4始値）