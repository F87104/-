# 節目飛び乗り抑制フィルタ v0.1（v2.x 試験）

作成日: 2026-05-31

> **2026-06-10 研究終了。** F1 試験は完了（件数照合済み）。  
> **v2.x 本体への移植は見送り。** 本番研究は既存2本柱（TrendBreakV1 + H4 T5）に集中する。

## 研究の問い

つまずきクラスタで見つかった「節目高値追い」「天井買い」「底売り」を、
**失敗の逆張り**ではなく **同方向エントリーの抑制** として v2.x に載せると、
件数と PF がどう変わるか。

## 根拠データ

| ファイル | 内容 |
|---|---|
| [student_stumble_clusters_v0_2.csv](student_stumble_clusters_v0_2.csv) | 29クラスタ / 全敗15 |
| [student_stumble_wait_zones_v0_1.csv](student_stumble_wait_zones_v0_1.csv) | 待つ場所15件 |
| [student_stumble_zones_*_v0_4.pine](../../pine/research/student_stumble_zones_gbpjpy_v0_4.pine) | 赤=失敗 / 青=待つ |

## フィルタ3本柱（Pine 試験実装）

| ID | 名称 | 条件 | つまずきとの対応 |
|---|---|---|---|
| **F1** | 節目近接追い | ラウンド価格±N 以内の順張り | GBPJPY 199/195、USDJPY 140/146、XAU 2720/2780/2950 |
| **F2** | 伸び切り直後 | 大足(≥1.1ATR)の後1-2本の同方向 | 「待てずに飛び乗り」型 |
| **F3** | 高安端追い | 20本高安から0.8ATR以内の端追い | 高値追い買い / 安値売り |

## v0.1.1 修正（2026-05-31）

**症状:** Strategy Tester が「トレードデータが必要」= 0件。

**原因:** F3「高安端追い」が 12本ブレイクと矛盾。ブレイク足は必ず高値/安値付近になるため、フィルタONで **100%ブロック** されていた。

**修正:**
- F1: 節目近接 **かつ** 高値/安値帯 **かつ** 同方向足（199円台追い型）
- F3: **初回ブレイクは通す**。既にレンジ外にいての二段目追いだけ抑制
- 右上テーブルに `Trades:` 件数を表示

## 試験 Pine

[stumble_chase_suppression_experiment_v0_1.pine](../../pine/research/stumble_chase_suppression_experiment_v0_1.pine)（v0.1.1）

- **入口**: 意図的に飛び乗りやすい「12本高安ブレイク + EMA50方向」
- **比較**: 入力 `フィルタON` を OFF / ON で切替
- **表示**: ブロックされた足にオレンジ `×`（F）

## TradingView テスト手順

1. **GBPJPY 1H**（199円クラスタ確認用）または **XAUUSD 1H**
2. Pine を貼り付け → Strategy Tester を開く
3. **フィルタOFF** でバックテスト → 件数・PF・DD をメモ
4. **フィルタON**（F1/F2/F3 全部ON）で再実行 → 差分を比較
5. 2024/10（GBPJPY 199円台）や 2024/12〜2025/2（XAUUSD 天井）を期間限定して確認

## 試験 Pine（確定版 v0.1.1）

[stumble_chase_suppression_experiment_v0_1.pine](../../pine/research/stumble_chase_suppression_experiment_v0_1.pine)

F1/F2/F3 のロジックはこのファイルで確定。**2026-06-10: v2.x 移植は見送り**（アーカイブ）。

## OANDA CSV 照合（2026-06-10 / Python）

| case | 件数 | PF |
|------|-----:|---:|
| filter_off | 1,193 | 1.07 |
| filter_on_all | 458 | 0.911 |
| TV 参照 OFF/ON | 1,279 / 473 | 0.906 / 0.78 |

件数パリティは取れたが、PF 改善は未確認 → **本番移植見送り**。

## TradingView 実測（GBPJPY 1H・全期間）

| 指標 | OFF | ON |
|---|---:|---:|
| 件数 | 1,279 | 473 |
| 純利益 | -34.61 JPY | -25.51 JPY |
| PF | 0.906 | 0.78 |
| 最大DD | 42.85 JPY | 30.56 JPY |

**結論（試験）**

- ベースラインは研究用の「追いやすい入口」のため PF<1 は想定内
- フィルタ ON は **件数・DD・損失額を改善** → 抑制ロジック自体は機能
- 全期間 PF 改善までは未達 → v2.x では **F1 だけ** 載せ、F2/F3 は保留

## v2.x への載せ方

~~1. 下記 F1 ブロック条件を matrix 戦略の新規エントリー前に `and not f1BlockLong` で追加~~  
~~2. 通貨別: GBPJPY=ON / XAUUSD=ON / USDJPY=要検証~~  
~~3. F2/F3 は v0.1.1 に残し、本番採用は見送り~~

**2026-06-10 更新: v2.x 移植は見送り。** OANDA 照合で件数パリティは取れたが、PF 改善は未確認。試験 Pine と CSV はアーカイブとして残す。

```pine
// F1 core (from v0.1.1) — 参考実装のみ
f1BlockLong  = nearRound and nearHigh and close > open and longSignal
f1BlockShort = nearRound and nearLow and close < open and shortSignal
```

## 次にやること

**2026-06-10: 研究終了。** 次は [RESEARCH_INDEX.md](RESEARCH_INDEX.md) の既存2本柱研究（TrendBreakV1 + H4 T5）へ。
