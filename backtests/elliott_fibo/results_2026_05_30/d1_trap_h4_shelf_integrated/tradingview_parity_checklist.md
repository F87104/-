# TradingView Parity Checklist

対象Pine: `pine/research/d1_trap_h4_shelf_strict_strategy.pine`

## 設定

- チャート: H4
- 銘柄フィルタ: 4通貨のみ
- D1 Trap: ON
- D1 lookback: 120
- D1有効期間: 30-180日
- H4 shelf bars: 6
- Shelf range: 1.8ATR
- Signal ADX max: 30
- TP: Entry基準 1.5R
- SL: 棚安値 - 0.25ATR

## 照合対象

Pythonの選定候補 `selected_CURRENT_A30_180_SIGADX30` は以下9件。

| symbol | expected entry_time | result |
|---|---|---:|
| EURJPY | 2015-04-27 16:00 | +1.49R |
| EURJPY | 2015-05-29 12:00 | +1.49R |
| AUDJPY | 2015-11-19 00:00 | +1.48R |
| GBPJPY | 2016-08-24 12:00 | +1.48R |
| EURJPY | 2016-10-04 00:00 | +1.48R |
| GBPJPY | 2024-10-09 12:00 | +1.49R |
| AUDJPY | 2025-03-17 08:00 | +1.48R |
| USDJPY | 2025-07-07 04:00 | +1.49R |
| USDJPY | 2025-09-24 08:00 | +1.48R |

## 確認手順

1. TradingViewで各通貨をH4にする。
2. Pineを追加し、期間を2015-2026にする。
3. Strategy Testerのトレード一覧で、上記 entry_time と同じ場所に `Long` が出るか確認する。
4. ずれる場合はまずD1 Trapラベルの発生日を確認する。
5. 次にH4 V候補、棚高値、シグナル足ADXを確認する。
6. シグナルは一致しているが損益がずれる場合は、Entry価格が次足始値か、TPがEntry基準かを確認する。

## 注意

Pineの `request.security()` はTradingViewの取引所タイムゾーン、週末足、データ提供元でD1確定タイミングが変わることがある。まずは「シグナル時刻一致」を最優先で見て、PFや勝率は一致確認後に使う。
