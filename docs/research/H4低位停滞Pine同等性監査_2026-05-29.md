# H4 Low Stag Pine Parity Audit

Status: 検証途中。Python検証の `D1 RSI35-55 + H4厳選 + 60本lookback厳格化` を、TradingView Pineへ正確に落とし込めるかの監査メモ。

## 結論

シグナル条件はPineへかなり正確に落とし込める。

ただし、バックテスト成績まで完全一致させるにはTradingViewの約定モデル差が残る。特にPythonは「シグナル足の次の足の始値で約定し、その始値から2Rターゲットを計算」する。Pineはシグナル足の終値時点で注文を出すため、次足始値が確定する前に完全なTP価格を知ることはできない。

今回のPineでは `calc_on_order_fills=true` を使い、約定後に `strategy.position_avg_price` からTPを再計算する形へ寄せた。

## Python定義

入口:

- H4のみ。
- Pineでは `H4以外は停止` をONにする。H1ではlookback本数の意味が変わるため照合対象外。
- `trigger_mode=stagnation`。
- lookback優先順: `120 -> 90 -> 180 -> 240 -> 60 -> 360 -> 480 -> 720`。
- 同じ通貨・同じentry_timeは優先順で1件だけ残す。
- practical: `ADX>=30`、`risk_atr_at_signal<=1.5`、`BB幅 3-8ATR`。
- H4品質: `break_depth_atr>=0.10`、`break_close_location<=0.50`。
- H4厳選: H4品質 + `support_age>10 or break_depth_atr>=0.20`。
- D1: 前日確定D1 RSIが `35-55`。
- 60本厳格化: `lookback != 60 or (support_age<=24 and break_depth_atr>=0.25)`。

注意:

- ここでの `break_depth_atr` は、停滞ゾーン安値からシグナル足終値までの下抜け深さ。
- `break_close_location` は、シグナル足の中で終値がどれだけ下側にあるか。
- `support_age` は、最初に安値更新した時点で、割った安値が何本前に作られていたか。

## Pine実装で合わせた点

- `request.security(..., "D", ta.rsi(close, 14)[1])` で未確定日足を使わない。
- H4以外ではシグナルを止める。
- 複数lookbackはPythonと同じ優先順で選択。
- `60本lookbackを厳格化` は、lookback優先順で候補を選んだ後に適用する。60本を除外した後に、後順位lookbackへ乗り換えない。
- 見送り理由に `60本条件不足` を表示。
- `process_orders_on_close=false` で、シグナル足の次足約定に寄せる。
- `calc_on_order_fills=true` で、約定後に実際の `strategy.position_avg_price` からTPを再計算。

## 残る差分

完全一致を阻む可能性があるもの:

- TradingViewとPython元データのOHLC差。
- OANDA/CFD銘柄名やセッション差。
- タイムゾーンと日足確定時刻の差。
- TradingViewの同一バー内の約定順序。PythonはH4足のOHLCで `SL優先 -> TP優先` の順に判定している。
- リスク%数量計算を使う場合、Pineはシグナル時点では次足始値を知らないため、Pythonの厳密なリスク計算とはズレる。照合中は固定数量推奨。

## 照合手順

1. H4チャートで対象銘柄を開く。
2. `D1厳選`、`Core4+SILVER`、`H4以外は停止=ON`、`60本lookbackを厳格化=ON` にする。
3. `candidate_trades.csv` ではなく、今回の厳選結果 `current_d1_strict_failure_audit.csv` の `keep_with_l60_guard=True` の11件と照合する。
4. まず成績ではなく、シグナル位置とlookbackを合わせる。
5. 位置が合った後に、SL/TPの価格とエグジット理由を見る。

## 判定

実戦アラート用のシグナル抽出としてはPine化可能。

バックテスト成績の完全一致は、TradingViewの約定モデルとデータ差があるため保証しない。最初の合格基準は「11件前後のシグナル位置が一致すること」とする。
