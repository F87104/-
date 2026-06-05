# 踏み上げ・投げ切り — 実装判定（徹底検証後）

**判定: 条件付き GO** — **SQZ STRICT のみ本番実装**。CAP は監視のみ。

**時間足: 踏み上げは H4 のみ（確定）。H1でのSQZエントリーは行わない。**

運用メモ: [`OPS_H4_ONLY.md`](OPS_H4_ONLY.md)

---

## 実装するもの

| ファイル | 役割 |
|----------|------|
| `pine/visual/market_psychology_cap_sqz_visual.pine` | **メイン表示**（観測専用・投げ切り① + 踏み上げ②・▲印のみ） |
| `pine/production/h4_sqz_tv_validation.pine` | **メイン戦略**（インジと完全一致・TV検証・約定） |
| `pine/production/h4_sqz_strict_live_ready.pine` | 補助（アラートのみ・軽量） |

---

## 本番仕様（確定）

- **時間足:** H4
- **方向:** ロングのみ
- **条件:** 棚6本・急落窓6本・棚幅≤**2.0**ATR・急落≥**3.5**ATR・終値で棚上抜け
- **通貨（推奨）:** XAUUSD, USDJPY, CHFJPY, SILVER — **EURJPYはデフォルトOFF**（研究PF 0.39）
- **除外:** GBPJPY, AUDJPY（常時禁止）
- **SL:** 棚安 − 0.25 ATR
- **TP:** **2.0R**（手動2.5Rはフォワードで比較）
- **エントリー:** シグナル足確定 → 次足始値（Python検証と同じ）

---

## コア数値（研究期 2015–2024）

### SQZ STRICT 2R・本番5通貨

| 指標 | 値 |
|------|-----|
| 件数 | 35 |
| 勝率 | 57.1% |
| PF | **2.55** |
| 合計R | +23.8R |
| maxDD | 3.1R |
| 最大連敗 | 3 |

### SQZ STRICT 2R・コア4通貨（EURJPY除外）

| 指標 | 値 |
|------|-----|
| 件数 | 29 |
| 勝率 | 65.5% |
| PF | **3.62** |
| 合計R | +26.9R |
| maxDD | 2.1R |

### 投げ切り CAP（単独エントリー）

| 指標 | 値 |
|------|-----|
| 研究期・5通貨 | 148シグナル（監視のみ） |
| 24H4以内にSQZ STRICT | **2.7%** |
| 単独2R PF | **≈1.04** → **実装しない** |

---

## OOS（参考・件数少）

| variant | OOS件数 | PF | 合計R |
|---------|--------|-----|-------|
| SQZ STRICT 2R・5通貨 | 3 | 0.99 | −0.03R |
| SQZ STRICT 2R・7通貨 | 3 | 0.99 | −0.03R |
| SQZ PINE 2R・5通貨 | 8 | 1.19 | +0.9R |

→ **OOSは統計不足**。フォワード20件まで「準本番」。

---

## TB / T5 との関係

- SQZ と TBロング / T5 の **同時保有重複 ≈ 0%**
- 合算（研究期・5通貨）:
  - TBロングのみ: +62.7R / PF1.56
  - T5のみ: +19.4R / PF4.04
  - **TB+T5+SQZ（T5優先）: +101.6R / PF1.79**（SQZ+35件相当）

---

## GO前の必須タスク

- [ ] TradingView: Python `trades_SQZ_STRICT_2R.csv` と **5件パリティ**
- [ ] フォワード **20件** 記録（コア4通貨）
- [ ] 運用ルール1行: TB+T5重複時は T5優先、空きスロットで SQZ

---

## 再実行

```bash
python3 scripts/validate_cap_sqz_thorough.py
```

全CSV: `docs/research/cap_sqz_thorough_validation_2026-06-01/`
