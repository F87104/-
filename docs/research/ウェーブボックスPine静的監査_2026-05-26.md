# WaveBox Pine Static Audit 2026-05-26

対象:

- `pine/archive/wavebox_usdjpy_h1_rebreak_v1.pine`

## 結論

リアルタイム運用を壊す重大な実装ミスは、コード上は見つからない。

ただしTradingViewのコンパイル確認と、実チャート上の目視確認は別途必要。

## 確認したこと

### 未来参照

H4参照はすべて `barmerge.lookahead_off`。

- `h4Close`
- `h4Ema`
- `h4Slope`

`lookahead_on` は使っていない。

### SIGNAL確定

SIGNALの起点は以下。

```pine
canArmSignal = barstate.isconfirmed and rawCoreSignal ...
```

つまり未確定のH1足ではシグナルを確定させない。

### ENTRYタイミング

SIGNAL時点では `simPending := true` にするだけ。

実際の内部ENTRYは以下。

```pine
if simPending and bar_index > pendingSignalBar
    entry = open
```

したがってENTRYはSIGNAL足ではなく、次のH1足の始値。

### 重複シグナル

同じ波形セットアップの重複は `setupKey != lastSetupKey` で抑制している。

### Strategy注文

`enableOrders` はデフォルトOFF。

ONにした場合、TradingViewのストラテジー注文は参考値。実力評価は内部R集計を優先する。

注意点:

- strategy注文の数量計算はSIGNAL足close基準のリスク距離を使う。
- 内部Rシミュレーションは次足open基準。
- そのため実運用判断は、内部R表示と手動記録を優先する。

## 監査結果

| 項目 | 判定 | コメント |
| --- | --- | --- |
| 未確定足シグナル | OK | `barstate.isconfirmed`で防止 |
| SIGNAL足での内部ENTRY | OK | `bar_index > pendingSignalBar`で次足open |
| H4未来参照 | OK | `lookahead_off` |
| 同一セットアップ重複 | OK | `setupKey`で抑制 |
| strategy損益の過大表示 | 注意 | デフォルトOFF。使うなら参考表示のみ |
| TradingViewコンパイル | 未確認 | TradingView上での最終確認が必要 |

## 次の実地確認

TradingViewで以下を確認する。

1. `WaveBox SIGNAL GO` アラートを設定する。
2. SIGNALが出たH1足の次の足に `EN` が出るか確認する。
3. A+/A/SELECT/OBS/SKIPがテーブルとラベルで一致するか確認する。
4. 1件ずつ `wavebox_forward_validation_tracker.xlsx` またはCSVへ記録する。
5. Pythonの該当トレードと時刻、方向、Entry、Stop、Targetを突き合わせる。
