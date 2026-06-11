# H4 Low-Stag Short Pine Parity Issue

作成日: 2026-05-29

Status: 未解決。Python検証を正として、Pine strategyのシグナル一致を監査中。

## 結論

H4 1ヶ月安値更新後の安値停滞ブレイクショートは、Python検証では有望だが、TradingView Pine strategyへの移植がまだ一致していない。

現時点では、TradingView上の `勝ちトレード57.14% / PF 2.447` は採用判断に使わない。これはPython期待シグナルと一致していない状態の仮成績。

## 問題

Python側の期待値では、GBPJPY H4の実戦候補は4件。

しかしTradingViewのPine strategyでは、GBPJPY H4で7件出ている。

つまり、Pineが余計な3件を拾っている可能性が高い。

## Python期待値

Python側の正解ファイル:

- `backtests/elliott_fibo/results_2026_05_28/h4_low_stag_pine_parity_audit/expected_gbpjpy_practical.csv`
- `backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/primary_trades.csv`

GBPJPY practical 期待4件:

| signal_time | entry_time | exit_time | result | support_age | depth_atr | close_loc | risk_atr | bb_width_atr | adx |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 2016-10-10 00:00 | 2016-10-10 04:00 | 2016-10-11 16:00 | TP | 48 | 0.425 | 0.107 | 1.376 | 7.061 | 42.03 |
| 2018-05-25 04:00 | 2018-05-25 08:00 | 2018-05-29 04:00 | TP | 68 | 0.173 | 0.232 | 1.401 | 7.881 | 39.09 |
| 2023-12-13 08:00 | 2023-12-13 12:00 | 2023-12-13 16:00 | TP | 73 | 0.206 | 0.231 | 1.422 | 4.293 | 30.06 |
| 2025-01-15 04:00 | 2025-01-15 08:00 | 2025-01-17 04:00 | TP | 3 | 0.424 | 0.487 | 1.489 | 4.522 | 46.02 |

期待成績:

| case | trades | winrate | total_r | avg_r | PF |
|---|---:|---:|---:|---:|---:|
| GBPJPY practical | 4 | 100.00% | +7.92R | +1.98R | inf |

## 最終フィルタ

最終的に比較すべき実戦候補条件:

| 条件 | 値 |
|---|---|
| timeframe | H4 |
| direction | short |
| lookback | 120 bars |
| trigger_mode | stagnation |
| symbols | core4: GBPJPY, CHFJPY, XAUUSD/GOLD, EURJPY |
| ADX | >= 30 |
| risk_atr_at_signal | <= 1.5 |
| BB width | 3ATRから8ATR |
| break_depth_atr | >= 0.10 |
| break_close_location | <= 0.50 |
| holiday filter | 12/15から1/10を除外 |
| entry | signal bar close confirmed, next bar open |
| stop | stagnation zone high + 0.25ATR |
| target | 2R |

## 重要な注意点

`break_depth_atr` は、初回の1ヶ月安値ブレイク足の深さではなく、最終CSVでは停滞下抜け足で再計算している。

正しい最終判定:

```text
break_depth_atr = (stagnation_zone_low - signal_close) / ATR_at_signal
break_close_location = (signal_close - signal_low) / (signal_high - signal_low)
```

この点を間違えると、PythonとPineの実戦候補がずれる。

## 見るべきPythonコード

| ファイル | 見る箇所 | 役割 |
|---|---|---|
| `backtests/elliott_fibo/run_monthly_low_rebreak_short.py` | `first_low_breaks` | 初回1ヶ月安値ブレイク判定 |
| `backtests/elliott_fibo/run_monthly_low_rebreak_short.py` | `low_break_signal` | ブレイク後の戻り、停滞、SL/TPの基本判定 |
| `backtests/elliott_fibo/run_monthly_low_rebreak_short.py` | `run_spec` | ポジション重複除外とトレード生成 |
| `backtests/elliott_fibo/run_h4_stagnation_deep_dive.py` | `add_stagnation_features` | `break_depth_atr`, `break_close_location` の最終再計算 |
| `backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py` | `base_primary` | ADX/risk/BB幅/重複除去の本命母集団 |
| `backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py` | `quality_mask` | 実戦候補フィルタ |
| `backtests/elliott_fibo/run_h4_stagnation_precision_hardening.py` | `strict_mask` | 厳選候補フィルタ |

## 見るべきPineコード

Pine strategy:

- `pine/research/h4_low_stagnation_short_strategy.pine`

最新タイトル:

```text
H4 Low Stag Short Strategy [Parity Check v3]
```

v2/v3で追加した監査機能:

| 表示/設定 | 意味 |
|---|---|
| `PY期待` | Python期待4件のシグナル時刻 |
| `一致` | PineロジックがPython期待時刻と同じバーで出た |
| `余計` | Pineだけが出した余計なロジックシグナル |
| `発注モード=Pineロジック` | 通常のPine移植ロジックで発注 |
| `発注モード=GBPJPY Python期待のみ` | GBPJPY期待4件だけで発注。照合専用 |
| `Logic signals` | Pineロジックのシグナル数 |
| `PY expected seen` | チャート上で見えたPython期待件数 |
| `Matched` | 期待時刻と一致した件数 |
| `Extra` | Pineだけが出した余計な件数 |
| `canScan` | ポジション中と決済バーでは新規ブレイク/停滞判定を止める |

## 切り分け手順

1. TradingViewでGBPJPY H4を開く。
2. Pineを最新版に丸ごと貼り替える。
3. スクリプト名が `[Parity Check v3]` になっていることを確認する。
4. `発注モード=GBPJPY Python期待のみ` にする。
5. 4件だけ発注されるか確認する。
6. 4件にならない場合、TradingViewのH4足区切り、時刻、データ、約定処理がPythonと違う可能性が高い。
7. 4件になる場合、`発注モード=Pineロジック` に戻す。
8. `余計` ラベルの3件を確認し、表示された `ADX`, `BBW`, `Risk`, `Depth`, `CloseLoc`, `Age`, `After` をPython条件と比較する。

## 疑う箇所

優先度順:

1. Pineの `break_depth_atr` がPython最終CSVと同じ定義になっているか。
2. Pineの `break_close_location` がシグナル足の位置で計算されているか。
3. Pineのactive stateがPythonの `run_spec` と同じように、トレード中の新規ブレイクを無視しているか。
4. H4足の区切りがPythonの `resample(..., label="left", closed="left")` とTradingView/OANDAで一致しているか。
5. ADX初期化がPythonの `ewm(alpha=1/length, adjust=False, min_periods=length)` とPine `ta.dmi` で十分近いか。
6. ATR初期化がPythonとPineで十分近いか。
7. BB幅がPython pandas標本標準偏差とPine `ta.stdev(close, length, false)` で一致しているか。
8. TradingView側で古い入力設定が残っていないか。

## 現時点の判断

この不一致が解消するまで、Pine strategyのPF、勝率、総損益は研究成績として扱わない。

Python検証上の手法自体は候補として残すが、Pine移植は未完了。

## 関連コミット

| commit | 内容 |
|---|---|
| `3d5264b` | Pine parity audit CSV/reportを追加 |
| `28b6eb7` | Python期待4件との照合マーカーをPineに追加 |
| `6419864` | Pineロジック発注とPython期待発注を分離 |
| v3 | 決済バーまで新規判定を抑制し、Pythonの `in_pos_until` に寄せる |
