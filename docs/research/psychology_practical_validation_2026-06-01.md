# 心理マップ — 実践検証（2026-06-01）

目的: **TrendBreak / T5 の実トレード**に H1 STOP・停滞(CHECK) を重ね、採用できるゲートだけ残す。

## 運用ルール（採用案）

| 優先 | ルール | 内容 |
|---:|---|---|
| 1 | **エントリー足の S** | 24h ではなく **その足に S** が付いた TB だけ見送り（過剰ブロックを避ける） |
| 2 | **CHECK** | 同方向 STOP でも `pre_range_6 ≤ 2.5 ATR` なら TB 可（停滞→再ブレイク） |
| 3 | **方向別（任意）** | XAU 売り / GBP 買いで 6h 内 STOP → 慎重（PF↑・件数↓） |
| 4 | **T5は止めない** | H4 T5 は心理ゲート非適用 |
| 5 | **マップ** | 赤＝追い確認。全面禁止にしない |

## TB と心理フラグの重なり

- エントリー足に同方向 STOP: **13.1%**
- 6本以内に同方向 STOP: **99.0%**
- 24本以内に同方向 STOP: **99.0%**（広すぎ・自動ブロック非推奨）

## TrendBreak ゲート比較（2015–2024 baseline）

| gate | trades | total_r | PF | win_rate | avg_r |
|---|---:|---:|---:|---:|---:|
| baseline_all | 381 | +194.6 | 1.79 | 39.4% | +0.511 |
| favor_sweep_down_long_only | 368 | +184.5 | 1.78 | 39.1% | +0.501 |
| block_f1_on_entry_bar | 336 | +157.9 | 1.72 | 38.4% | +0.470 |
| block_stop_on_entry_bar | 331 | +151.2 | 1.69 | 38.1% | +0.457 |
| asym_xau_sell_gbp_buy_stop | 314 | +144.5 | 1.70 | 38.2% | +0.460 |
| block_same_dir_unless_check | 208 | +135.3 | 2.08 | 42.8% | +0.650 |
| asym_plus_check | 179 | +113.6 | 2.05 | 42.5% | +0.635 |
| block_f1_6h | 134 | +63.8 | 1.72 | 38.8% | +0.476 |
| block_f1_only_24h | 81 | +35.3 | 1.65 | 38.3% | +0.435 |
| block_stop_any_24h | 2 | +2.0 | 2.91 | 50.0% | +0.975 |
| block_same_dir_unless_check_h1only | 25 | +1.1 | 1.06 | 28.0% | +0.046 |
| block_same_dir_stop_6h | 4 | -0.3 | 0.91 | 25.0% | -0.075 |
| block_same_dir_stop_24h | 4 | -0.3 | 0.91 | 25.0% | -0.075 |

**推奨ゲート:** `baseline_all (no gate beat baseline)`（total_r 最大・件数過少なし）

## 通貨別 Pine プリセット

```json
{
  "GBPJPY": {
    "prox_yen": 0.25,
    "prox_half": 0.15,
    "ext_atr": 0.6,
    "swing_len": 48,
    "big_mult": 1.05,
    "strict_f1": true,
    "wick_atr": 0.4,
    "sweep_lb": 20,
    "fwd_bars": 72
  },
  "XAUUSD": {
    "prox_yen": 0.25,
    "prox_half": 0.15,
    "ext_atr": 0.85,
    "swing_len": 48,
    "big_mult": 1.05,
    "strict_f1": false,
    "wick_atr": 0.4,
    "sweep_lb": 20,
    "fwd_bars": 48
  },
  "USDJPY": {
    "prox_yen": 0.25,
    "prox_half": 0.15,
    "ext_atr": 0.6,
    "swing_len": 48,
    "big_mult": 1.05,
    "strict_f1": true,
    "wick_atr": 0.4,
    "sweep_lb": 20,
    "fwd_bars": 12
  },
  "DEFAULT": {
    "prox_yen": 0.25,
    "prox_half": 0.15,
    "ext_atr": 0.85,
    "swing_len": 48,
    "big_mult": 1.05,
    "strict_f1": true,
    "wick_atr": 0.4,
    "sweep_lb": 20,
    "fwd_bars": 24
  }
}
```

## STOP 成分（H1本数ベース）

### XAUUSD
- f1_long: 1554本 (2.63%)
- f2_long: 2790本 (4.72%)
- brk_long: 1199本 (2.03%)
- f1_short: 1287本 (2.18%)
- f2_short: 2775本 (4.70%)
- brk_short: 921本 (1.56%)
- stop_long: 4515本 (7.64%)
- stop_short: 4143本 (7.01%)
- sweep_down: 334本 (0.57%)

### USDJPY
- f1_long: 1550本 (2.49%)
- f2_long: 2829本 (4.55%)
- brk_long: 1415本 (2.28%)
- f1_short: 1279本 (2.06%)
- f2_short: 2862本 (4.61%)
- brk_short: 1089本 (1.75%)
- stop_long: 4317本 (6.95%)
- stop_short: 3990本 (6.42%)
- sweep_down: 343本 (0.55%)

### EURJPY
- f1_long: 2193本 (3.63%)
- f2_long: 3231本 (5.35%)
- brk_long: 1382本 (2.29%)
- f1_short: 1939本 (3.21%)
- f2_short: 3339本 (5.52%)
- brk_short: 1120本 (1.85%)
- stop_long: 5123本 (8.48%)
- stop_short: 4914本 (8.13%)
- sweep_down: 356本 (0.59%)

### GBPJPY
- f1_long: 2160本 (3.57%)
- f2_long: 3328本 (5.51%)
- brk_long: 1354本 (2.24%)
- f1_short: 1849本 (3.06%)
- f2_short: 3415本 (5.65%)
- brk_short: 1130本 (1.87%)
- stop_long: 5203本 (8.61%)
- stop_short: 4856本 (8.03%)
- sweep_down: 359本 (0.59%)

### CHFJPY
- f1_long: 2262本 (3.64%)
- f2_long: 2842本 (4.57%)
- brk_long: 1216本 (1.96%)
- f1_short: 1918本 (3.09%)
- f2_short: 2765本 (4.45%)
- brk_short: 1003本 (1.61%)
- stop_long: 4825本 (7.76%)
- stop_short: 4397本 (7.07%)
- sweep_down: 429本 (0.69%)

### SILVER
- f1_long: 1087本 (1.84%)
- f2_long: 2612本 (4.43%)
- brk_long: 1007本 (1.71%)
- f1_short: 937本 (1.59%)
- f2_short: 2638本 (4.47%)
- brk_short: 856本 (1.45%)
- stop_long: 3693本 (6.26%)
- stop_short: 3484本 (5.91%)
- sweep_down: 348本 (0.59%)

## 青帯（待つ場所）到達率

- ゾーン数 17 / 期間内に帯タッチ **94.1%**

| rank | currency | rule | touched |
|---:|---|---|---|
| 1 | XAUUSD | pullback | ✓ |
| 2 | GBPJPY | pullback | ✓ |
| 3 | USDJPY | bounce | ✓ |
| 4 | GBPJPY | bounce | ✓ |
| 5 | GBPJPY | pullback | ✓ |
| 6 | XAUUSD | pullback | ✓ |
| 7 | GBPJPY | pullback | ✓ |
| 8 | GBPJPY | bounce | ✓ |
| 9 | USDJPY | pullback | ✓ |
| 10 | USDJPY | pullback | ✓ |
| 11 | GBPJPY | bounce | ✓ |
| 12 | XAUUSD | pullback | ✓ |
| 13 | USDJPY | pullback | — |
| 14 | GBPJPY | pullback | ✓ |
| 16 | GBPJPY | pullback | ✓ |
| 17 | AUDJPY | pullback | ✓ |
| 18 | AUDJPY | pullback | ✓ |

## 結論（実践）

1. **TBを心理マップで自動全停止しない** — 6h/24h 内 STOP は TB の ~99% と重なるため。
2. **手動の見送りは「エントリー足に S」**（約13%）— `block_stop_on_entry_bar` でも総Rは +194→+151 と減るため、
   エンジン組み込みより **最終チェック** 向き。
3. **CHECK** — 同方向 STOP でも TB の `pre_range_6_atr ≤ 2.5` なら見送り不要（PF 2.08・件数半減のトレードオフ）。
4. **狩り後ロング** — `favor_sweep_down_long_only` は総Rほぼ維持（+184.5）→ 下狩り直後の追い買いだけ注意。
5. **T5** — 心理ゲート不要（30件・PF3.4）。
6. **青帯** — 待ちゾーンは期間内タッチ率高い → 飛び乗り禁止・押し/戻り待ちの教材と一致。

### エントリー前チェックリスト（TB）

- [ ] エントリー足に **S** が無い（あれば見送り or ロット半減）
- [ ] S が出ていても **直前6本が停滞**（レンジ/ATR≤2.5）なら CHECK → TB可
- [ ] XAU 売り / GBP 買いで節目追いなら **赤帯・整数** を確認
- [ ] 直近に **安値狩り＋陽線** なら追い買い慎重
- [ ] T5 シグナルは心理マップと独立に優先

## ファイル

- `psychology_practical_gate_results_2026-06-01.csv` — ゲート一覧
- `psychology_practical_presets_2026-06-01.json` — Pine 入力用プリセット
- `psychology_liquidity_param_sweep_2026-06-01.md` — パラメータスイープ

## TradingView

- 目視: `pine/visual/psychology_map_live.pine`（プリセットを通貨で切替）
- TB 試験: エントリー前24本に S が出たら手動見送り（CHECK は停滞足ありなら可）
