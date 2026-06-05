# 価格固定ラベル — Pine 再現レシピ

踏み上げ投げ切りで **インジとチャートがぴったり合った** 表示方法の記録。

## ファイル

| ファイル | 用途 |
|----------|------|
| `pine/lib/price_anchored_labels_v1.pine` | 共通ライブラリ（TV に1回保存） |
| `pine/visual/market_psychology_cap_sqz_visual.pine` | **メイン表示**（観測専用・▲印のみ。ラベルずれ対策は不要） |
| `pine/production/h4_sqz_tv_validation.pine` | **メイン戦略**（インジ②と完全一致） |
| `pine/templates/TEMPLATE_price_anchored_indicator.pine` | 新規インジ用ひな型 |

## 原因の切り分け（覚えておく）

| パターン | 結果 |
|----------|------|
| `label.new(bar_index + 8, 0, yloc=belowbar)` | **NG** — 8本後の別ローソクの下に付く |
| `label.new(bar_index + 8, h4Close, yloc=price)` + security 価格 | **NG** — Y がチャートとズレることがある |
| `label.new(bar_index + 6, close, yloc=price)` + 水平点線 | **OK** — シグナル足の価格を固定、横だけ逃がす |
| `plotshape(..., location=belowbar)` on **同じ bar_index** | **OK** — ▲用 |

**主因は `bar_index` と `yloc.belowbar` の併用。** security は H4 直表示では副次。

## 再現チェックリスト（新インジを書くとき）

1. **チャート TF = 判定 TF**（例: H4 なら `f()` をチャート足で直計算、`security` は使わない）
2. **▲** は `plotshape` + `location.belowbar` + **シグナル足の bar_index**
3. **SIG ラベル**
   - `anchorPrice = close`（シグナル足）
   - `labelX = bar_index + N`
   - `yloc = yloc.price`
   - 点線: `(bar_index, close) → (labelX, close)`
4. **約定ラベル**（翌足エントリーなら）
   - `anchorPrice = open`（約定足）
   - `labelX = bar_index + N + stagger`
   - 同様に `yloc.price` + 水平点線
5. **TP/SL ライン** — `line.new(約定bar, price, 約定bar+extend, price)`（全画面 plot だけにしない）
6. **ストラテジー** — `comment=""`、表示はインジのみ（二重ラベル防止）

## TradingView でライブラリを使う

1. `pine/lib/price_anchored_labels_v1.pine` をコピー
2. TV → Pine エディタ → **ライブラリ** として新規保存 → 名前 `PriceAnchoredLabels_v1`
3. インジ先頭に追加:

```pine
import YOUR_USERNAME/PriceAnchoredLabels_v1/1 as pal
```

4. ラベル描画例:

```pine
[lb, ln] = pal.drawAnchoredLabel(
     bar_index, close, ta.atr(14), 0.35, 6,
     "SIG\nS " + pal.fmtPrice(close),
     color.new(color.lime, 12), color.new(color.lime, 50),
     true, "up")
```

## 踏み上げの約定ルール（ロジック側）

- シグナル: 棚ブレイク確定足
- 約定: **翌足始値**
- SL: 棚安 − 0.25×ATR
- TP: 2R
- 重複: Python 同等（保有中は次 SIG スキップ）

## やってはいけないこと

- `yloc.belowbar` で `bar_index + N`（N>0）のラベル
- ラベル Y に `request.security` の close（チャートと同じ TF なら `close` を使う）
- インジ + ストラテジー両方で同じラベル
- ストラテジー `comment="踏み上げ"`（TV が別位置に約定ラベル表示）
