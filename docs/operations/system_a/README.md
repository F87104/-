# 系統A — V1 + H4 T5 本番運用

作成日: 2026-06-01

TrendBreak V1（H1）+ H4 T5 + **踏み上げ投げ切り（表示）** + **踏み上げ TV検証（strategy）** を同一 H4 チャートに載せる本番定義。

## ファイル

| ファイル | 用途 |
|----------|------|
| [portfolio_slots.yaml](portfolio_slots.yaml) | 6通貨・H1/H4・Pine3本の載せ方・重複ルール |
| [chart_bundle.yaml](chart_bundle.yaml) | H4 3本スタック・通貨別 ON/OFF |

## H4チャートに載せる順（6通貨）

| 順 | Pine | 種類 |
|:---:|------|------|
| 1 | [h4_t5_macd_bb_live_ready.pine](../../pine/production/h4_t5_macd_bb_live_ready.pine) | strategy（本番） |
| 2 | [market_psychology_cap_sqz_visual.pine](../../pine/visual/market_psychology_cap_sqz_visual.pine) | indicator（観測） |
| 3 | [h4_sqz_tv_validation.pine](../../pine/production/h4_sqz_tv_validation.pine) | strategy（踏み上げ・対象通貨のみ） |

**踏み上げ strategy の対象:** XAUUSD・USDJPY・CHFJPY・SILVER  
**除外:** EURJPY（研究マイナス）・GBPJPY・AUDJPY

## 重複ルール

1. **TB vs T5（同一通貨）:** T5 優先 → [A-path DECISION](../../research/original_a_path_DECISION_2026-06-01.md)
2. **T5 vs 踏み上げ:** 同時保有ほぼなし。重なれば **T5 優先**
3. **投げ切り:** ラベルのみ。エントリーしない

## 踏み上げ strategy の表示設定

インジと二重にならないよう:

- `▲をここでも描画` → **OFF**
- `SIG/約定ラベル` → **OFF**（インジで十分な場合）

## 参照

- [STRATEGY_GUIDE.md](../../STRATEGY_GUIDE.md) — TVデプロイ手順
- [h4_t5_macd_bb_live_ready_notes.md](../../h4_t5_macd_bb_live_ready_notes.md)
- [cap_sqz DECISION](../../research/cap_sqz_thorough_validation_2026-06-01/DECISION.md)
