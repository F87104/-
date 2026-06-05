# 系統B — 本番運用ファイル

作成日: 2026-06-01

系統A（TrendBreak V1 + H4 T5）とは **別帳簿**。V1/T5 は系統Bのレーンに含めない。

## ファイル

| ファイル | 用途 |
|----------|------|
| [portfolio_slots.yaml](portfolio_slots.yaml) | レーン定義・有効/無効・リスクR・Pineパス・重複優先順 |
| [system_b_forward_trade_log.csv](system_b_forward_trade_log.csv) | フォワード／実弾の1行1トレード台帳（テンプレ付き） |
| [lane_exclusions.md](lane_exclusions.md) | B03除外・B04観測のみの運用固定 |

## 使い方

1. 新規シグナル前に `portfolio_slots.yaml` で `enabled` と `risk_r_default` を確認
2. 執行したら `system_b_forward_trade_log.csv` に1行追加（`record_id` は `FW-B06-20260601-001` 形式を推奨）
3. B06: **4通貨37件** TV OANDA 照合OK（2026-06-05）→ `0.25R` フォワード可。期待値は `python_expected_b06_tv_oanda_*.csv`
4. B03/B04 はログに載せない（除外テンプレ行は参照のみ）

## Pine 照合（B06/B07）

```bash
python3 scripts/export_system_b_pine_parity.py
python3 scripts/run_system_b_pine_parity_audit.py
```

出力: [docs/research/system_b_pine_parity_2026-06-01/](../../research/system_b_pine_parity_2026-06-01/)

**TVスモーク（執行の正）:** `*_b06_tv_oanda_smoke.md`（銘柄別）— TV OANDA/統一データ上の Python。旧 F87104 34件リストは使わない。

## 検証の再実行

```bash
python3 scripts/validate_system_b_lanes.py
```
