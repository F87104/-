# Sai H1 Backtest

Forex Testerを使わず、GitHubのCSVデータからSai手法の近似条件を検証するためのバックテストです。

## Data

データリポジトリ:

- `https://github.com/F87104/test.git`

CSV内の `<TICKER>` を銘柄名として読み取り、全データを1時間足OHLCへ正規化してから使います。GBPJPYデータには1分足が混ざっている年があるため、この正規化は必須です。

## Default Test

```bash
python3 backtests/sai_h1/backtest_sai_h1.py \
  --data-root ../fx-test-data \
  --out-dir backtests/sai_h1/results_2015_2024 \
  --start 2015-01-01 \
  --end 2024-12-31
```

デフォルトではUSDJPYを除外します。これは教材内で「Sai手法とドル円は相性がよくない」と説明されていたためです。

また、12月15日から1月10日も除外します。

## Outputs

- `data_coverage.csv`
  - 銘柄ごとのデータ範囲

- `trades.csv`
  - 全トレード明細
  - `method` に日本語の手法名が入ります

- `summary_by_symbol.csv`
  - 銘柄別集計

- `summary_by_method.csv`
  - 手法別集計
  - 例: `高値停滞`, `V字＋高値停滞`, `急な揺り戻し＋高値停滞`

- `summary_by_method_symbol.csv`
  - 手法 x 銘柄の集計

- `summary_by_setup.csv`
  - 内部ロジック名での集計

- `report.md`
  - 主要結果をMarkdownでまとめたもの

## Current Method Labels

- `高値停滞`
- `安値停滞`
- `抵抗線付近の高値停滞`
- `支持線付近の安値停滞`
- `値幅広めの高値停滞`
- `値幅広めの安値停滞`
- `V字＋高値停滞`
- `逆V字＋安値停滞`
- `急な揺り戻し＋高値停滞`
- `急な揺り戻し＋安値停滞`
- `レンジ抜け2回目以降のブレイクアウト`

## Visual Check In TradingView

TradingViewで視覚確認する場合は、以下のPineを開いてチャートに追加します。

- `pine/visual/sai_h1_visual_scanner.pine`

1時間足で使ってください。Pythonバックテストと完全一致ではなく、同じ思想で候補を表示する確認用インジケーターです。

## Interpretation

この検証は「Sai手法の完全再現」ではなく、文字起こしから作った機械的な近似条件です。

次にやるべきこと:

1. `summary_by_method_symbol.csv` で手法 x 銘柄の強弱を見る。
2. 成績の良い手法だけを残す。
3. `trades.csv` の負けトレードをTradingViewで目視確認する。
4. Pine側でシグナル位置を見ながら、停滞幅、V字、短中一致の条件を調整する。
