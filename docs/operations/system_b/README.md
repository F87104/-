# 系統B — 本番運用ファイル

作成日: 2026-06-01

系統A（TrendBreak V1 + H4 T5）とは **別帳簿**。V1/T5 は系統Bのレーンに含めない。

## ファイル

| ファイル | 用途 |
|----------|------|
| [chart_bundle.yaml](chart_bundle.yaml) | **B06 を H4 4本目として載せる手順** |
| [portfolio_slots.yaml](portfolio_slots.yaml) | レーン定義・有効/無効・リスクR・Pineパス・重複優先順 |
| [system_b_forward_trade_log.csv](system_b_forward_trade_log.csv) | フォワード／実弾の1行1トレード台帳（テンプレ付き） |
| [lane_exclusions.md](lane_exclusions.md) | B03除外・B04観測・**B07退役**の運用固定 |

## H4 チャート（JPY4本番 + 試験3銘柄・4本目）

系統A H4 のあとに B06 を Add to chart:

1. [h4_v_initial_shelf_breakout_strategy.pine](../../pine/research/h4_v_initial_shelf_breakout_strategy.pine)
2. 設定: JPY4は `4通貨のみ` / 試験3銘柄は `試験3銘柄` / PRECALM ON / `Signal基準` TP / 年末年始停止 ON

| 通貨 | H4 本数 | 内訳 | B06 |
|------|---------|------|-----|
| USDJPY | 4 | T5 + インジ + 踏み上げ + **B06** | 本番 0.25R |
| EURJPY | 3 | T5 + インジ + **B06** | 本番 0.25R |
| GBPJPY | 3 | T5 + インジ + **B06** | 本番 0.25R（Pine5件執行正） |
| AUDJPY | 1〜4 | B06 必須（系統A外のため B06 単独タブでも可） | 本番 0.25R |
| XAUUSD | 4 | T5 + インジ + 踏み上げ + **B06試験** | **TRIAL** 0.25R |
| CHFJPY | 3 | T5 + インジ + **B06試験** | **TRIAL** 0.25R（FOREXCOM CSV・9件） |
| SILVER | 4 | T5 + インジ + 踏み上げ + **B06試験** | **TRIAL** 0.25R |

## 使い方

1. 新規シグナル前に `portfolio_slots.yaml` で `enabled` と `risk_r_default` を確認
2. 執行したら `system_b_forward_trade_log.csv` に1行追加（`record_id` は `FW-B06-20260601-001` 形式を推奨）
3. B06: **4通貨37件** TV OANDA 照合OK（2026-06-05）→ `0.25R` フォワード可。期待値は `python_expected_b06_tv_oanda_*.csv`
4. B03/B04/B07 はログに載せない（除外・退役テンプレ行は参照のみ）
5. **JPY4 棚抜けは B06 のみ**（B07 ﾄﾗ棚は退役）

## Pine 照合（B06）

```bash
python3 scripts/run_b06_tv_oanda_parity.py          # JPY4 + 試験（CSVある銘柄）
python3 scripts/run_b06_tv_oanda_parity.py --trial-only
python3 scripts/export_system_b_pine_parity.py
python3 scripts/run_system_b_pine_parity_audit.py
```

出力: [docs/research/system_b_pine_parity_2026-06-01/](../../research/system_b_pine_parity_2026-06-01/)

**TVスモーク（執行の正）:** JPY4は `*_b06_tv_oanda_smoke.md` / 試験は `python_expected_b06_tv_oanda_trial_all.csv` をチャート照合。

## 検証の再実行

```bash
python3 scripts/validate_system_b_lanes.py
```
