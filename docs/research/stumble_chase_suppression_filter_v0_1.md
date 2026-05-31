# 節目飛び乗り抑制フィルタ v0.1（v2.x 試験）

作成日: 2026-05-31

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

## 試験 Pine

[stumble_chase_suppression_experiment_v0_1.pine](../../pine/research/stumble_chase_suppression_experiment_v0_1.pine)

- **入口**: 意図的に飛び乗りやすい「12本高安ブレイク + EMA50方向」
- **比較**: 入力 `フィルタON` を OFF / ON で切替
- **表示**: ブロックされた足にオレンジ `×`（F）

## TradingView テスト手順

1. **GBPJPY 1H**（199円クラスタ確認用）または **XAUUSD 1H**
2. Pine を貼り付け → Strategy Tester を開く
3. **フィルタOFF** でバックテスト → 件数・PF・DD をメモ
4. **フィルタON**（F1/F2/F3 全部ON）で再実行 → 差分を比較
5. 2024/10（GBPJPY 199円台）や 2024/12〜2025/2（XAUUSD 天井）を期間限定して確認

## 期待する結果（仮説）

| 指標 | フィルタOFF | フィルタON |
|---|---|---|
| 件数 | 多い | 減る |
| PF | 低め（追い負け多） | 改善する可能性 |
| 勝率 | — | やや下がっても PF 改善ならOK |

**成功の定義**: つまずき期間（10/28-30 GBPJPY、12/12 XAUUSD 等）で
フィルタON が明らかにエントリーを減らし、DD が改善する。

## v2.x への載せ方（次段）

1. 本試験で F1-F3 のパラメータを通貨別に調整
2. `market_psychology_v2_matrix_strategy` の新規エントリー前に
   `not blockLong / not blockShort` を AND する
3. 通貨別 ON/OFF マトリクス（GBPJPY/XAUUSD=ON、USDJPY=部分ON 等）

## 次にやること

1. GBPJPY / XAUUSD / USDJPY で OFF vs ON の数値を TradingView に記録
2. F1 だけ / F2 だけ / F3 だけ の寄与を切り分け
3. v2.x 本体ブランチ取得後、同じ関数を matrix 戦略へ移植
