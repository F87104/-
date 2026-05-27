# Synapse 定義グリッド検証 所感

作成日: 2026-05-25

## 検証範囲

- 対象: USDJPY
- 元データ: `F87104_test/**/USDJPY_M5_*.csv`
- 期間: 2014-01-01 から 2026-05-22
- 時間足: M5 / M15 / M30 / H1 / H4
- OOS: 2025-01-01 以降

## 比較したA/B構造

- `classic_6pivot`: 既存検証に近い6pivot型。ロングは `L-H-L-H-L-H`
- `ihs_5pivot`: 小波の逆三尊/三尊を優先する5pivot型。ロングは `L-H-L-H-L`
- `role_ab_5pivot`: A/B役割線を優先する5pivot型。ロングは `H-L-H-L-H`

## 大きな結論

全組み合わせを単純合算すると、53,187件、勝率42.0%、合計 -891.6R。
ただしこれは同じ相場を多数の別ルールで重複売買した合算なので、ポートフォリオ評価ではない。

見るべきは「時間足 x 構造 x フィルタ x TP」の個別比較。

現時点で一番実装候補に近いのは、次の方向。

1. 時間足は M5 より H1 / M15 / H4 が良い
2. フィルタは `context` または `diag_break` が良い
3. TPは半値TP単独より、固定1.5R/2Rを併記して見るべき
4. A/B構造は `ihs_5pivot` が最も安定、`classic_6pivot` は少数精鋭、`role_ab_5pivot` はOOSで良いがISが不安定
5. `strict_synapse` は絞りすぎで件数が少なく、初期Pine条件には向かない

## フィルタ x TP

上位は次の通り。

| filter | TP | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| context | fixed_2R | 2184 | 40.34% | 26.19R | 0.012R | 1.02 | 64.10R |
| context | fixed_1_5R | 2216 | 44.04% | 9.37R | 0.004R | 1.01 | 49.19R |
| diag_break | half_wave | 75 | 48.00% | 6.87R | 0.092R | 1.16 | 12.16R |
| context | half_wave | 36 | 47.22% | 4.83R | 0.134R | 1.25 | 5.45R |

`context fixed_2R` は件数が多く、全体で唯一まとまってプラス。
ただし平均Rは薄いので、このまま実運用というより「Pine可視化の土台」として見る。

`half_wave` は件数が少ないが、候補を厳選すると平均R/PFが改善する。
裁量の目標線としては使えるが、自動売買の固定出口にはまだ弱い。

## 時間足別

| timeframe | filter | trades | win_rate | total_r | avg_r | pf |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| H1 | basic_role | 1251 | 44.04% | 91.24R | 0.073R | 1.14 |
| M15 | basic_role | 3806 | 42.54% | 83.78R | 0.022R | 1.04 |
| H1 | diag_break | 718 | 43.87% | 69.05R | 0.096R | 1.19 |
| H4 | context | 113 | 54.87% | 21.23R | 0.188R | 1.42 |
| M5 | basic_role | 9037 | 40.78% | -460.98R | -0.051R | 0.91 |
| M5 | diag_break | 4581 | 40.56% | -229.46R | -0.050R | 0.91 |

M5は候補が多すぎて、ノイズをかなり拾っている。
Synapseの初期Pineは、M5エントリーではなく、H1/M15/H4の波認識を優先したほうが良い。

## A/B構造別

有望な構造:

| structure | filter | TP | trades | win_rate | total_r | avg_r | pf |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ihs_5pivot | context | fixed_2R | 1368 | 40.50% | 39.68R | 0.029R | 1.05 |
| ihs_5pivot | context | fixed_1_5R | 1383 | 44.54% | 35.34R | 0.026R | 1.05 |
| classic_6pivot | diag_break | half_wave | 31 | 64.52% | 16.47R | 0.531R | 2.33 |
| classic_6pivot | context | half_wave | 18 | 61.11% | 10.44R | 0.580R | 2.36 |
| role_ab_5pivot | basic_role | fixed_2R | 3229 | 40.11% | 15.36R | 0.005R | 1.01 |

`ihs_5pivot + context` は件数と安定性のバランスが最も良い。
`classic_6pivot + half_wave` は件数が少ないが質が高く、裁量チェック用の候補表示に向いている。
`role_ab_5pivot` はOOSで良い局面があるが、全期間では薄い。

## OOSの目立つ組み合わせ

IS/OOSを分けると、次が目立つ。

| timeframe | structure | filter | TP | IS trades | IS R | OOS trades | OOS R |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| M15 | role_ab_5pivot | basic_role | fixed_2R | 626 | 25.43R | 65 | 19.61R |
| M5 | role_ab_5pivot | context | fixed_2R | 234 | 3.64R | 26 | 14.37R |
| M30 | ihs_5pivot | diag_break | fixed_2R | 309 | 22.77R | 41 | 7.63R |
| M30 | ihs_5pivot | context | fixed_1_5R | 198 | 20.36R | 23 | 6.79R |
| M30 | ihs_5pivot | context | fixed_2R | 196 | 22.07R | 23 | 5.20R |

OOSだけを見ると `role_ab_5pivot` が強く見える。
ただしM5/M30ではISが弱いものも多いので、過信せず「表示候補」として扱う。

## エントリー方式

| entry_mode | filter | TP | trades | win_rate | total_r | avg_r | pf |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B_plus_diag | diag_break | fixed_2R | 835 | 40.36% | 20.12R | 0.024R | 1.04 |
| B_plus_diag | basic_role | fixed_2R | 1039 | 41.19% | 17.17R | 0.017R | 1.03 |
| B_confirmed | context | fixed_1_5R | 1281 | 44.34% | 16.99R | 0.013R | 1.02 |
| B_plus_diag | context | fixed_2R | 404 | 40.35% | 16.01R | 0.040R | 1.07 |

エントリーは `B_plus_diag` が最も筋が良い。
単独B抜けより、「B抜け時点で斜めも抜けている」条件が数字に残っている。

## 次のPineへの落とし込み

次の表示専用Pineでは、最初からエントリーを出さない。
以下を候補表示にする。

優先候補:

- `ihs_5pivot`
- `classic_6pivot`
- `role_ab_5pivot` は薄色の参考候補

初期表示条件:

- 中波2波戻し: 0.50から0.886
- 斜めライン: 現在足で抜けている
- B: ブレイク済み、またはブレイク直前
- 上位足: 1つ以上順行、明確な逆行は低品質表示
- 実体: body ratio 0.35以上を高品質表示
- Bからの距離: 1.8ATR以内
- 調整横軸: 1波時間の0.5倍以上を高品質表示

表示すべきライン:

- 中波 `P0/P1/P2`
- 小波ヘッド/右肩
- A
- B
- 斜めライン
- 半値TP
- 1.5R/2R参考TP

現時点では、`strict_synapse` をそのままPineの初期条件にしない。
絞りすぎて人間の確認候補まで消える可能性が高い。
