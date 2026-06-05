# 投げ切り・踏み上げ — 実装前 徹底検証

作成: 2026-06-01

## 1. 実装対象の切り分け

| レイヤ | 判定 | 根拠 |
|--------|------|------|
| **踏み上げ SQZ STRICT** | **実装（EXECUTE）** | 本番5通貨・研究期 PF≥2、DD抑制 |
| **踏み上げ SQZ Pineデフォルト** | 監視プリセット | 件数多め・PFやや低 |
| **投げ切り CAP** | **WATCHのみ** | 研究期 PF≈1、単独エントリー非推奨 |

## 2. 本番ユニバース（推奨）

- 通貨: XAUUSD, USDJPY, EURJPY, CHFJPY, SILVER
- 除外: GBPJPY, AUDJPY
- 時間足: H4、ロングのみ
- 仕様: SQZ STRICT — 棚≤2ATR、急落≥3.5ATR、SL=棚安−0.25ATR、TP=2R、次足始値、最大120本

## 3. コア数値（SQZ STRICT 2R・研究期・本番5通貨）

- 件数: 35
- 勝率: 57.1%
- PF: 2.55
- 合計R: 23.83R
- maxDD: 3.09R
- 最大連敗: 3
- TP到達率: 57.1%

参考 Pineデフォルト2R（同ユニバース）:
- 83件 / WR 48.2% / PF 1.8 / +34.65R

## 4. 2R vs 2.5R（STRICT・本番5通貨・研究期）

- **2R**: 35件 WR 57.1% PF 2.55 +23.83R DD 3.09R
- **2.5R**: 35件 WR 51.4% PF 2.5 +26.09R DD 3.11R

## 5. 通貨別（STRICT 2R・研究期）

symbol  trades  win_rate  total_r  avg_r   pf  max_dd_r  max_ls  tp_pct
CHFJPY       1     100.0     1.97  1.965  inf      0.00       0   100.0
EURJPY       6      16.7    -3.09 -0.514 0.39      3.05       3    16.7
SILVER       7      71.4     7.33  1.048 4.47      1.03       1    71.4
USDJPY      11      54.5     6.88  0.626 2.36      2.02       2    54.5
XAUUSD      10      70.0    10.73  1.073 4.45      2.07       2    70.0

## 6. 期間別（STRICT 2R）

         period  trades  win_rate  total_r  avg_r   pf  max_dd_r  max_ls  tp_pct
  DEV_2015_2021      23      52.2    12.10  0.526 2.07      2.07       2    52.2
  OOS_2024_2026       6      83.3     8.92  1.487 9.73      1.02       1    83.3
VALID_2022_2023       6      50.0     2.81  0.468 1.93      3.02       3    50.0

## 7. パラメータ感度（本番5通貨・研究期・2R）

上位3:
 shelf_atr  move_atr  trades  win_rate  total_r  avg_r   pf  max_dd_r  max_ls  tp_pct
       2.0       4.0      14      71.4    15.43  1.102 4.73      1.08       1    71.4
       2.5       4.0      16      68.8    16.42  1.026 4.19      1.08       1    68.8
       3.0       4.0      17      64.7    15.40  0.906 3.50      2.02       2    64.7

## 8. アンサンブル（研究期・本番5通貨・重複時優先）

 trades  win_rate  total_r  avg_r   pf  max_dd_r  max_ls  tp_pct               scenario
    165      36.4    62.73  0.380 1.56     12.44       8     0.0           TB_long_only
     21      61.9    19.42  0.925 4.04      3.35       4     0.0                T5_only
     35      57.1    23.83  0.681 2.55      3.09       3     0.0               SQZ_only
    179      39.1    77.74  0.434 1.68     12.44       8     0.0       TB+T5_T5priority
    200      40.0    86.56  0.433 1.68      9.27       7     0.0      TB+SQZ_TBpriority
     56      58.9    43.25  0.772 2.99      4.39       4     0.0      T5+SQZ_T5priority
    214      42.1   101.57  0.475 1.79      9.27       7     0.0    TB+T5+SQZ_T5>TB>SQZ
    214      42.1   101.57  0.475 1.79      9.27       7     0.0 TB+T5+SQZ_SQZwhen_free

## 9. 重複率

          pair  sqz_trades  overlap_trades  overlap_pct
SQZ_vs_TB_long          35               0          0.0
     SQZ_vs_T5          35               0          0.0

## 10. 投げ切り（監視層）

- 研究期シグナル数（本番5通貨）: 148
- 24H4以内にSQZ STRICTが続く率: 2.7%

## 11. 実装 GO 条件チェック

| 条件 | 状態 |
|------|------|
| 研究期 PF≥1.5 | OK (2.55) |
| 研究期 件数≥25 | OK (35) |
| maxDD≤8R | OK (3.09R) |
| OOS PF≥1.0 | 要確認 summary_matrix |
| TVパリティ5件 | 未実施 |
| フォワード20件 | 未実施 |

## 12. 実装タスク

1. `pine/production/h4_sqz_strict_live.pine` — EXECUTE + alert
2. `pine/visual/market_psychology_cap_sqz_visual.pine` — ユーザー案を保存（CAP/SQZ表示）
3. 運用: CAP=青ラベル監視、SQZ STRICT=ライム＋アラート
4. TB/T5併用時は `TB+T5+SQZ_T5>TB>SQZ` または空きスロットのみSQZ

## ファイル

- `docs/research/cap_sqz_thorough_validation_2026-06-01/` 以下 CSV 一式