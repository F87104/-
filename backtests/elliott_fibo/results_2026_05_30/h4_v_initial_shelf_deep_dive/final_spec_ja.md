# H4 V Initial Shelf Breakout 最終仕様書

## 判定

本番運用候補。ただし通常ロットはまだ早い。Pine照合後、0.25Rからフォワード検証。

採用理由は、単なるV底買いではなく、売りが失敗したあとに上側で棚を作り、崩れずに再点火する構造が残っているため。
一方で、2018-2021の開発分割では弱く、34件だけでは年別の偏りを吸収できない。

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

## 採用しない最適化

- 棚7本はPFが上がるが、20件前後まで件数が落ちるため暫定不採用。
- 棚幅を1.2ATRまで絞る案は成績が良いが、5件しかなく不採用。
- body/close条件の過度な厳格化は、勝ち負けの差分が小さいため不採用。
- SL0.4ATR + 最大保有12/18本は有望だが、入口条件ではなく出口研究として別管理。
- ADX<=22は有望な監視バリアント。ただし本線はまずADX<=26の再現性を優先。

## 監視バリアント

フォワードでは本線と同時に、以下をラベルだけ出して比較する。

- `ADX22`: ADX14 <= 22、EMA50傾き条件なし、60本レンジ幅 <= 20ATR
- `ShelfTight`: 棚幅 <= 1.5ATR
- `ExitFast`: SL 0.4ATR、最大保有18本、TP 1.5R

これらは本線より成績がよい可能性があるが、今は「発見」として扱い、実運用ルールへ昇格させない。

## Pine実装注意

- pivotはconfirmedのみ。`ta.pivothigh/low(left, right)` の検出足は `bar_index - right`、利用可能になるのは現在足。
- 棚はシグナル足を含めず `high[1]` から過去6本で計算。
- strategy entryはシグナル足で注文、約定は次足始値想定。
- TPはEntry約定価格が確定してから計算する。
- Python照合用に signal_time, v_start_time, v_low_time, shelf_high, shelf_low, stop をラベル/テーブル表示する。
