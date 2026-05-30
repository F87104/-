# 市場心理 v2 統合仕様 (Market Psychology Strict v2)

> Deep research の 10 項目を統合した、現時点での **最強仕様**。
> 詳細な検証根拠: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md)

**作成日**: 2026-05-30
**親ドキュメント**: [`README.md`](./README.md) / [`framework.md`](./framework.md) / [`status.md`](./status.md)
**Pine 実装**: [`pine/research/market_psychology_strict_v2_strategy.pine`](../../../pine/research/market_psychology_strict_v2_strategy.pine)

---

## 1. v1 → v2 で変えたこと (一覧)

| 項目 | v1 | v2 | 根拠 (deep research) |
|---|---|---|---|
| Squeeze 棚幅上限 | 2.0 ATR | **2.2 ATR** | #3 ヒートマップ最良セル |
| Squeeze 急落幅下限 | 3.5 ATR | **4.0 ATR** | #3 |
| Squeeze 候補足 body/close_loc | なし | **入れない** (寄与なし確認) | #4 |
| Capitulation シグナル足値幅 | 1.8 ATR | **3.0 ATR** ⭐ 最重要 | #10 (PF 1.06 → 2.06) |
| Capitulation 通貨除外 | GBPJPY | **GBPJPY + SILVER** | #9 |
| Squeeze 通貨除外 | GBPJPY | GBPJPY (変更なし) | #9 確認 |
| 早期撤退 | なし | **MFE < 0.5R after 12 bars → -0.35R 撤退** | #2 |
| 時間フィルタ | なし | **4 / 8 / 16 / 20 UTC のみ** (任意) | #8 |
| Volume フィルタ | なし | **vol > sma(20) × 1.3** (任意 / TV のみ) | #1 |
| 重複制御 | 不要 | **不要** (他戦略との重複ゼロ確認) | #7 |
| TP | 2R | 2R |  |
| SL | 構造外側 - 0.25 ATR | 構造外側 - 0.25 ATR |  |
| 最大保有 | 120 本 | 120 本 |  |

---

## 2. v2 期待成績

### Squeeze v2 (主力)

| 仕様 | trades | WR | total R | PF | DD | 連敗 |
|---|---:|---:|---:|---:|---:|---:|
| v1 SQZ_STRICT_RR2 ex GBPJPY | 43 | 53.5% | +24.72R | 2.21 | 3.09R | 3 |
| + 棚 2.2 / 急落 4.0 (#3) | 21 | 57.1% | +14.38R | 2.57 | 2.06R | 2 |
| + 早期撤退 (#2 推定上限) | 21 | 57.1% | +14.38R | 2.57 | 2.06R | 2 |
| + 時間フィルタ 4/8/16/20 (#8) | **15** | **60.0%** | **+11.56R** | **2.88** | **2.06R** | **2** |

**PF +30% / DD -33% / 件数 -65%** (件数低下は他構造で補う方針)

### Capitulation v2 (副軸)

| 仕様 | trades | WR | total R | PF | DD |
|---|---:|---:|---:|---:|---:|
| v1 CAP_DEFAULT_RR2 ex GBPJPY | 175 | 38.3% | +6.46R | 1.06 | 26.46R |
| **+ sig_range_atr ≥ 3.0 (#10)** | **33** | **60.6%** | **+14.15R** | **2.06** | **4.51R** |

**PF 2 倍 / DD 1/6 / Capitulation を本線へ昇格可能**

### Squeeze + Capitulation 並走

両者は構造的に独立。同 Pine で両 ON にして合算想定:

- 期待 trades: 45-70 件 (10 年)
- 期待 Total R: +25-30R
- 期待 PF: 2.5+
- 期待 DD: 5R 以下

---

## 3. 通貨方針 (v2 確定)

### Squeeze v2

| 通貨 | 採用 | 根拠 (#9) |
|---|---|---|
| XAUUSD | ⭐ 本命 | MFE 平均 2.43R / WR 69% / +54.23R |
| EURJPY | ✅ 採用 | WR 51% / +34.85R |
| AUDJPY | ✅ 採用 | WR 47% / +18.94R |
| USDJPY | ✅ 採用 (弱め) | WR 38% / +6.22R |
| SILVER | ⚠️ 監視 | WR 42% / +6.19R (Cap では弱いので注意) |
| CHFJPY | ⚠️ 監視 | WR 36% / +2.75R (件数不足) |
| **GBPJPY** | ❌ **除外** | WR 36% / **-5.77R** |

### Capitulation v2

| 通貨 | 採用 | 根拠 (#9) |
|---|---|---|
| XAUUSD | ⭐ 本命 | +30.16R |
| CHFJPY | ✅ 採用 | +18.50R |
| AUDJPY | ✅ 採用 | +18.10R |
| USDJPY | ✅ 採用 (弱め) | +4.45R |
| EURJPY | ⚠️ 監視 | +3.39R |
| **GBPJPY** | ❌ **除外** | -20.06R |
| **SILVER** | ❌ **除外** ⭐ 新規 | **-37.85R** (構造的に弱い) |

---

## 4. v2 共通エントリー / 出口

```
エントリー:
  - シグナル成立は H4 確定足のみ
  - エントリー価格: 次足始値
  - サイジング: 口座 1% リスク固定

出口 (3 通り、早い方を採用):
  1. SL = 構造外側 - 0.25 ATR  (Squeeze=棚安値、Cap=投げ切り足安値)
  2. TP = 2R 固定
  3. 早期撤退 (任意 ON):
     経過 12 バー時点で MFE < 0.5R なら -0.35R で撤退
  4. 強制クローズ: 120 バー保有で時間切れ
```

---

## 5. 任意フィルタ (推奨運用)

### 時間フィルタ (#8)

```
hour in {4, 8, 16, 20}  // UTC
```

理由:
- 16 UTC (NY 11:00) が PF 5.91 と突出
- 4 / 8 / 20 もすべて PF >= 1.9
- 12 UTC は PF 1.29 → 除外

⚠️ 件数 6-10 件/時間と少ない。本番固定ではなくフォワード監視タグ扱い推奨。

### Volume フィルタ (#1, TV 限定)

```
volume > sma(volume, 20) * 1.3
```

理由:
- ローカル OHLC では検証不能。TV 実 volume で ON/OFF 比較
- 特に Capitulation で効果が期待される (投げ切り = 出来高急増の心理仮説)

---

## 6. 残課題 (本番昇格条件)

このまま v2 を **本線採用 🟢** にはまだしない。以下を満たす必要がある:

- [ ] **フォワード 30 件記録** (Squeeze v2)
- [ ] **フォワード 30 件記録** (Capitulation v2)
- [ ] **フォワード 30 件記録** (Long Liquidation) ← 🆕 Pine 実装済み
- [ ] **フォワード 30 件記録** (Dormant Breakout) ← 🆕 Pine 実装済み
- [ ] **Pine ↔ Python parity** (v2 のシグナル時刻を Python で再現できるか)
- [ ] **Volume フィルタの効果検証** (TV 上で ON/OFF 比較)
- [ ] **Long Liquidation / Dormant Breakout の OHLC 検証** (OHLC が利用可能になった時点で Python で過去全期間を回す)

これら満了で初めて **🟢 本線採用** へ昇格。

フォワード記録は [`forward_log_template.md`](./forward_log_template.md) を月初にコピーして始める。

---

## 7. ステータス更新

[`status.md`](./status.md) のテーブルを以下に更新する想定:

| # | 研究 | 旧判定 | **新判定 (v2)** |
|---|---|---|---|
| R6 | Market Psychology Squeeze | 🟡 フォワード候補 | 🟡 → **v2 でブラッシュアップ済み、フォワード継続** |
| R-new | Capitulation v2 (sig_range ≥ 3.0) | (R4 系で保留) | 🟡 **新規フォワード候補** |
| R-new | Deep Research v2 | — | ⚪ **本仕様** (v2_spec.md) |

---

## 8. 関連ファイル

### 検証 / レポート
- 検証コード: [`backtests/elliott_fibo/run_market_psychology_v2_deep_research.py`](../../../backtests/elliott_fibo/run_market_psychology_v2_deep_research.py)
- 結果フォルダ: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/)
- 詳細レポート: [`report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md)

### Pine (本命 v2)
- v2 統合 strategy: [`pine/research/market_psychology_strict_v2_strategy.pine`](../../../pine/research/market_psychology_strict_v2_strategy.pine)
- 🆕 Long Liquidation strategy: [`pine/research/market_psychology_long_liquidation_strategy.pine`](../../../pine/research/market_psychology_long_liquidation_strategy.pine)
- 🆕 Long Liquidation visual: [`pine/visual/market_psychology_long_liquidation_visual.pine`](../../../pine/visual/market_psychology_long_liquidation_visual.pine)
- 🆕 Dormant Breakout strategy: [`pine/research/market_psychology_dormant_breakout_strategy.pine`](../../../pine/research/market_psychology_dormant_breakout_strategy.pine)
- 🆕 Dormant Breakout visual: [`pine/visual/market_psychology_dormant_breakout_visual.pine`](../../../pine/visual/market_psychology_dormant_breakout_visual.pine)

### フォワード記録
- 月次テンプレート: [`forward_log_template.md`](./forward_log_template.md)

### Pine (v1 比較用)
- v1 default Pine: [`pine/research/market_psychology_strategy.pine`](../../../pine/research/market_psychology_strategy.pine)
- v1 strict Pine: [`pine/research/market_psychology_squeeze_strict_strategy.pine`](../../../pine/research/market_psychology_squeeze_strict_strategy.pine)
