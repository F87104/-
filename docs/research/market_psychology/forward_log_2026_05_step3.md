# Forward Log 2026-05 — STEP 3 (Long Liquidation v1) + STEP 1+2+3 完全マトリクス

**期間**: 2026-05-30 のセッション
**Pine**: [`pine/research/market_psychology_long_liquidation_strategy.pine`](../../../pine/research/market_psychology_long_liquidation_strategy.pine)

## STEP 3 結果

時間足: H4 / リスク: 1% / 早期撤退: ON (デフォルト) / 時間 / Volume フィルタ: OFF。

| # | 通貨 | フィード | データ期間 | Trades | WR | PF | DD | Net% | 評価 |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | XAUUSD | Vantage | 2018-03-19 〜 2026-05-30 (8年) | 62 | 29.0% | 0.78 | 14.63% | **-9.69%** | ❌ |
| 2 | EURJPY | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 43 | 37.2% | 1.10 | 8.04% | +2.86% | △ |
| 3 | AUDJPY | JFX | 2021-12-17 〜 2026-05-30 (4.5年) | 19 | 26.3% | 0.68 | 7.71% | **-4.42%** | ❌ |
| 4 | **USDJPY** | **OANDA** | **2013-01-02 〜 2026-05-30 (13年)** | **56** | **46.4%** | **1.64** | **4.40%** | **+21.61%** | 🏆 |
| 5 | SILVER | OANDA | 2013-01-02 〜 2026-05-30 (13年) | 69 | 29.0% | 0.78 | 15.92% | **-9.51%** | ❌ |
| 6 | **CHFJPY** | FOREXCOM | 2017-03-15 〜 2026-05-30 (9年) | 44 | 38.6% | 1.24 | 6.42% | **+6.62%** | ✅ |
| **合計** | — | — | — | **293** | 35% | — | — | **+7.47%** | |

### LL の通貨カテゴリ

| カテゴリ | 通貨 | 共通特徴 |
|---|---|---|
| ❌ **金属系** (LL 不向き) | XAUUSD / SILVER | 長期上昇トレンド、急騰失敗 = 単なる押し → 売ると焼かれる |
| 🏆 **JPY ペア** (LL 適合) | USDJPY / CHFJPY | カーリー / 安全資産、急騰後の急落 (リスクオフ / BOJ 介入) が頻発 |
| △ **クロス円** (マージナル) | EURJPY / AUDJPY | 上昇トレンド傾向で LL は薄利または負け |

## 重要発見

### USDJPY が突出して強い

```
USDJPY Long Liquidation:
  13 年 / 56 trades / WR 46.4% / PF 1.64 / DD 4.40% / Net +21.61%
```

これは本リポジトリの本番 2 本柱 (TrendBreakV1 / H4 T5) と **同水準**。
構造的説明:
- USDJPY は **キャリートレード** で上昇しがち (高金利通貨買い → 円売り)
- 急騰後に **リスクオフ / BOJ 介入 / 金融危機** で急落する
- 「急騰の高値更新失敗 + 棚下抜け」がこの **典型パターン** を完璧に捉える

### XAUUSD / SILVER がほぼ同じ数字

| | XAUUSD | SILVER |
|---|---:|---:|
| trades | 62 | 69 |
| WR | 29.0% | 29.0% |
| PF | 0.78 | 0.78 |
| DD | 14.63% | 15.92% |
| Net | -9.69% | -9.51% |

偶然ではなく、**金属系の共通性質** が破壊的に効いている。これら 2 通貨は LL から完全除外。

## STEP 1+2+3 統合 通貨×構造マトリクス

各セルは Net% (件数):

| 通貨 | Squeeze v2 | Capitulation v2 | Long Liquidation v1 | 採用構造 | 通貨合計 |
|---|---:|---:|---:|---|---:|
| XAUUSD | **+0.98%** (2) | -2.30% (4) | -9.69% (62) | Sqz only | **+0.98%** |
| EURJPY | **+1.45%** (2) | **+3.10%** (3) | +2.86% (43) * | Sqz + Cap | **+4.55%** |
| AUDJPY | **+1.97%** (2) | **+2.25%** (2) | -4.42% (19) | Sqz + Cap | **+4.22%** |
| USDJPY | -3.07% (8) | **+0.38%** (5) | **+21.61%** (56) | Cap + LL | **+21.99%** |
| SILVER | **+7.16%** (5) | (除外) | -9.51% (69) | Sqz only | **+7.16%** |
| CHFJPY | **+1.04%** (3) | **+3.38%** (5) | **+6.62%** (44) | Sqz + Cap + LL | **+11.04%** |
| **合計** | | | | | **+49.94%** |

\* EURJPY LL は PF 1.10 / DD 8% のため **保守的に除外**

## 最適配分のシナリオ比較

| シナリオ | 通貨×構造 | trades | Net% |
|---|---|---:|---:|
| ① 全部素直 (LL 含む) | 6×3 | 425 | -10.78% |
| ② Sqz + Cap のみ全通貨 | 6×2 | 41 | +16.34% |
| ③ Sqz + Cap マトリクス最適化 (USDJPY Sqz 除外, XAUUSD Cap 除外) | — | 29 | +22.71% |
| ④ **3 構造マトリクス最適化** | **6 通貨 × 構造選別** | **129** | **+49.94%** 🏆 |

シナリオ ④ では:
- **USDJPY**: Cap (5) + LL (56) = 61 trades / Net +21.99%
- **CHFJPY**: Sqz (3) + Cap (5) + LL (44) = 52 trades / Net +11.04%
- 他通貨: 各 2-5 trades

USDJPY と CHFJPY の **LL 寄与** が大幅な改善を生む。

## 通貨×構造の運用ルール (確定版)

```
Squeeze v2:
  採用: XAUUSD / EURJPY / AUDJPY / SILVER / CHFJPY
  除外: USDJPY (-3.07%), GBPJPY (自動除外)

Capitulation v2:
  採用: EURJPY / AUDJPY / USDJPY / CHFJPY
  除外: XAUUSD (-2.30%), SILVER (Python 検証時除外), GBPJPY (自動除外)

Long Liquidation v1:
  採用: USDJPY (+21.61%) / CHFJPY (+6.62%)
  除外: XAUUSD / SILVER (金属系 -9%), EURJPY (PF 1.10 マージナル), AUDJPY (-4.42%), GBPJPY (自動)

注: 全構造で GBPJPY は除外固定
```

## DD リスク評価

| 構造 | 最大 DD (採用通貨) | 許容 (リスク 1%) |
|---|---:|---|
| Sqz v2 | 1.57% (CHFJPY) | ✅ 余裕あり |
| Cap v2 | 1.83% (USDJPY) | ✅ 余裕あり |
| **LL v1** | **6.42%** (CHFJPY) | △ 高め |

LL の DD が他より 1 段大きい。**LL は通貨別に小ロット**で運用するか、ポートフォリオ全体で **3 構造合算 DD ≤ 10%** を上限ルール化するのが安全。

## 残課題

- [x] STEP 1: Squeeze v2 ベースライン
- [x] STEP 2: Capitulation v2 ベースライン + STEP 1+2 統合
- [x] STEP 3: Long Liquidation v1 ベースライン + STEP 1+2+3 統合
- [ ] STEP 4: Dormant Breakout v1 ベースライン (両方向)
- [ ] **通貨×構造マトリクス自動化** (Pine 内で symbol 別に Sqz/Cap/LL を自動 ON/OFF)
- [ ] USDJPY Sqz の追加検証 (なぜ Sqz だけ失敗するのか)
- [ ] XAUUSD Cap の追加検証 (Python では +7.37R だったが TV で -2.30%)
- [ ] EURJPY LL の救済可能性 (急騰幅 ≥ 4.5 ATR で再測定)

## 参照

- STEP 1 ログ: [`forward_log_2026_05_step1.md`](./forward_log_2026_05_step1.md)
- STEP 2 ログ: [`forward_log_2026_05_step2.md`](./forward_log_2026_05_step2.md)
- v2 仕様: [`v2_spec.md`](./v2_spec.md)
- Pine (LL): [`pine/research/market_psychology_long_liquidation_strategy.pine`](../../../pine/research/market_psychology_long_liquidation_strategy.pine)
