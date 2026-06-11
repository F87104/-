# WaveBox Red-Team Audit 2026-05-26

## 結論

結果は良いが、そのまま実力値として信じない。

コード上の明確な未来参照・同足ENTRY・TP優先の過大評価は見つからない。一方で、成績は時間フィルターと近年相場に強く支えられている。特にOOS 2025-2026は6件だけで、全勝しているため統計的な証拠としては弱い。

## Passed Integrity Checks

| check | bad_count |
| --- | --- |
| entry_i == signal_i + 1 | 0 |
| setup_age >= 0 | 0 |
| risk > 0 | 0 |
| stop is on correct side | 0 |
| target equals 1.5R from next open | 0 |
| no overlapping strict trades | 0 |
| same-bar TP/SL counted as SL | 0 |

## Hour Filter Dependence

| label | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- |
| Strict no hour filter | 98 | 51.02 | 24.63 | 0.25 | 1.51 | 6.93 |
| Strict exclude 1 | 77 | 61.04 | 38.22 | 0.50 | 2.24 | 3.13 |
| Strict exclude 1/6 | 71 | 64.79 | 41.93 | 0.59 | 2.64 | 3.13 |
| Strict exclude 1/6/14 | 69 | 65.22 | 41.47 | 0.60 | 2.69 | 3.13 |

## Period Dependence

| label | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- |
| Strict all | 69 | 65.22 | 41.47 | 0.60 | 2.69 | 3.13 |
| Strict 2014-2022 | 54 | 59.26 | 24.28 | 0.45 | 2.08 | 3.13 |
| Strict 2023+ | 15 | 86.67 | 17.19 | 1.15 | 9.42 | 1.03 |
| GO A+ or clean A | 38 | 68.42 | 26.09 | 0.69 | 3.15 | 4.18 |
| GO only pre-2023 | 29 | 62.07 | 15.29 | 0.53 | 2.38 | 4.18 |
| GO only 2023+ | 9 | 88.89 | 10.80 | 1.20 | 11.51 | 1.03 |

## Win-Rate Confidence

| label | wins | trades | win_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- |
| Strict all | 45 | 69 | 65.22 | 53.45 | 75.38 |
| GO A+ or clean A | 26 | 38 | 68.42 | 52.54 | 80.92 |
| GO only pre-2023 | 18 | 29 | 62.07 | 44.00 | 77.31 |
| Strict OOS 2025-2026 | 6 | 6 | 100.00 | 60.97 | 100.00 |

## Exit Count

| exit_reason | trades |
| --- | --- |
| TP | 45 |
| SL | 23 |
| time_exit | 1 |

## Red Flags

- 時間フィルターなしでは `Strict` はPF1.50まで落ちる。つまり1時/6時/14時除外の寄与が大きい。
- 2023年以降がかなり良すぎる。近年のUSDJPYトレンド環境に適合している可能性がある。
- `GO A+ or clean A` は38件しかなく、95%信頼区間は広い。
- 2025-2026のOOSは6件全勝だが、件数が少なく、実戦証拠にはならない。
- この手法は作成過程で複数条件を見ているため、厳密な未使用OOSではない。

## Practical Verdict

- 実装ミスで勝っている疑いは低め。
- ただし結果は過信禁止。実力値はPF3ではなく、まずPF1.5-2.0程度に割り引いて見る。
- 実弾は `GO A+ / GO A` の20-30件フォワードが取れるまで小ロット。
- 20件まではパラメータ変更禁止。変更すると検証がまた最初からになる。