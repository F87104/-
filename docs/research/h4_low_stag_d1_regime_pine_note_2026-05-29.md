# H4 Low Stag Short D1 Regime Pine Note

Status: 検証途中。Python検証で見つかった `前日D1 RSI 35-55` フィルタをTradingViewで確認するためのPine実装メモ。

## 追加したPine

- `pine/research/h4_low_stag_short_d1_regime_strategy.pine`

## 目的

H4安値停滞ショートに、前日確定の日足RSI地合いを重ねる。

Pythonで有望だった本線:

- 対象: `Core4+SILVER`
- H4候補: practical条件
- D1条件: 前日確定D1 RSIが35から55
- H4品質: `break_depth >= 0.10ATR` かつ `break_close_location <= 0.50`
- H4厳選: H4品質 + `support_age > 10 or break_depth >= 0.20ATR`

## TradingView推奨設定

- チャート: H4
- 対象通貨: `Core4+SILVER`
- 検証するラベル: まず `D1厳選`
- 見送り理由ラベル: ON
- 前日D1 RSI下限: `35`
- 前日D1 RSI上限: `55`
- lookback: まず全ON。優先順は `120 -> 90 -> 180 -> 240 -> 60 -> 360 -> 480 -> 720`

## エントリーしない理由の見方

Pine版には、候補が出たのに現在の検証モードでエントリーしない場合の診断を追加した。

- `見送` ラベル: rawの安値停滞候補は出たが、実戦フィルタまたはD1条件で落ちたバー。
- `No entry`: 見送り候補の累計。
- `Now reason`: 直近バーの状態。候補以前なら `安値更新なし`、`安値更新直後: 条件待ち`、`監視中: 戻り/停滞/再下抜け待ち` のように表示。
- `Last reason`: 最後に候補が落ちた理由。

主な見送り理由:

- `ADX不足`
- `Risk過大`
- `BB幅不足` / `BB幅過大`
- `下抜け浅い`
- `終値位置が高い`
- `新しい安値で深さ不足`
- `前日D1 RSI範囲外`
- `対象通貨外`
- `検証期間外/年末年始除外`
- `保有中または決済直後`

## Python検証結果

`practical_no_AUD_USD` baseline:

- 37 trades
- 勝率 43.24%
- 総R +8.36R
- PF 1.37
- maxDD 4.76R

`D1 RSI35-55 + H4品質`:

- 16 trades
- 勝率 75.00%
- 総R +18.90R
- PF 5.56
- maxDD 1.07R

`D1 RSI35-55 + H4厳選`:

- 14 trades
- 勝率 78.57%
- 総R +18.14R
- PF 6.84
- maxDD 1.07R

## 実装上の注意

- D1 RSIは未確定日足を使わない。Pineでは `request.security(..., "D", ta.rsi(close, 14)[1])`。
- Pythonの practical 集合は複数lookbackを同一時刻で重複除去している。Pineでは優先順で最初に通ったlookbackを選ぶ。
- TradingViewのデータ範囲、タイムゾーン、OANDA/CFD銘柄差で完全一致しない可能性があるため、まず件数とシグナル位置の目視照合を行う。
- H1戻り高値切り下げ条件は件数が7件程度まで減るため、最初から必須にしない。追加タグとして比較する。

## 次に見ること

1. GBPJPY, CHFJPY, EURJPY, XAUUSD, SILVERで `D1厳選` の位置を確認。
2. Python候補トレード一覧 `candidate_trades.csv` とTradingViewのシグナル時刻を比較。
3. 余計なシグナルが多ければ、lookbackを `60/90/120/180` に絞る。
4. Pine上で近い結果になったら、アラート用indicator版へ分離する。
