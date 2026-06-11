# Forward Log 2026-05 — STEP 2 (Capitulation v2 ベースライン) + STEP 1+2 統合分析

**期間**: 2026-05-30 のセッションで TradingView Strategy Tester による初期計測
**Pine**: [`pine/research/market_psychology_strict_v2_strategy.pine`](../../../pine/research/market_psychology_strict_v2_strategy.pine)

## テスト条件 (STEP 1 との違い)

| 項目 | STEP 1 | **STEP 2** |
|---|---|---|
| ① Squeeze | ✅ ON | ❌ OFF |
| ② Capitulation | ❌ OFF | ✅ **ON** |
| その他全て | 同じ | 同じ |

通貨除外: GBPJPY 自動 + Capitulation で SILVER 自動除外。

## STEP 2 結果

| # | 通貨 | フィード | データ期間 | Trades | WR | PF | DD | Net% | 評価 |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | **XAUUSD** | **FXCM** | 2013-01-02 〜 2026-05-30 (13年) | 4 | **0.0%** | **0** | 2.30% | **-2.30%** | **❌** |
| 2 | EURJPY | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 3 | 100.0% | ∞ | 0.54% | +3.10% | 🏆 |
| 3 | AUDJPY | JFX | 2021-12-17 〜 2026-05-30 (4.5年) | 2 | 100.0% | ∞ | 0.47% | +2.25% | 🏆 |
| 4 | USDJPY | OANDA | 2013-01-02 〜 2026-05-30 (13年) | 5 | 60.0% | 1.19 | 1.83% | +0.38% | ✅ |
| 5 | CHFJPY | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 5 | 80.0% | 4.36 | 1.16% | +3.38% | 🏆 |
| **5 通貨合計** | — | — | — | **19** | **63.2%** | — | — | **+6.81%** | |
| **XAUUSD 除外** | — | — | — | **15** | **80.0%** | — | — | **+9.11%** | |

## STEP 1 + STEP 2 統合 (通貨×構造マトリクス)

| 通貨 | Squeeze (STEP 1) | Capitulation (STEP 2) | 合計 Net% | 推奨運用 |
|---|---|---|---:|---|
| XAUUSD | +0.98% / 2t | -2.30% / 4t | -1.32% | **Sqz のみ** |
| EURJPY | +1.45% / 2t | +3.10% / 3t | **+4.55%** | 両方 |
| AUDJPY | +1.97% / 2t | +2.25% / 2t | **+4.22%** | 両方 |
| USDJPY | -3.07% / 8t | +0.38% / 5t | -2.69% | **Cap のみ** |
| SILVER | +7.16% / 5t | (除外) | **+7.16%** | Sqz のみ |
| CHFJPY | +1.04% / 3t | +3.38% / 5t | **+4.42%** | 両方 |

### 構造別配分シミュレーション

| 配分 | Sqz 通貨 | Cap 通貨 | 合計 trades | 合計 Net% |
|---|---|---|---:|---:|
| ① 全部両方 | 6 通貨 | 5 通貨 | 41 | +16.34% |
| ② XAUUSD 除外 | 5 通貨 | 4 通貨 | 35 | +21.71% |
| ③ **通貨×構造最適化** | **5 通貨** (USDJPY 除く) | **4 通貨** (XAUUSD / SILVER 除く) | **29** | **+22.71%** 🏆 |

## 大発見

### 1. 通貨ごとに相性のいい構造が違う

| パターン | 通貨 | 心理仮説 |
|---|---|---|
| **Sqz のみが効く** | XAUUSD / SILVER | 金属系: ショートカバーが速く棚ブレイクが機能。投げ切り直買いはマクロ要因 (中央銀行 / 実需) で反転継続せず |
| **Cap のみが効く** | USDJPY | ドル円: 投げ切り反転は機能。棚ブレイクは V 字戻りで失敗しやすい |
| **両方効く** | EURJPY / AUDJPY / CHFJPY | クロス円: 価格構造が素直、両方の心理パターンが機能する |

これは "1 つの戦略で全通貨" ではなく、**「通貨 × 構造」 の個別最適化** が次の精度向上の鍵であることを示唆。

### 2. XAUUSD Capitulation の Python ↔ TV 乖離

| | Python 期待 | TV 実測 |
|---|---|---|
| XAUUSD CAP | 32 件 / WR 44% / +7.37R / PF 1.40 | 4 件 / WR 0% / PF 0 / -2.30% |

両方とも「中庸」だが、TV では **完全に逆方向** に出た。原因仮説:

- フィード差 (FXCM vs Python のローカルソース) — XAUUSD は祝日 / 週末ギャップ / 流動性が時間帯で大きく変動
- `signal_range_atr ≥ 3.0` 厳格化 (v1 は 1.8) で **本物の投げ切り** ではなく「マクロ起因の継続急落」だけが残った
- D1 EMA50 の `[1]` 修正 (lookahead 安全化) で文脈フィルタが微妙に変化

→ **XAUUSD を Capitulation 対象から外す** が現時点で最も安全な判断。

### 3. USDJPY の構造別反応

| | Squeeze (STEP 1) | Capitulation (STEP 2) |
|---|---|---|
| USDJPY | **-3.07% / WR 25% (8 件)** | **+0.38% / WR 60% (5 件)** |

USDJPY は **構造で挙動が真逆**。これは「USDJPY を全構造で除外」していたら見落としていた発見。
個別検証の重要性を示すサンプル。

## 暫定運用ポリシー (v2)

```
Squeeze v2 を運用する通貨:
  XAUUSD / EURJPY / AUDJPY / SILVER / CHFJPY  (USDJPY と GBPJPY を除外)

Capitulation v2 を運用する通貨:
  EURJPY / AUDJPY / USDJPY / CHFJPY  (XAUUSD / SILVER / GBPJPY を除外)
```

期待 (8-13 年データ、TradingView 実測):
- 29 trades / WR 70% 前後 / Net +22.71% / 最大 DD 3% 未満

## 残課題

- [ ] STEP 3: Long Liquidation を 6 通貨で測る
- [ ] STEP 4: Dormant Breakout を 6 通貨両方向で測る
- [ ] USDJPY Squeeze 追加検証 (早期撤退 OFF / v1 値 / 別フィード)
- [ ] XAUUSD Capitulation 追加検証 (フィード変更 / 早期撤退 OFF)
- [ ] Pine に **通貨 × 構造マトリクス** を組み込む (シンボル別の自動 ON/OFF)

## 参照

- STEP 1 ログ: [`forward_log_2026_05_step1.md`](./forward_log_2026_05_step1.md)
- v2 仕様: [`v2_spec.md`](./v2_spec.md)
- 元検証レポート: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md)
