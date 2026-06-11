# D1 Trap Delayed H4 Shelf Strict

作成日: 2026-05-30

## 結論

現時点で私が一番自信を持って提案できる新候補は、**D1 Trap Delayed H4 Shelf Strict**。

これはV字を直接買う手法ではありません。D1で120本級の安値割れが否定されたあと、すぐには買わず、30日以上あとにH4で「急落V -> 上側の棚 -> 棚高値ブレイク」が出た場所だけを買います。

本質は、**D1で売りが一度否定され、その後もしばらく価格が崩れず、H4で売り直しが失敗して再点火する局面**です。

## 最終候補

| rule | trades | winrate | total_r | avg_r | pf | max_dd | oos |
|---|---:|---:|---:|---:|---:|---:|---:|
| selected_CURRENT_A30_180_SIGADX30 | 9 | 100.00% | +13.35R | +1.48R | inf | 0.00R | +4.46R |
| selected_CURRENT_A30_180 | 12 | 83.33% | +12.81R | +1.07R | 7.30 | 2.03R | +4.46R |
| selected_CURRENT_A30_240_SIGADX30 | 10 | 90.00% | +12.33R | +1.23R | 13.00 | 1.03R | +4.46R |

採用候補は `selected_CURRENT_A30_180_SIGADX30`。件数は少ないため本番通常ロットではなく、Pine照合とフォワード確認用の準本命です。

## ルール仕様

対象:

- H4
- USDJPY, EURJPY, GBPJPY, AUDJPY
- XAUUSD, CHFJPY, SILVER は除外

D1文脈:

- D1で120本安値の下抜け否定を検出
- 採用する否定:
  - 安値をヒゲで割って、終値で120本安値の上へ戻る
  - 終値で120本安値を割ったあと、6本以内に終値で上へ戻る
- D1否定足は実体比率35%以上、終値位置60%以上
- Trap確定翌日から30日未満は入らない
- Trap確定翌日から180日を超えたら文脈失効

H4エントリー:

- confirmed pivot high -> confirmed pivot low の急落Vを検出
- 下落幅 >= 2.8ATR
- 左肩速度 >= 0.25ATR/本
- 右肩速度 / 左肩速度 >= 1.0
- 回復率 0.65から1.25
- V安値後の安値更新は 0.10ATR まで
- V前は過熱トレンドではない
  - ADX14 <= 26
  - EMA50傾き <= 1.2ATR/20本
  - Close-EMA50 <= 3ATR
  - 60本レンジ幅 <= 16ATR
- V後に6本の棚を作る
- 棚幅 <= 1.8ATR
- 棚安値がVの50%回復ラインを維持
- 棚高値を終値で0.05ATR上抜け
- ブレイク足の実体比率 >= 40%
- ブレイク足の終値位置 >= 60%
- シグナル足ADX14 <= 30

売買:

- Entry: 次H4足始値
- SL: 棚安値 - 0.25ATR
- TP: Entry基準 1.5R
- 最大保有: 120本
- 同一ポジション保有中は新規なし

## なぜこの形が良いか

D1 Trap単独は強くありませんでした。D1で売りが否定されても、その直後はまだ荒く、戻り売りも出やすい。

一方で、30日以上経ったあとにH4で急落Vが出て、さらに上側で6本の棚を作って崩れず、その棚を抜く形は意味が変わります。

これは「売られたのに下がらない」だけでなく、**売り直しが失敗して、買い戻しと追随買いが同時に入り始める形**です。

## 削った条件

- D1 Trap直後15日以内は採用しない
- D1 Trapから180日超は基本採用しない
- シグナルADX14 > 30 は採用しない
- SILVER追加は見送り
- XAUUSD/CHFJPYは引き続き除外

## 注意

この候補はかなりきれいですが、9件しかありません。数字は良いものの、統計的にはまだ完成ではなく、**PineでPythonのシグナル時刻と一致すること、2026年以降のフォワードで最低20件程度を記録すること**が必要です。

ただし、これまで見た候補の中では「なぜ勝ちやすいのか」を最も説明しやすい構造です。

## 成果物

- 検証コード: `backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py`
- レポート: `backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/report_ja.md`
- 全結果: `backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/summary_grid.csv`
- 選定トレード: `backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_trades.csv`
- 勝ち負け比較: `backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_win_loss_compare.csv`
- Pine研究版: `pine/research/d1_trap_h4_shelf_strict_strategy.pine`
