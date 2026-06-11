# Synapse TradingView H4 検証 — 銘柄横断比較

> `run_synapse_tv_h4.py` の出力（`results_tv_h4/`）から自動生成。
> 構造は **ihs_5pivot**（最良構造）に固定し、フィルタは context / diag_break のうち
> total_r 最良（trades ≥ 20）を採用。コストは銘柄別に概算設定済み。

## 1. 銘柄ごとの最良構成（ihs_5pivot）

| 銘柄 | フィルタ | TP | 件数 | 勝率 | 合計R | PF | 最大DD |
|---|---|---|---:|---:|---:|---:|---:|
| USDJPY | context | fixed_1_5R | 44 | 47.73 | 3.64 | 1.19 | 4.67 |
| EURJPY | diag_break | fixed_1_5R | 89 | 47.19 | 10.76 | 1.28 | 12.87 |
| GBPJPY | diag_break | fixed_1_5R | 74 | 58.11 | 31.21 | 2.08 | 4.50 |
| AUDJPY | context | fixed_2R | 39 | 46.15 | 3.99 | 1.20 | 9.26 |
| CHFJPY | diag_break | fixed_2R | 58 | 44.83 | 4.42 | 1.15 | 10.98 |
| XAUUSD | diag_break | fixed_2R | 90 | 41.11 | 8.49 | 1.17 | 21.16 |
| XAGUSD | context | fixed_2R | 48 | 37.50 | -2.04 | 0.93 | 5.02 |
| NAS100 | diag_break | fixed_1_5R | 53 | 54.72 | 10.68 | 1.48 | 3.68 |

## 2. IS（2014-2024）vs OOS（2025-）

| 銘柄 | 構成 | IS件数 | IS PF | IS R | OOS件数 | OOS PF | OOS R |
|---|---|---:|---:|---:|---:|---:|---:|
| USDJPY | context+fixed_1_5R | 47 | 1.01 | 0.26 | 6 | 1.09 | 0.27 |
| EURJPY | diag_break+fixed_1_5R | 114 | 1.50 | 24.33 | 11 | 0.71 | -1.67 |
| GBPJPY | diag_break+fixed_1_5R | 103 | 1.66 | 28.35 | 17 | 0.71 | -3.05 |
| AUDJPY | context+fixed_2R | 55 | 1.30 | 8.25 | 6 | 1.66 | 2.01 |
| CHFJPY | diag_break+fixed_2R | 77 | 1.00 | 0.15 | 13 | 5.48 | 9.18 |
| XAUUSD | diag_break+fixed_2R | 105 | 1.03 | 1.59 | 14 | 1.74 | 4.75 |
| XAGUSD | context+fixed_2R | 68 | 1.22 | 7.54 | 5 | 1.31 | 0.93 |
| NAS100 | diag_break+fixed_1_5R | 75 | 1.35 | 11.45 | 9 | 1.19 | 0.98 |

## 3. 所感（8銘柄検証時点）

- 通貨ごとに最適フィルタ/TPが異なる（v2.1マトリクスと同じく**銘柄別最適化**が必要）。
- **採用候補（ihs_5pivot でプラス）**: GBPJPY(PF2.08) / NAS100(PF1.48) / EURJPY(PF1.28) /
  AUDJPY(PF1.20) / USDJPY(PF1.19) / XAUUSD(PF1.17) / CHFJPY(PF1.15)。
- **NAS100 は Synapse と好相性**（diag_break 1.5R で PF1.48・勝率55%・DD3.7Rと優秀）。
- **XAGUSD は ihs_5pivot ではマイナス**（PF0.93）。銀はこの構造を使わない、
  または別構造（all構造では context 2R が PF1.23）で再検討する。
- フィルタ傾向: GBPJPY/EURJPY/NAS100/XAUUSD/CHFJPY は **diag_break**、
  USDJPY/AUDJPY は **context** が良い。
- 貴金属（XAUUSD）は total_r は出るが DD が大きい（21R）→ ロット調整前提。

## 4. 残タスク

- [ ] XAGUSD の別構造（classic_6pivot / role_ab_5pivot）での再検証
- [ ] 精度向上フィルタ（ADX下限 / 調整時間 / 実体比率）のグリッド追加
- [ ] 採用候補のTradingView目視確認（人が見て納得できる位置に出るか）
- [ ] H4で機能した銘柄をH1へ落とせるか検証