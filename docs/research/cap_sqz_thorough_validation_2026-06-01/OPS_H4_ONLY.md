# 踏み上げ（SQZ）運用ルール — H4専用

**確定日: 2026-06-01**

## 時間足

| 構造 | 時間足 | エントリー |
|------|--------|------------|
| **踏み上げ SQZ** | **H4のみ** | 可（STRICT・2R） |
| 投げ切り CAP | 任意（監視用） | **不可** |

- H1で踏み上げマークが出ても **エントリーしない**（研究: 同設定でPF≈0.9）
- チャートは **H4に切り替えて** シグナル確定を待つ
- H1は **投げ切りの早期気づき** 程度に使う（任意）

## 本番ファイル

- **表示（メイン）:** `pine/visual/market_psychology_cap_sqz_visual.pine`（踏み上げ投げ切り）
- **戦略（メイン）:** `pine/production/h4_sqz_tv_validation.pine`（インジと完全一致・翌足始値）
- アラート補助: `pine/production/h4_sqz_strict_live_ready.pine`

## 通貨

- 許可: XAUUSD, USDJPY, CHFJPY, SILVER
- 禁止: GBPJPY, AUDJPY
- EURJPY: デフォルトOFF

## 検証根拠（H4 STRICT・コア4・研究期）

- 29件 / 勝率65% / PF3.62 / +27R / maxDD2.1R
- 年約3件

## TB / T5

- 同銘柄・重複時: **T5優先** → 空きスロットでSQZ
