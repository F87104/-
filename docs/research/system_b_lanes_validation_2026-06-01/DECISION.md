# 系統B 10レーン — 本格実装判定

作成日: 2026-06-01

## 結論

- **系統A（TrendBreak V1 + H4 T5）は変更しない。** 系統Bは別ポートフォリオとして追加する。
- **即実装（フルサイズ候補）:** B01 XAU SQZ、B05 SILVER SQZ — Research PF≥4、DD≤2.1R、Pine ready。
- **0.25Rフォワード（Pine ready・要OOS監視）:** B02 USDJPY SQZ — Research良好だがOOS 2敗。
- **0.25Rのみ / レーン縮小:** B03 EURJPY SQZ — Research **マイナス**（-3.09R）。本番から外すかシンボル停止を推奨。
- **観測継続:** B04 CHFJPY SQZ — 10年1件。統計として未成立。
- **Pine照合後フォワード:** B06 VIS PRECALM、B07 DTS — 品質は良いが样本・B06↔B07重複9件あり。
- **保留:** B08 LSS、B09 IGNITION — Pine未整備。Researchは良好だが年1件未満。

## ポートフォリオ（重複排除・SQZ優先）

- 採用 **88** 件 / 年 **7.87**（目標20–30/年に対しやや多め）
- 総R **53.79** / PF **2.46** / maxDD **6.15R**

## 本番ゲート（固定・再最適化禁止）

1. レーンあたり Research trades≥5、PF≥1.5、maxDD≤6R
2. 年あたり≤3件/レーン（B06は4銘柄合算のため別枠で監視）
3. Pine `yes` のみフルサイズ候補。`partial` は0.25Rまで。
4. 同一 H4 バー・同一銘柄は SQZ > VIS > DTS > LSS > IGNITION で1件のみ

## 次アクション

1. ~~`portfolio_slots.yaml` + トレードログCSVテンプレート~~ → [docs/operations/system_b/](../../operations/system_b/)
2. ~~B06/B07 Pine parity 期待値エクスポート~~ → [system_b_pine_parity_2026-06-01/](../system_b_pine_parity_2026-06-01/)（TV照合は手動）
3. ~~B03 除外の運用ドキュメント化~~ → [lane_exclusions.md](../../operations/system_b/lane_exclusions.md)
4. B08/B09 Pine実装または系統Bから外す

再現: `python3 scripts/validate_system_b_lanes.py`  
Pine export: `python3 scripts/export_system_b_pine_parity.py`