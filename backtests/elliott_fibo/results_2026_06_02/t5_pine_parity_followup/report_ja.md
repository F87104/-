# H4 T5 Pine/Python 照合フォローアップ

作成日: 2026-06-02

## 結論

外部AIが提示した修正版Pineは、そのまま採用しない。

理由は、照合修正だけでなく、実戦用に入れていた `SIGNAL` / `LONG FILLED` / `EXIT` ラベル、価格入り `alert()`、状態テーブル、運用判定表示まで削られていたため。本番用の視認性と運用性が落ちる。

## より良い改善方針

売買ロジックを無理に4件へ合わせ込むのではなく、まずは非破壊の照合監査モードを追加する。

追加したもの:

- `Python照合監査` グループ
- `SIGNAL/SKIPに監査情報を追加`
- ラベルに `Audit key`, `V start/low`, `Candidate` を表示

2026-06-02 追記:

- 監査情報をデフォルトONへ変更
- `監査ON時は見送りラベルを隠す` を追加
- SIGNALラベルに `Signal time`, `V times`, `Candidate time` を追加

目的は、SKIPラベルの山に実トレードが埋もれないようにし、Python期待値4件とPine側6件を画面上で直接比較できる状態にすること。

これにより、TradingView側で余計に出る2件について、Python側の `candidate_key = v_start_i-v_extreme_i` 相当の構造と照合しやすくなる。

## 次の確認手順

1. TradingViewで `Python照合モード` をONにする。
2. `SIGNAL/SKIPに監査情報を追加` をONにする。
3. USDJPY H4で余計に出る2件のラベルを確認する。
4. `Audit key`, V起点/安値、候補終値、シグナル時刻をPythonの `normal_live_trades.csv` と比較する。

Python期待値は以下の4件:

| signal_time | entry_time | trigger_type |
|---|---|---|
| 2016-12-07 04:00 | 2016-12-07 08:00 | stagnation |
| 2018-10-30 00:00 | 2018-10-30 04:00 | rebreak |
| 2022-10-06 12:00 | 2022-10-06 16:00 | rebreak |
| 2024-04-08 00:00 | 2024-04-08 04:00 | stagnation+rebreak |

## 判断

この段階でロジック修正を急がない。

余計な2件が、データ元差、ピボット候補差、Broad Block差、または実際のバグのどれかを分けてから、最小修正だけを入れる。
