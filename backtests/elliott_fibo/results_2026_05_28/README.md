# 2026-05-28 ショート側研究結果

Status: 検証途中。ここにある手法はまだ本番採用ではない。

このフォルダは、H4 T5 + MACD + BB のショート側研究をあとから再開するための結果置き場です。CSVは検証の生データ、`report_ja.md` は各検証の要約です。

## まず読むもの

1. 全体の研究ノート: `../../../docs/research/short_side_research_2026-05-28_in_progress.md`
2. 現時点の本命候補: `monthly_low_rebreak_short/report_ja.md`
3. 不採用理由の確認: `t5_short_mirror_validation/report_ja.md`

## フォルダ一覧

| フォルダ | 状態 | 何を検証したか | 結論 |
|---|---|---|---|
| `t5_short_mirror_validation/` | 不採用 | ロング版 H4 V候補 T5 + MACD + BB を上下反転したショート | 実戦ミラー条件は 18 trades / -12.82R / PF 0.15。明確に使わない |
| `t5_short_high_vol_continuation/` | 観察候補 | ミラーを捨て、高ボラ下落継続だけを狙うショート | プラス断片はあるがOOS不足。採用ではなく研究継続 |
| `t5_short_practical_hardening/` | 観察候補 | 高ボラ下落継続の出口や撤退を実戦向けに調整 | DDは抑えられるが、利益が薄くOOS不足 |
| `monthly_low_rebreak_short/` | 検証途中の本命候補 | 1ヶ月から3ヶ月の安値更新後、戻り再下落または安値停滞下抜けを売る | 1ヶ月安値更新後の安値停滞下抜けが最有望 |
| `low_break_lookback_exit_study/` | 検証途中の深掘り | 安値更新期間を0.5ヶ月から6ヶ月に拡張し、レンジ/トレンド分類と利確基準を比較 | 1ヶ月が最も強く、3ヶ月以上は強くならない。サポート保持60-119本が有望 |
| `h1_low_break_lookback_exit_study/` | H1検証 | H4本命をH1へ換算し、0.5〜6ヶ月lookbackと利確基準を比較 | H1安値停滞型は弱い。別候補としてGBPJPY 0.5ヶ月rebreakが有望 |
| `h4_stagnation_deep_dive/` | H4安値停滞の別角度分析 | 停滞レンジ品質、下抜け足、サポート保持期間、直後フォロースルー、出口管理を比較 | サポート保持60-119本、下抜け終値位置、12本以内1R未達撤退が次の検証候補 |
| `h4_stagnation_followup_validation/` | H4安値停滞の追加検証 | 同一通貨・同一時刻の重複を除去し、通貨除外、support age、時間切れ撤退を再評価 | Primary L120 core4 + 固定2Rが最もきれい。support60-119は強いが実質8件 |
| `h4_stagnation_precision_hardening/` | H4安値停滞の精度向上 | Pine実装に向けて下抜け深さ、終値位置、新しい支持線の強さを検証 | core4厳選フィルタは8 trades / +15.71R / 全勝。ただし件数不足 |

## 現時点の本命候補

`monthly_low_rebreak_short/` と `low_break_lookback_exit_study/` の中では、以下が暫定ベストです。

| ルール | trades | winrate | total_r | avg_r | PF | maxDD |
|---|---:|---:|---:|---:|---:|---:|
| L120_STAG_ONLY__ADX30_RISK_LE1_5_BBW3_8 | 18 | 61.11% | +13.61R | +0.76R | 2.78 | 3.41R |

意味:

- H4で過去120本、約1ヶ月の安値を更新。
- すぐに売らず、安値付近の停滞を待つ。
- 停滞レンジを下抜けたらショート。
- ADX>=30、BB幅3から8ATR、損切り幅1.5ATR以下で絞る。
- TPは2R。

この候補は、戻り高値再ブレイクよりも安値停滞下抜けの方が重要です。

追加検証では、3ヶ月や6ヶ月へ伸ばしても成績は強くなりませんでした。むしろ、安値がH4で60-119本ほど保持されたあとに割れる形が最も良く、これは「長期トレンドの途中」より「見えているサポートが割れる」形に近いです。

H4安値停滞の別角度分析では、6本以内に停滞レンジ中央へ戻るものは弱い傾向がありました。ただし即撤退は期待値を削るため、実戦管理としては「12本以内に1Rへ届かなければ撤退」の方が候補です。通貨はGBPJPYが最も強く、AUDJPY/USDJPYは除外候補です。

ただし追加検証で重複除去すると、広いPracticalやsupport60-119の件数は大きく減りました。実戦単位で最もきれいに残ったのは `Primary L120 core4` で、11 trades / +12.55R / PF 4.98 / maxDD 1.08R。core4は GBPJPY, CHFJPY, XAUUSD, EURJPY です。support60-119は8 trades / +9.66R、12本撤退で +11.23R と強いものの、件数不足のため観察タグ扱いです。

精度向上検証では、core4に `下抜け深さ>=0.10ATR`、`下抜け足の終値位置<=0.50`、`support age<=10なら下抜け深さ>=0.20ATR` を加えると、8 trades / +15.71R / 全勝になりました。これは本番採用ではなく、Pineの `厳選候補` ラベルとして扱うのが現実的です。

## まだ本番採用しない理由

- OOS 2025-2026 がまだ1件だけ。
- 2017年に負けが集中している。
- 通貨別では GBPJPY が強いが、件数が少なく過信できない。
- TrendBreakV1 との同時発生時の優先順位が未定。
- Pine可視化とフォワード記録がまだ未整備。

## 再開するときの流れ

1. このREADMEを読む。
2. `../../../docs/research/short_side_research_2026-05-28_in_progress.md` を読む。
3. `monthly_low_rebreak_short/report_ja.md` で暫定候補を確認する。
4. 必要なら `monthly_low_rebreak_short/trades.csv` で個別トレードを見る。
5. 期間・利確基準を見る場合は `low_break_lookback_exit_study/report_ja.md` を読む。
6. H4安値停滞の質と出口管理を見る場合は `h4_stagnation_deep_dive/report_ja.md` を読む。
7. 重複除去後の実戦寄り評価は `h4_stagnation_followup_validation/report_ja.md` を読む。
8. Pine実装向けの厳選条件は `h4_stagnation_precision_hardening/report_ja.md` を読む。
9. H1版を見る場合は `h1_low_break_lookback_exit_study/report_ja.md` を読む。
10. Pine可視化または追加OOS検証に進む。

## 再実行コマンド

OHLCデータ `F87104_test` はGit管理外です。再実行するには、リポジトリ直下に `F87104_test` がある状態にします。

```bash
python3 backtests/elliott_fibo/run_t5_short_mirror_validation.py
python3 backtests/elliott_fibo/run_t5_short_high_vol_continuation.py
python3 backtests/elliott_fibo/run_t5_short_practical_hardening.py
python3 backtests/elliott_fibo/run_monthly_low_rebreak_short.py
python3 backtests/elliott_fibo/run_low_break_lookback_exit_study.py
python3 backtests/elliott_fibo/run_h1_low_break_lookback_exit_study.py
python3 backtests/elliott_fibo/run_h4_stagnation_deep_dive.py
python3 backtests/elliott_fibo/run_h4_stagnation_followup_validation.py
python3 backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py
```

## ファイルの見方

| ファイル | 意味 |
|---|---|
| `report_ja.md` | 人間向けの要約。まずここを見る |
| `summary.csv` | 条件ごとの成績比較 |
| `trades.csv` | 個別トレード一覧 |
| `by_symbol.csv` | 通貨別集計 |
| `by_trigger.csv` | トリガー別集計 |
| `selected_*` | 実戦化監査で選んだ候補の詳細 |
| `lookback_strength.csv` | 安値更新期間ごとの強さ |
| `exit_summary.csv` | 利確/撤退ルールごとの比較 |
| `regime_summary.csv` | 事前状態がレンジ割れかトレンド継続かの比較 |
| `support_age_summary.csv` | サポート保持期間別の比較 |
| `stagnation_feature_summary.csv` | H4安値停滞をレンジ幅、下抜け足、通貨、期間、戻り方で分解した集計 |
| `stagnation_management_summary.csv` | H4安値停滞の出口管理比較 |
| `rule_exit_summary.csv` | 重複除去後の入口ルールと出口の比較 |
| `time_stop_sweep.csv` | 4-24本の1R未達撤退スイープ |
| `symbol_exclusion_sweep.csv` | 通貨除外ごとの比較 |
| `failure_audit.csv` | 厳選条件がどの負けを除外したかの監査 |
| `threshold_sweep.csv` | 下抜け深さとfresh support条件の感度 |
