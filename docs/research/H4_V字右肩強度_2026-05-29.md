# H4 V右肩優位・左肩起点超え 検証メモ

作成日: 2026-05-29

## 仮説

V字回復の中でも、以下の形は強い可能性がある。

- Vの左肩: confirmed pivot high から confirmed pivot low への急落
- Vの右肩: pivot low からの回復
- 右肩の角度が左肩より急
- 右肩の終値が、左肩の起点である急落前pivot highを超える

これは単なる61.8%回復ではなく、急落を否定して、急落前の売り手の起点まで取り返した形と考える。

## 検証定義

- 時間足: H4 / D1
- 方向: ロングのみ
- Entry: 条件成立足の次足始値
- SL: V安値 - 0.25ATR
- TP: 固定RR
- コスト: 既存検証と同じスプレッド・スリッページ
- Research: 2015-2024
- OOS: 2025-2026

主な条件:

- 下落幅 >= 3.2ATR
- 下落速度 >= 0.25ATR/本
- 下落本数 2-30本
- 回復本数 30本以内
- 終値が左肩起点を0.05ATR上抜け
- 右肩速度 >= 左肩速度、または1.2倍/1.5倍
- 実戦寄りフィルタでは、実体45%以上、終値位置60%以上

## 主な結果

H4では、仮説は有効寄り。

| rule | trades | winrate | total_r | avg_r | pf | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| RS100_BODY45_CLOSE60_RR1.5 | 189 | 48.15% | +28.25R | +0.15R | 1.30 | 13.94R |
| RS120_BODY45_CLOSE60_RR1.5 | 130 | 50.00% | +26.49R | +0.20R | 1.43 | 9.63R |
| RS120_BODY45_CLOSE60_RR2.0 | 128 | 44.53% | +24.83R | +0.19R | 1.37 | 11.94R |
| RS120_UPREG_BODY45_CLOSE60_RR1.5 | 54 | 51.85% | +13.34R | +0.25R | 1.53 | 5.07R |

速度を1.0倍から1.2倍へ強めると、取引数は減るがPFと平均Rが改善した。

## 実戦候補

現時点の本線候補は以下。

**H4 RS120 BODY45 CLOSE60 RR1.5 / XAUUSD除外**

| trades | winrate | total_r | avg_r | pf | max_dd |
|---:|---:|---:|---:|---:|---:|
| 103 | 51.46% | +26.75R | +0.26R | 1.57 | 9.09R |

期間別:

| period | trades | winrate | total_r | avg_r | pf | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| Research_2015_2024 | 88 | 50.00% | +19.70R | +0.22R | 1.48 | 9.09R |
| OOS_2025_2026 | 15 | 60.00% | +7.06R | +0.47R | 2.30 | 2.01R |

## 通貨別の気づき

RS120_BODY45_CLOSE60_RR1.5:

- CHFJPYが最も良い: 16 trades / +8.00R / PF 2.32
- USDJPY, GBPJPY, EURJPY, AUDJPY, SILVERもプラス
- XAUUSDは 27 trades / -0.26R / PF 0.98 で除外候補

上向きEMA環境を入れると全体DDは下がるが、GBPJPY/EURJPY/SILVERが弱くなり、通貨選別が必要になる。

## 暫定結論

この形は「V字そのものを買う」条件として、以前の完全回復Vよりかなり良い。

ただしPF 1.4-1.6帯なので、単独主力ではなく、以下のどちらかが実戦向き。

1. H4 V右肩優位を補助手法として採用する
2. H4 V右肩優位をT5や棚ブレイクの上位フィルタにする

最初にPine化するなら、最も素直なのは **RS120_BODY45_CLOSE60_RR1.5 / XAUUSD除外**。

## 次の改善候補

- TPを固定1.5Rだけでなく、急落前高値ブレイク後の次の高値更新まで伸ばす管理を比較する
- XAUUSDだけ別条件にするか除外する
- H4 V右肩優位がTrendBreakV1と重なる時、どちらを優先するか確認する
- Pine化では、pivot確定後にシグナル位置がずれないよう、xloc.bar_timeで固定する

## 出力

- `backtests/elliott_fibo/run_v_right_shoulder_strength_study.py`
- `backtests/elliott_fibo/results_2026_05_29/v_right_shoulder_strength/report_ja.md`
- `backtests/elliott_fibo/results_2026_05_29/v_right_shoulder_strength/trades.csv`
- `backtests/elliott_fibo/results_2026_05_29/v_right_shoulder_strength/summary_practical_ex_xau.csv`
- `backtests/elliott_fibo/results_2026_05_29/v_right_shoulder_strength/summary_practical_ex_xau_by_period.csv`
- `pine/research/h4_v_right_shoulder_strength_strategy.pine`

## Pine化メモ

Pine版は `RS120_BODY45_CLOSE60_RR1.5 / XAUUSD除外` を初期値にした。

Parity上の注意:

- Pythonは銘柄別スプレッド・スリッページをRで集計する。
- Pine Strategy Testerは価格損益ベースなので、勝率・PFは完全一致しない。
- ただし、シグナル条件はPythonと同じになるようにした。
- confirmed pivot配列を保持し、直近12個のH→Lペアを走査する。
- 同じVペアは `startBar-lowBar` キーで一度しか使わない。
- ポジション保有中、未約定pending中、決済バーでは新規シグナルを抑制する。
- ラベルとラインは `xloc.bar_time` 固定。チャートを動かしてもシグナル位置がずれにくい。
