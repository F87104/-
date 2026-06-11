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

## 2. IS（2014-2024）vs OOS（2025-）

| 銘柄 | 構成 | IS件数 | IS PF | IS R | OOS件数 | OOS PF | OOS R |
|---|---|---:|---:|---:|---:|---:|---:|
| USDJPY | context+fixed_1_5R | 47 | 1.01 | 0.26 | 6 | 1.09 | 0.27 |
| EURJPY | diag_break+fixed_1_5R | 114 | 1.50 | 24.33 | 11 | 0.71 | -1.67 |
| GBPJPY | diag_break+fixed_1_5R | 103 | 1.66 | 28.35 | 17 | 0.71 | -3.05 |
| AUDJPY | context+fixed_2R | 55 | 1.30 | 8.25 | 6 | 1.66 | 2.01 |
| CHFJPY | diag_break+fixed_2R | 77 | 1.00 | 0.15 | 13 | 5.48 | 9.18 |
| XAUUSD | diag_break+fixed_2R | 105 | 1.03 | 1.59 | 14 | 1.74 | 4.75 |

## 3. 所感（自動生成時点）

- 通貨ごとに最適フィルタ/TPが異なる（v2.1マトリクスと同じく**銘柄別最適化**が必要）。
- GBPJPY は diag_break が突出。USDJPY/EURJPY/CHFJPY は context が安定。
- 貴金属（XAUUSD）は total_r は出るが DD が大きい → ロット調整前提。
- 次の精度向上候補: D1方向一致（実装済みのcontext）に加え、ADX下限・調整時間フィルタ。

## 4. 残タスク

- [ ] NAS100 / XAGUSD のデータ追加と検証
- [ ] 精度向上フィルタ（ADX / 調整時間 / 実体比率）のグリッド追加
- [ ] 採用候補のTradingView目視確認（人が見て納得できる位置に出るか）