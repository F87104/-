# H4 Right-Shoulder V Reclaim 実戦メモ 2026-06-02

## 狙う形

画面で赤線を引いたような、左肩の急落より右肩の回復が急なVを探す。

T5のようにBB/MACD/stagnationを全部満たすかを見るのではなく、Vそのものの質を見る。

## 手法名

H4 Right-Shoulder V Reclaim

Python研究名では `RS120_BODY45_CLOSE60_RR15`。

## 条件

- 時間足: H4
- 方向: ロングのみ
- confirmed pivot high から confirmed pivot low への急落を左肩とする
- 下落幅 >= 3.2 ATR
- 左肩速度 >= 0.25 ATR/本
- 左肩本数: 2〜30本
- 右肩本数: 30本以内
- 右肩速度 >= 左肩速度 x 1.20
- 終値が左肩起点を 0.05 ATR 上抜け
- シグナル足の実体比率 >= 45%
- シグナル足の終値位置 >= 60%
- SL = V安値 - 0.25 ATR
- TP = 1.5R
- XAUUSDは現状除外候補
- 12/15〜1/10は新規停止

## 既存検証結果

対象: H4、XAUUSD除外、2015〜2026。

| rule | trades | winrate | total_r | avg_r | PF | max_dd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RS120_BODY45_CLOSE60_RR15 | 103 | 51.46% | +26.75R | +0.26R | 1.57 | 9.09R |

期間別:

| period | trades | winrate | total_r | PF | max_dd |
| --- | ---: | ---: | ---: | ---: | ---: |
| Research_2015_2024 | 88 | 50.00% | +19.70R | 1.48 | 9.09R |
| OOS_2025_2026 | 15 | 60.00% | +7.06R | 2.30 | 2.01R |

## 使い方

T5とは別物として扱う。

- T5: V後の停滞/再ブレイク/BB/MACDで早めに拾う
- Right-Shoulder V: 左肩起点を強く取り返したVだけ拾う

実戦では、右肩加速Vが出たあとにすぐ飛び乗るより、同じ方向にTrendBreakV1や再ブレイクが重なるかを見ると、主力手法との接続がしやすい。

## Pine

実戦確認用:

- `pine/production/h4_v_right_shoulder_acceleration_reclaim.pine`

このPineは、Vラインを時間固定で描画するため、チャートを横に動かしても線がずれにくい。

