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

## 現時点の本命候補

`monthly_low_rebreak_short/` の中では、以下が暫定ベストです。

| ルール | trades | winrate | total_r | avg_r | PF | maxDD |
|---|---:|---:|---:|---:|---:|---:|
| L120_STAG_ONLY__ADX30_RISK_LE1_5_BBW3_8 | 18 | 55.56% | +10.62R | +0.59R | 2.22 | 3.41R |

意味:

- H4で過去120本、約1ヶ月の安値を更新。
- すぐに売らず、安値付近の停滞を待つ。
- 停滞レンジを下抜けたらショート。
- ADX>=30、BB幅3から8ATR、損切り幅1.5ATR以下で絞る。
- TPは2R。

この候補は、戻り高値再ブレイクよりも安値停滞下抜けの方が重要です。

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
5. Pine可視化または追加OOS検証に進む。

## 再実行コマンド

OHLCデータ `F87104_test` はGit管理外です。再実行するには、リポジトリ直下に `F87104_test` がある状態にします。

```bash
python3 backtests/elliott_fibo/run_t5_short_mirror_validation.py
python3 backtests/elliott_fibo/run_t5_short_high_vol_continuation.py
python3 backtests/elliott_fibo/run_t5_short_practical_hardening.py
python3 backtests/elliott_fibo/run_monthly_low_rebreak_short.py
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

