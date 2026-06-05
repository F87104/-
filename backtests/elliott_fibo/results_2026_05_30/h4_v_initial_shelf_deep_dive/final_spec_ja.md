# H4 V Initial Shelf Breakout 最終仕様書

## 判定

本番運用候補。ただし通常ロットはまだ早い。Pine照合後、0.25Rからフォワード検証。

## 推奨仕様

- 時間足: H4
- 対象: USDJPY, EURJPY, GBPJPY, AUDJPY
- 除外: XAUUSD, CHFJPY, SILVER
- 方向: ロングのみ
- V条件: confirmed pivot high -> confirmed pivot low
- pivot width: 3
- 下落幅 >= 2.8ATR
- 下落速度 >= 0.25ATR/本
- 回復率: 65%から125%
- 回復速度 >= 下落速度
- V谷後、V谷 - 0.10ATRを下抜けない
- V前環境: ADX14 <= 26, EMA50傾き <= 1.2ATR/20本, Close-EMA50 <= 3ATR, 60本レンジ幅 <= 16ATR
- 棚: V候補成立後36本以内、直近6本
- 棚幅 <= 1.8ATR
- 棚安値 >= V谷 + 下落幅 x 0.50 - 0.05ATR
- Entry signal: close > 棚高値 + 0.05ATR, 実体 >= 40%, 終値位置 >= 60%
- Entry: 次足始値
- SL: 棚安値 - 0.25ATR
- TP: Entry基準 1.5R を推奨。36d90e6再現ではSignal close基準。
- 最大保有: 120本を基準。短期最大保有は別途exit研究。
- 同一通貨で1ポジションのみ

## Pine実装注意

- pivotはconfirmedのみ。`ta.pivothigh/low(left, right)` の検出足は `bar_index - right`、利用可能になるのは現在足。
- 棚はシグナル足を含めず `high[1]` から過去6本で計算。
- strategy entryはシグナル足で注文、約定は次足始値想定。
- TPはEntry約定価格が確定してから計算する。
- Python照合用に signal_time, v_start_time, v_low_time, shelf_high, shelf_low, stop をラベル/テーブル表示する。