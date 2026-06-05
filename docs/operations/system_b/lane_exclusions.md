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

## B07 DTS ﾄﾗ棚 — 研究・本番から退役（RETIRED）

| 項目 | 値 |
|------|-----|
| レーンID | `B07_DTS_TRAP_SHELF` |
| 退役日 | 2026-06-01 |
| 理由 | B06（棚抜）と **H4シグナル時刻が9〜12件すべて重複**。B06優先運用では B07 は執行上の追加価値なし |
| 参照データ | [DECISION_b07_tv_oanda_parity.md](../../research/system_b_pine_parity_2026-06-01/DECISION_b07_tv_oanda_parity.md)（照合記録は残置） |

### 運用上の扱い

1. `portfolio_slots.yaml` で `enabled: false`、`status: RETIRED`
2. `overlap_resolution.priority` から B07 を削除
3. JPY4 H4 の棚抜けは **B06（棚抜）のみ** — [h4_v_initial_shelf_breakout_strategy.pine](../../../pine/research/h4_v_initial_shelf_breakout_strategy.pine)
4. `d1_trap_h4_shelf_strict_strategy.pine` はチャートに載せない（研究用にリポジトリ内に残すのみ）
5. `system_b_forward_trade_log.csv` に B07 は記録しない

除外理由コード: `SYSB_RETIRED_B06_SUPERSET`

```
2026-06-01 判定: B07⊆B06(H4) → 系統B本番は B06 のみ継続
```

---

## 有効レーンとの重複（現行）

- 本番優先: **SQZ > B06棚抜**（B07は退役のため対象外）
- B06 は SQZ・系統A T5 との重複は別ルール（[portfolio_slots.yaml](portfolio_slots.yaml)）

---

## 変更履歴

| 日付 | 変更 |
|------|------|
| 2026-06-01 | B07 退役（B06のみ継続） |
| 2026-06-01 | B03 除外、B04 観測のみを文書化 |
