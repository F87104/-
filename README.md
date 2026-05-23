# FX-AI — TrendBreakV1 + Sai Best Method アンサンブル戦略

> H1 ブレイクアウト系の自動売買戦略リポジトリ。10年バックテスト (2015-2024) で検証済みの 2戦略を組み合わせて運用する。

---

## 📚 ドキュメント目次

| ドキュメント | 内容 |
|---|---|
| 👉 **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** | **メインの説明書 (これを読めばOK)** |
| [backtests/ensemble/ensemble_report.md](backtests/ensemble/ensemble_report.md) | アンサンブル運用検証レポート |
| [backtests/ensemble/portfolio_comparison.md](backtests/ensemble/portfolio_comparison.md) | 通貨フィルタ別比較 |
| [backtests/audit/](backtests/audit/) | コスト・OOS監査 |
| [backtests/relaxation/RELAXATION_REPORT.md](backtests/relaxation/RELAXATION_REPORT.md) | パラメータ緩和スタディ |
| [backtests/comparison/comparison_report.md](backtests/comparison/comparison_report.md) | 戦略間比較 |

---

## 🎯 結論 (TL;DR)

### 採用戦略

| 戦略 | ファイル | 役割 |
|---|---|---|
| **TrendBreakV1** | [`pine/TrendBreakV1_Final.pine`](pine/TrendBreakV1_Final.pine) | 高EV・低頻度ブレイクアウト |
| **Sai Best Method** | [`pine/sai_best_method_strategy.pine`](pine/sai_best_method_strategy.pine) | V字+停滞 (相補性確保) |

### 推奨運用構成 (TOP5)

XAUUSD / SILVER / EURJPY / GBPJPY / XAGUSD の **5通貨ペア** に両戦略を同時運用。

### 10年バックテスト成績 (2015-2024, H1)

| 指標 | 値 |
|---|---|
| **Total R** | +235R |
| **WR** | 45.3% |
| **PF** | 1.99 |
| **MaxDD** | -11.3R |
| **Calmar** | **🟢 20.76** |
| **連敗最大** | 9 |
| **年間トレード** | 44 (月3.7回) |

> **Calmar 20** は機関投資家ファンドのトップ水準。

---

## 🚀 すぐ使う場合

1. **TradingView** を開く
2. **5チャート** (XAUUSD, SILVER, EURJPY, GBPJPY, XAGUSD) を H1 でセット
3. 各チャートに以下2つの Strategy を貼る:
   - `pine/TrendBreakV1_Final.pine` (Auto preset)
   - `pine/sai_best_method_strategy.pine` (デフォルト設定)
4. アラートを設定 → 通知が来たら手動 (または API 経由) で発注

詳細は **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** を参照。

---

## 📂 リポジトリ構成

```
fx-ai/
├── README.md                       ← このファイル (入り口)
├── STRATEGY_GUIDE.md               ← 戦略の説明書 (本体)
├── pine/                           ← TradingView Pine Script
│   ├── TrendBreakV1_Final.pine        本番1: ブレイクアウト
│   ├── sai_best_method_strategy.pine  本番2: V字+停滞
│   ├── sai_h1_visual_scanner.pine     Saiシグナル可視化 (Indicator)
│   ├── sai_mtf_visual_checker.pine    MTF確認用 (Indicator)
│   └── trendbreak_v1_final_fixed.pine 旧版 (archive)
├── backtests/                      ← Python バックテスト
│   ├── ensemble/                      アンサンブル運用検証 ⭐
│   ├── trendbreak_v1/                 TrendBreakV1 単独検証
│   ├── sai_h1/                        Sai 単独検証
│   ├── audit/                         コスト・OOS監査
│   ├── relaxation/                    緩和スタディ
│   └── comparison/                    戦略間比較
├── backtest/                       ← 既存のバックテストツール
├── F87104_test/                    ← OHLCデータ (2014-2024)
└── forex_tester_sai_scanner/       ← ForexTester用スキャナ (archive)
```

---

## 📈 戦略開発の経緯

```
[初期]  Sai H1 戦略 (低EV, PF 1.05) を発見 → 改善必要と判断
   ↓
[Step 1] TrendBreakV1 を発見 → 単独で PF 1.56, +551R (4モード合計)
   ↓
[Step 2] Sai を分解 → 「急な揺り戻し+高値停滞」だけ PF 1.47, +99R 抽出
   ↓
[Step 3] TrendBreakV1 を精密監査 → コスト込みでも +454R (-20%) で頑健
   ↓
[Step 4] パラメータ緩和スタディ → HYBRID最適化で頻度+27%
   ↓
[Step 5] アンサンブル運用検証 → Calmar 12.3 → 16.98 に改善
   ↓
[Step 6] 通貨フィルタリング → TOP5構成で Calmar 20.76 達成
```

---

## ⚠️ 注意事項

- **過去パフォーマンスは将来を保証しない**。資金は失っても困らない範囲で。
- **スプレッド・スリッページは想定済み** (audit 参照)
- **CHFJPY と AUDJPY は除外する**こと (リスク調整後リターンが劣化する)
- **2018年は全体的に苦戦する年**だった (低ボラ環境)。覚悟しておく。
- **DD 20%超え時は運用停止**を Pine Script に組み込み済み (`maxDDPctIn`)

---

## 📜 ライセンス

このリポジトリのコードは個人運用目的での使用を想定。商用利用・再配布は控えてください。
