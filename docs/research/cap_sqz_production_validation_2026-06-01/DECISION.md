# 投げ切り・踏み上げ — 本番導入判定（2026-06-01）

## 検証対象

ユーザー提示 Pine「踏み上げ投げ切り」（観測用インジ）と同義の Python 実装:

- `backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py`
- 追加: `scripts/validate_cap_sqz_production.py`

**出口（TB/T5と同系）**

| 項目 | 値 |
|------|-----|
| 利確 | 固定 **2R** または **2.5R** |
| 損切 | 棚安値 / 投げ切り足安値 − **0.25 ATR** |
| エントリー | シグナル足の **次H4始値** |
| 最大保有 | **120 H4本** |
| R | スプレッド・スリッページ込み `r_after_cost` |

---

## 結論（1ページ）

| 構造 | Pineデフォルト単独 | 本番採用 |
|------|-------------------|----------|
| **② 踏み上げ SQZ** | **採用候補** | **準本番#1**（GBPJPY除外、できれば STRICT） |
| **① 投げ切り CAP** | 単独はエッジ薄 | **監視のみ**（単独エントリーは非推奨） |
| **両方まとめて毎回入る** | 件数増・PF中程度 | **非推奨**（SQZが良いトレードを薄める） |

**手動成績が良かった場合**、銘柄が XAG/SILVER 中心なら研究データと整合（XAU strict SQZ が強い）。CAP 単独で勝っているなら、銘柄バイアスかサンプル数少の可能性が高い。

---

## 数値（2015–2024 研究期・GBPJPY+AUDJPY除外）

| ケース | 件数 | 勝率 | PF | 合計R | maxDD |
|--------|-----:|-----:|---:|------:|------:|
| **SQZ Pine 2R** | 83 | 48.2% | **1.80** | +34.6 | 4.3R |
| **SQZ Pine 2.5R** | 83 | 44.6% | **1.87** | +40.5 | 4.3R |
| **SQZ STRICT 2R** | 35 | **57.1%** | **2.55** | +23.8 | **3.1R** |
| CAP Pine 2R | 139 | 38.1% | 1.04 | +3.6 | 13.5R |
| CAP Pine 2.5R | 138 | 34.8% | 1.08 | +7.9 | 12.5R |
| BOTH（SQZ優先）2R | 215 | 42.8% | 1.32 | +41.9 | 14.8R |
| BOTH 2.5R | 214 | 39.3% | 1.38 | +51.5 | 13.3R |

参考（全通貨・2015–2026）:

| ケース | 件数 | PF | 合計R |
|--------|-----:|---:|------:|
| SQZ Pine 2R | 135 | 1.48 | +36.4 |
| SQZ STRICT ex-GBP | 43 | **2.21** | +24.7 |
| CAP Pine 2R | 205 | 1.01 | +0.7 |

---

## TBとの重複

- SQZ（6通貨研究）と TrendBreak ロングの **保有重複は約 4%**。
- CAP は **約 1%** — 別系統。

→ アンサンブル上、SQZ は TB/T5 と **競合しにくい追加柱** になりうる。

---

## 運用ルール案（本格導入）

1. **時間足 H4**、ロングのみ。
2. **踏み上げ（SQZ）のみエントリー** — Pineデフォルト or STRICT（棚≤2ATR・急落≥3.5ATR）。
3. **GBPJPY 除外**（研究で一貫して弱い）。AUDJPY は T5 と同様 **除外推奨**。
4. **投げ切り（CAP）はアラート監視** — 「底候補」表示。単独ロットは入れない。
5. **利確** — 手動2.5R運用なら研究上も PF 微増（+34.6R→+40.5R）だが、**STRICT は 2R の方が勝率・DDが良い** → 本番は **2R推奨**、2.5Rはフォワード比較用。
6. **TB/T5 との優先** — 同銘柄・同時保有はルール化（例: T5 > SQZ > TB は要別検証。現状重複少）。

---

## 手動検証（XAGUSD TV）との関係

`Market_Psychology_Strategy_*_XAGUSD_2026-05-30.csv` は **7トレード・累積+11.5%** 程度。

バックテスト XAU SQZ strict: **10件・PF約4.5（全期間）** — 方向性は一致するが、**件数が少ない銘柄単体では過信しない**。

---

## 次ステップ（本格導入前）

- [ ] Pine を `pine/production/` に live-ready 化（SQZ のみ EXECUTE、CAP は WATCH）
- [ ] TradingView で **シグナル時刻 vs Python** 5件パリティ
- [ ] フォワード **最低20件**（SQZ strict・6通貨）
- [ ] 2R vs 2.5R を実トレード日記で並記
- [ ] TB+T5+SQZ 合算シミュレーション（重複時の優先ルール）

---

## ファイル

| 用途 | パス |
|------|------|
| 詳細CSV | `docs/research/cap_sqz_production_validation_2026-06-01/summary.csv` |
| 全トレード | `docs/research/cap_sqz_production_validation_2026-06-01/trades_all.csv` |
| 再実行 | `python3 scripts/validate_cap_sqz_production.py` |
| 既存TVチェック | `backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py` |
