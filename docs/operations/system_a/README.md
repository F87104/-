# 系統A — V1 + H4 T5 + 踏み上げ投げ切り

更新: 2026-05-31

TrendBreak V1（H1）+ H4（T5 + 踏み上げ投げ切り + 踏み上げ + **B06棚抜**）

## H4 Pine（載せ順）

| 順 | ファイル | 種類 | 対象 |
|:---:|----------|------|------|
| 1 | [h4_t5_macd_bb_live_ready.pine](../../pine/production/h4_t5_macd_bb_live_ready.pine) | strategy | 6通貨 |
| 2 | [market_psychology_cap_sqz_visual.pine](../../pine/visual/market_psychology_cap_sqz_visual.pine) | indicator | 6通貨 |
| 3 | [h4_sqz_tv_validation.pine](../../pine/production/h4_sqz_tv_validation.pine) | strategy | XAU/USDJPY/銀 |
| 4 | [h4_v_initial_shelf_breakout_strategy.pine](../../pine/research/h4_v_initial_shelf_breakout_strategy.pine) | **strategy（B06棚抜）** | **JPY4** |

## 役割

- **インジ:** 投げ切り①（水色）+ 踏み上げ②（緑）— 発注なし
- **strategy:** インジ②踏み上げと同一条件（2.5/3.0 ATR・翌足始値・RR2）

## 踏み上げ strategy の対象

| 通貨 | 載せる |
|------|--------|
| XAUUSD, USDJPY, SILVER | ✅ |
| EURJPY, GBPJPY | ❌ |
| CHFJPY | インジのみ |

## JPY4 の4本目（B06）

USDJPY / EURJPY / GBPJPY / AUDJPY の H4 に **4本目** で B06 を追加。  
詳細: [系統B chart_bundle](../system_b/chart_bundle.yaml)

- リスク **0.25R**
- GBPJPY は **Pine 5件** が執行正
- T5・踏み上げと重なったら **T5優先**

## 重複ルール

1. TB vs T5 → **T5優先**
2. T5 vs 踏み上げ / B06 → **T5優先**
3. 投げ切り → **エントリーしない**

## strategy 表示設定

- `▲をここでも描画` → **OFF**（インジと二重防止）

## 参照

- [chart_bundle.yaml](chart_bundle.yaml)
- [STRATEGY_GUIDE.md](../../STRATEGY_GUIDE.md)
