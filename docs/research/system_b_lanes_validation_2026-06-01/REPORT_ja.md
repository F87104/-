# 系統B — 10レーン本格実装向け検証

作成日: 2026-06-01

**前提:** TrendBreak V1 / H4 T5 とは完全別系統。最適化なし・既存固定ルールのみ再集計。

## 1. レーン別サマリー（全期間）

| lane_id | name_ja | direction | tf | pine_ready | all_trades | all_trades_per_year | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | res_trades | res_trades_per_year | res_win_rate | res_total_r | res_avg_r | res_pf | res_max_dd_r | oos_trades | oos_trades_per_year | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01_SQZ_XAUUSD | 踏み上げ STRICT・XAU | long | H4 | yes | 10 | 1.42 | 70.0 | 10.73 | 1.073 | 4.45 | 2.07 | 10 | 1.42 | 70.0 | 10.73 | 1.073 | 4.45 | 2.07 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |  | 0.0 |
| B02_SQZ_USDJPY | 踏み上げ STRICT・USDJPY | long | H4 | yes | 13 | 1.32 | 46.2 | 4.87 | 0.375 | 1.69 | 2.02 | 11 | 1.29 | 54.5 | 6.88 | 0.626 | 2.36 | 2.02 | 2 | 2.0 | 0.0 | -2.01 | -1.007 | 0.0 | 1.01 |
| B03_SQZ_EURJPY | 踏み上げ STRICT・EURJPY | long | H4 | yes | 6 | 0.65 | 16.7 | -3.09 | -0.514 | 0.39 | 3.05 | 6 | 0.65 | 16.7 | -3.09 | -0.514 | 0.39 | 3.05 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |  | 0.0 |
| B04_SQZ_CHFJPY | 踏み上げ STRICT・CHFJPY | long | H4 | yes | 1 | 1.0 | 100.0 | 1.97 | 1.965 | inf | 0.0 | 1 | 1.0 | 100.0 | 1.97 | 1.965 | inf | 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |  | 0.0 |
| B05_SQZ_SILVER | 踏み上げ STRICT・SILVER | long | H4 | yes | 7 | 0.93 | 71.4 | 7.33 | 1.048 | 4.47 | 1.03 | 7 | 0.93 | 71.4 | 7.33 | 1.048 | 4.47 | 1.03 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |  | 0.0 |
| B06_VIS_PRECALM | V初動棚 PRECALM | long | H4 | partial | 34 | 3.12 | 58.8 | 15.55 | 0.457 | 2.09 | 5.11 | 29 | 3.07 | 55.2 | 10.61 | 0.366 | 1.8 | 5.11 | 5 | 4.91 | 80.0 | 4.93 | 0.986 | 5.84 | 1.02 |
| B07_DTS_TRAP_SHELF | D1トラップ遅延 H4棚 | long | H4 | partial | 9 | 0.86 | 100.0 | 13.35 | 1.484 | inf | 0.0 | 6 | 0.63 | 100.0 | 8.9 | 1.483 | inf | 0.0 | 3 | 3.0 | 100.0 | 4.46 | 1.485 | inf | 0.0 |
| B08_LSS_SHORT_CORE4 | 月次安値停滞ショート | short | H4 | no | 11 | 1.14 | 72.7 | 12.55 | 1.141 | 4.98 | 1.08 | 10 | 1.05 | 70.0 | 10.57 | 1.057 | 4.35 | 1.08 | 1 | 1.0 | 100.0 | 1.98 | 1.984 | inf | 0.0 |
| B09_IGNITION_STRICT | 点火 STRICT（XAU除外） | long | H4 | no | 7 | 0.85 | 71.4 | 5.36 | 0.765 | 3.62 | 1.02 | 6 | 0.77 | 66.7 | 3.87 | 0.644 | 2.89 | 1.02 | 1 | 1.0 | 100.0 | 1.49 | 1.492 | inf | 0.0 |

## 2. 昇格判定

| lane_id | name_ja | pine_ready | max_trades_per_year | status | blockers | passes | res_trades | res_trades_per_year | res_win_rate | res_total_r | res_avg_r | res_pf | res_max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01_SQZ_XAUUSD | 踏み上げ STRICT・XAU | yes | 3 | LIVE_CANDIDATE | oos_no_trades | sample_ok;research_pf_ok;research_dd_ok;freq_ok;pine_ok | 10 | 1.42 | 70.0 | 10.73 | 1.073 | 4.45 | 2.07 |
| B02_SQZ_USDJPY | 踏み上げ STRICT・USDJPY | yes | 3 | LIVE_CANDIDATE | oos_weak | sample_ok;research_pf_ok;research_dd_ok;freq_ok;pine_ok | 11 | 1.29 | 54.5 | 6.88 | 0.626 | 2.36 | 2.02 |
| B03_SQZ_EURJPY | 踏み上げ STRICT・EURJPY | yes | 3 | FORWARD_0.25R | research_PF<1.5;oos_no_trades | sample_ok;research_dd_ok;freq_ok;pine_ok | 6 | 0.65 | 16.7 | -3.09 | -0.514 | 0.39 | 3.05 |
| B04_SQZ_CHFJPY | 踏み上げ STRICT・CHFJPY | yes | 3 | FORWARD_0.25R | trades<5;oos_no_trades | research_pf_ok;research_dd_ok;freq_ok;pine_ok | 1 | 1.0 | 100.0 | 1.97 | 1.965 | inf | 0.0 |
| B05_SQZ_SILVER | 踏み上げ STRICT・SILVER | yes | 3 | LIVE_CANDIDATE | oos_no_trades | sample_ok;research_pf_ok;research_dd_ok;freq_ok;pine_ok | 7 | 0.93 | 71.4 | 7.33 | 1.048 | 4.47 | 1.03 |
| B06_VIS_PRECALM | V初動棚 PRECALM | partial | 3 | FORWARD_0.25R |  | sample_ok;research_pf_ok;research_dd_ok;freq_ok;oos_okish;pine_parity_pending | 29 | 3.07 | 55.2 | 10.61 | 0.366 | 1.8 | 5.11 |
| B07_DTS_TRAP_SHELF | D1トラップ遅延 H4棚 | partial | 3 | FORWARD_0.25R |  | sample_ok;research_pf_ok;research_dd_ok;freq_ok;oos_okish;pine_parity_pending | 6 | 0.63 | 100.0 | 8.9 | 1.483 | inf | 0.0 |
| B08_LSS_SHORT_CORE4 | 月次安値停滞ショート | no | 3 | HOLD | pine_not_ready | sample_ok;research_pf_ok;research_dd_ok;freq_ok;oos_okish | 10 | 1.05 | 70.0 | 10.57 | 1.057 | 4.35 | 1.08 |
| B09_IGNITION_STRICT | 点火 STRICT（XAU除外） | no | 3 | HOLD | pine_not_ready | sample_ok;research_pf_ok;research_dd_ok;freq_ok;oos_okish | 6 | 0.77 | 66.7 | 3.87 | 0.644 | 2.89 | 1.02 |

## 3. ポートフォリオ（重複排除・SQZ優先）

- 採用トレード数: **88**
- 年あたり: **7.87**
- 総R: **53.79** / PF **2.46** / maxDD **6.15R**

## 4. 重複の多いレーン組

| lane_a | lane_b | overlap_pairs |
| --- | --- | --- |
| B06_VIS_PRECALM | B07_DTS_TRAP_SHELF | 9 |
| B02_SQZ_USDJPY | B06_VIS_PRECALM | 1 |
| B01_SQZ_XAUUSD | B02_SQZ_USDJPY | 0 |
| B05_SQZ_SILVER | B06_VIS_PRECALM | 0 |
| B04_SQZ_CHFJPY | B05_SQZ_SILVER | 0 |
| B04_SQZ_CHFJPY | B06_VIS_PRECALM | 0 |
| B04_SQZ_CHFJPY | B07_DTS_TRAP_SHELF | 0 |
| B04_SQZ_CHFJPY | B08_LSS_SHORT_CORE4 | 0 |
| B04_SQZ_CHFJPY | B09_IGNITION_STRICT | 0 |
| B05_SQZ_SILVER | B07_DTS_TRAP_SHELF | 0 |

## 5. 実装ロードマップ

### 即フォワード0.25R（Pine ready）

- B01_SQZ_XAUUSD: 踏み上げ STRICT・XAU
- B02_SQZ_USDJPY: 踏み上げ STRICT・USDJPY
- B03_SQZ_EURJPY: 踏み上げ STRICT・EURJPY
- B04_SQZ_CHFJPY: 踏み上げ STRICT・CHFJPY
- B05_SQZ_SILVER: 踏み上げ STRICT・SILVER

### Pine照合後フォワード

- B06_VIS_PRECALM: V初動棚 PRECALM
- B07_DTS_TRAP_SHELF: D1トラップ遅延 H4棚

### 保留（样本/Pine）

- B08_LSS_SHORT_CORE4: pine_not_ready
- B09_IGNITION_STRICT: pine_not_ready

## 6. 再現

```bash
python3 scripts/validate_system_b_lanes.py
```

全トレード: 98 件