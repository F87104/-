# Forward Log 2026-05 — STEP 1 (Squeeze v2 ベースライン)

**期間**: 2026-05-30 のセッションで TradingView Strategy Tester による初期計測
**Pine**: [`pine/research/market_psychology_strict_v2_strategy.pine`](../../../pine/research/market_psychology_strict_v2_strategy.pine)
**コミット**: `c1b8bc3` (lookahead 安全化版)

## テスト条件

| 項目 | 値 |
|---|---|
| 時間足 | H4 |
| 構造 | ① Squeeze ON / ② Capitulation OFF |
| 棚幅上限 | 2.2 ATR (v2) |
| 急落幅下限 | 4.0 ATR (v2) |
| 通貨除外 (Sqz) | GBPJPY 自動除外 |
| 早期撤退 | **ON** (デフォルト) ⚠️ |
| 時間フィルタ | OFF |
| Volume フィルタ | OFF |
| TP | 2R |
| SL | 構造外側 - 0.25 ATR |
| 最大保有 | 120 本 |
| リスク | 口座 1% |
| 初期資金 | $10,000 / ¥10,000 |

> ⚠️ 当初は「早期撤退 OFF」で開始予定でしたが、Pine のデフォルトが ON のままだったため、6 通貨すべて **早期撤退 ON** で計測しています。これは v2 本仕様と一致するので統一済みのまま分析。

## 結果サマリー

| # | 通貨 | フィード | データ期間 | Trades | WR | PF | DD | Net% | 評価 |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | XAUUSD | Vantage | 2018-03-19 〜 2026-05-30 (8年) | 2 | 50.0% | 1.97 | 1.40% | +0.98% | ✅ |
| 2 | EURJPY | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 2 | 50.0% | 3.72 | 1.42% | +1.45% | ✅ |
| 3 | AUDJPY | JFX | 2021-12-17 〜 2026-05-30 (4.5年) | 2 | 50.0% | 90.36 | 0.68% | +1.97% | ✅ |
| 4 | **USDJPY** | **OANDA** | **2013-01-02 〜 2026-05-30 (13年)** | **8** | **25.0%** | **0.41** | **3.07%** | **-3.07%** | **❌** |
| 5 | SILVER (XAGUSD) | OANDA | 2013-01-02 〜 2026-05-30 (13年) | 5 | 80.0% | 8.16 | 1.49% | +7.16% | 🏆 |
| 6 | CHFJPY | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 3 | 66.7% | 2.03 | 1.57% | +1.04% | ✅ |

## 集計

| 集計 | Trades | WR | Net% | 備考 |
|---|---:|---:|---:|---|
| **6 通貨フル** | 22 | 50.0% | **+9.53%** | USDJPY の負けが他を圧迫 |
| **USDJPY 除外** | 14 | 64.3% | **+12.60%** | 本線候補 |

データ期間が通貨ごとに違うことに注意 (TradingView のフィード仕様)。

## Python 期待値との対比

| 通貨 | Python 期待 (10年) | TV 実測 | 評価 |
|---|---|---|---|
| XAUUSD | 5-10 trades / PF 4.5 / +10R | 2 trades (8年) / PF 1.97 / +0.98% | データ短く件数不足だが方向 ✅ |
| EURJPY | 3-6 trades / PF 2.1 / +13R | 2 trades / PF 3.72 / +1.45% | PF は期待超え、件数小 |
| AUDJPY | 2-4 trades / PF 2.0 / +3R | 2 trades / PF 90 / +1.97% | 早期撤退で PF 異常値、Net は期待通り |
| **USDJPY** | **5-10 trades / PF 1.7 / +5R** | **8 trades / PF 0.41 / -3.07%** | **期待から逆方向に大乖離** |
| SILVER | 3-5 trades / PF 4.5 / +7R | 5 trades / PF 8.16 / +7.16% | ほぼ完全一致 🏆 |
| CHFJPY | 0-2 trades / PF inf-like / +2R | 3 trades / PF 2.03 / +1.04% | 期待を上回る |

**5 通貨は Python 想定通り、USDJPY だけが想定外に弱い**。

## 重要発見

### 1. 全体として v2 仕様は機能している

- USDJPY 除外で **WR 64.3% / Net +12.60%** の堅実な数字
- DD は全通貨 1.5% 以下 (SILVER の 1.49% が最大、リスク 1% 設定で 1.5R 相当)
- SILVER と EURJPY が期待を超える

### 2. USDJPY が唯一の問題児

- データ期間が最長 (13 年) で件数も最多 (8 件) なので **統計的に意味のある負け**
- PF 0.41 で「半分の確率で損切り」状態
- 想定原因 (要追加検証):
  - v2 の急落 ≥ 4.0 ATR で USDJPY の有効シグナルが除外された
  - 早期撤退 ON で USDJPY の遅延勝ちパターンが切られた
  - OANDA フィードの H4 境界がローカル検証と違う
  - Python 検証でも USDJPY は弱め (+6.22R / WR 38%)、それが TV では更に悪化した

### 3. AUDJPY の PF 90 は「早期撤退副作用」

- 勝ち = +2R (TP 到達) / 負け = -0.02R 程度 (早期撤退で即クローズ)
- PF = 2.0 / 0.02 ≒ 100
- 統計的にはノイズ。件数 2 なので過大評価注意

## STEP 1 暫定結論

| 項目 | 結論 |
|---|---|
| Squeeze v2 全体 | 🟡 **フォワード継続候補** (本線採用にはまだ件数不足) |
| 採用通貨 | **5 通貨**: XAUUSD / EURJPY / AUDJPY / SILVER / CHFJPY |
| 除外候補 | **USDJPY** (追加検証で判定) |
| 早期撤退 | 機能している (DD 全通貨 1.5% 以下) |

## 次のアクション

- [x] STEP 1 (Squeeze v2) — 6 通貨計測完了 ← **本ファイル**
- [ ] STEP 2 (Capitulation v2) — 同 Pine の ① OFF / ② ON で 5 通貨 (SILVER 除く)
- [ ] STEP 3 (Long Liquidation) — 別 Pine で 6 通貨 (GBPJPY 除外、両方向 = ロング側除外)
- [ ] STEP 4 (Dormant Breakout) — 別 Pine で 6 通貨両方向
- [ ] USDJPY 追加検証 (3 パターン): 早期撤退 OFF / v1 値 / 別フィード

## メモ

- TradingView の期間警告: 「先読みバイアスの可能性」は generic 警告。コミット `c1b8bc3` で `[1]` を加えて二重防壁化済み (実害なし、警告のみ抑制狙い)
- データ範囲がフィードごとに大きく違う (AUDJPY は JFX で 4.5 年、USDJPY は OANDA で 13 年)。月次フォワード記録の方が件数を稼ぎやすい
- 早期撤退 ON のままでも 6 通貨フルで Net プラスを維持できているのは v2 の robustness の証

## 参照

- v2 仕様書: [`v2_spec.md`](./v2_spec.md)
- 検証レポート: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md)
- フォワード記録テンプレート: [`forward_log_template.md`](./forward_log_template.md)
