# SQZ STRICT 実装仕様（確定案）

## 時間足（必須）

- **踏み上げ SQZ: H4 のみ。** H1/M15等ではシグナルを出さず、エントリーしない。
- 根拠: `docs/research/cap_sqz_h1_vs_h4_2026-06-01/` — 同パラメータをH1に貼るとPF<1。

## エントリー（H4・ロング）

1. `shelfBars=6` 直前の高値 `shelfHi`、安値 `shelfLo`
2. `shelfRange <= 2.0 * ATR`
3. 棚前 `dropWin=6` の高値から棚高値まで `>= 3.5 * ATR` 下落
4. 前足終値 `<= shelfHi` かつ 当足終値 `> shelfHi`
5. シグナル足確定 → **次足始値**でエントリー

## 出口

- SL: `shelfLo - 0.25 * ATR`
- TP: `2.0R`（フォワードで2.5R比較可）
- 最大保有: 120 H4

## 通貨

- 許可: XAUUSD, USDJPY, EURJPY, CHFJPY, SILVER
- 禁止: GBPJPY, AUDJPY

## 投げ切り

- 表示・アラートのみ。自動発注なし。
- Pineデフォルト条件はユーザー提示インジと同一。

## TradingView 検証用 Pine

- **表示（メイン）:** `pine/visual/market_psychology_cap_sqz_visual.pine` — 投げ切り① + 踏み上げ②（棚 **2.5ATR** / 急落 **3.0ATR**）
- **戦略（メイン）:** `pine/production/h4_sqz_tv_validation.pine` — インジ②と完全一致（翌足始値・overlapMode・maxHold）
- **研究コピー:** `pine/research/h4_sqz_strict_tv_validation.pine` — 本番と同一
- **アラート補助:** `pine/production/h4_sqz_strict_live_ready.pine` — 軽量シグナルのみ
- Python 厳密照合は `SQZ_STRICT_RR2`（2.0/3.5）のため、TV ではトレード数が増える点に注意
