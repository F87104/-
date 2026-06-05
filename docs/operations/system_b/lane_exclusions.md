# 系統B — レーン除外・観測のみ（運用固定）

作成日: 2026-06-01

**方針:** パラメータ再最適化はしない。検証結果に基づき、本番スロット（`portfolio_slots.yaml` の `enabled: true`）だけを更新する。

根拠データ: [system_b_lanes_validation_2026-06-01/DECISION.md](../../research/system_b_lanes_validation_2026-06-01/DECISION.md)

---

## B03 EURJPY SQZ — 本番除外（EXCLUDED）

| 項目 | 値 |
|------|-----|
| レーンID | `B03_SQZ_EURJPY` |
| ルール | SQZ_STRICT（他SQZレーンと同一Pine・同一 spec） |
| Research 2015–2024 | 6件 / **-3.09R** / **PF 0.39** / maxDD 3.05R |
| OOS 2025–2026 | 0件 |
| 判定 | 系統Bの昇格ゲート（PF≥1.5）**不合格** |

### 運用上の扱い

1. `portfolio_slots.yaml` で `enabled: false`、`status: EXCLUDED`
2. `system_b_forward_trade_log.csv` には記録しない（テンプレ行 `FW-EXCLUDED-B03` は参照用のみ）
3. TradingView で EURJPY に SQZ シグナルが出ても **系統B枠では執行しない**
4. 系統A（TB/T5）とは無関係。TB/T5の運用は変更しない
5. 再開条件（将来）: フォワードで別検証を完了し、研究インデックスで明示承認があるまで **自動再開しない**

### 記録用（監査）

除外理由コード: `SYSB_EXCL_RESEARCH_PF`

```
2026-06-01 検証: Research PF 0.39, total_r -3.09 → 系統B本番スロットから除外
```

---

## B04 CHFJPY SQZ — 観測のみ（OBSERVE_ONLY）

| 項目 | 値 |
|------|-----|
| レーンID | `B04_SQZ_CHFJPY` |
| Research 2015–2024 | **1件** / +1.97R / PF inf |
| 判定 | 样本不足。年1件未満でレーン設計意図（2–3件/年）未達 |

### 運用上の扱い

1. `enabled: false`、`status: OBSERVE_ONLY`
2. チャート上でシグナルを **メモ・parity練習** に使うのは可。実弾・フォワードログには載せない
3. 10件以上のフォワードが溜まった時点で、研究側が再検証を依頼するまで昇格しない

除外理由コード: `SYSB_OBS_LOW_SAMPLE`

---

## 有効レーンとの重複

- B06 VIS と B07 DTS は同一 H4・銘柄で **9ペア** 重複（検証CSV `overlap_matrix.csv`）
- 本番では `overlap_resolution.priority` により **SQZ > VIS > DTS**。B06とB07が競合したら **B06を優先**（B07は `overlap_suppressed=yes` でログ）

---

## 変更履歴

| 日付 | 変更 |
|------|------|
| 2026-06-01 | B03 除外、B04 観測のみを文書化 |
