# V字回復 応用手法仕様書 (2026-05-30)

> H4 急落 V 字回復ロジックを土台に、再現性ある複数手法へ応用するための研究ノート。
> 目的:「急落後に大衆が売り切ったあと、買い戻しが本格化する局面」を数値化し、検証可能な
> エントリ・除外条件・期待値計測手順としてまとめる。

---

## 0. 目次

1. 中核エッジの再定義
2. 機能しやすい相場環境 / 機能しにくい相場環境
3. 応用手法 7 候補
4. 除外条件マスター
5. 検証マトリクス（網羅すべき切り口）
6. 最有望案: **Variant A "D1 トレンド整合プルバック V"** の完全仕様
7. 期待される統計プロファイル
8. 実装ロードマップ

---

## 1. 中核エッジの再定義

### 1.1 ベースロジック（土台）

| 項目 | 値 |
|---|---|
| 時間足 | H4 |
| 検出 | confirmed pivot high → confirmed pivot low の急落 |
| 急落幅 | ≥ 3.5 ATR(14) |
| 回復 | 終値 ≥ 急落開始の pivot high の水準 |
| 回復本数 | ≤ 下落本数 |
| シグナル足品質 | 実体比率 ≥ 60% |
| Entry | シグナル足終値 or 次足始値 |
| SL | V 谷 − 0.25 ATR |
| TP | Entry + 2R |

### 1.2 何故これがエッジになるのか

急落 V 字回復は、本質的に **「ポジション圧潰 → 流動性ボイド → リバーサル」** という市場構造のシグナル。

| 局面 | 構造 | プレイヤー行動 |
|---|---|---|
| 急落 (左肩) | ストップ狩り・損切り連鎖 | 弱気が売り切る |
| 谷 | 流動性ボイド | 板が薄くなる |
| 右肩 (回復) | 機関の買い戻し / カバー | 売り側がショートカバー |
| シグナル足 | 大衆が「もう底だ」と気付く前 | スマートマネー先行買い |
| ブレイク | 後続のスイングトレーダー参戦 | トレンド再開 |

このため、**「右肩の速度 > 左肩の速度」「シグナル足の実体強い」** が鍵。
逆に右肩が左肩よりダラダラ戻る形は単なる「死に体反発」(dead cat bounce) で、再下落する。

### 1.3 既存ロジックの数値的洗練

実用化に当たって、以下の数値化が必要:

- **左右の本数比**: 回復本数 / 下落本数 ≤ 1.0 (理想は 0.5〜0.8、急進回復ほど良い)
- **左右の速度比**: 右肩 ATR/本 / 左肩 ATR/本 ≥ 1.2 (右肩が左肩より急角度)
- **回復余白**: 終値 ≥ pivot high + 0.05 ATR (フェイクアウト防止)
- **シグナル足終値位置**: (close - low) / (high - low) ≥ 0.60
- **谷からの上昇率**: (close - V低) / ATR ≥ 2.5（実質 RR 2 が取れる距離）

---

## 2. 機能しやすい相場環境 / 機能しにくい相場環境

### 2.1 期待値プラスの環境

| 環境 | 数値判定例 | 期待値貢献 |
|---|---|---|
| **D1 強気トレンド中の押し目** | D1 EMA50 > D1 EMA200, close > EMA50, ADX(14) > 20 | +++ |
| **D1 レンジ下限反発** | D1 Donchian20 幅 < 5×D1 ATR かつ V 低が下限から 1×D1 ATR 以内 | ++ |
| **節目近接** | V 低が D1/W1 スイング安値, ラウンドナンバー, FIBO 0.618-0.786 から 1 ATR 以内 | ++ |
| **ボラ拡大期** | ATR(14) / ATR(14)[20] ≥ 1.2 | + |
| **NY/London セッション** | hour in 7-15 UTC (London) or 13-21 UTC (NY) | + |

### 2.2 期待値マイナスの環境

| 環境 | 数値判定例 | 影響 |
|---|---|---|
| **D1 強い下降トレンド** | D1 EMA50 < D1 EMA200, close < EMA50, ADX(14) > 25 | ーー (デッドキャット率高) |
| **超低ボラ収縮** | ATR(14) / ATR(14)[60] < 0.7 | ー (ダマシ多発) |
| **大型イベント直前** | NFP/CPI 直前 6h, FOMC 当日 | ーーー (予測不能) |
| **直近高値に距離ない** | (前 H1 swing high − Entry) / ATR < 1.0 | ー (TP 到達前にレジ) |
| **年末/年始流動性枯渇** | 12/15〜1/10 | ーー (歪み) |
| **アジアセッション単独** | hour in 22-6 UTC のみ | ー (薄い) |

---

## 3. 応用手法 7 候補

### Variant A — D1 トレンド整合プルバック V 【★最有望】

> HTF（D1）上昇トレンドの **押し目** で V 字回復が出るパターン。「大衆の振い落とし →
> トレンド再開」の典型例。最も期待値が安定する。

**追加条件:**
- D1 EMA50 の傾き > 0（直近 10 D1 バーで EMA50 > EMA50[10]）
- D1 close > D1 EMA50
- 任意: D1 ADX(14) > 18（弱いトレンド除外）
- V 低 が D1 EMA50 から ±1.0 × D1 ATR(14) 以内 **か** 直近 D1 スイング安値の上 0.5 × D1 ATR 以内
- **除外**: D1 RSI(14) < 35（D1 過売り継続局面）

**期待勝率**: 55-62% / **PF**: 1.6-2.2 / **頻度**: 6〜15回/年/通貨

---

### Variant B — レンジ下限反発 V

> D1 がレンジで、V がレンジ下限にタッチして反発するケース。平均回帰戦略。

**追加条件:**
- D1 Donchian20 幅 ≤ 5 × D1 ATR(14) （レンジ判定）
- V 低が D1 Donchian20 低値の ±1.0 × D1 ATR 以内
- D1 BBwidth(20, 2) 縮小中（標準偏差が直近 20D 平均以下）
- **除外**: ADX(14) > 25（既にブレイク中）

**期待勝率**: 50-58% / **PF**: 1.4-1.8 / **頻度**: 10〜20回/年

---

### Variant C — 節目 + ボラ拡大コンフルエンス V

> 価格節目（前回安値、フィボ、ラウンドナンバー）+ ボラ拡大 で機関参加を確認する形。

**追加条件:**
- V 低が以下のいずれかから 1 × ATR(14) 以内:
  - 直近 60H4 バーの最安値
  - 直近 W1 スイング安値
  - 0.5 / 1.0 単位のラウンドナンバー（JPY ペアは 0.5 円, ドルストレートは 50pip）
  - 直近 H4 高値→低値の Fib 0.618/0.786 retrace
- ATR(14) / ATR(14)[20] ≥ 1.2
- シグナル足レンジ ≥ 1.5 × ATR(14)
- **除外**: 上記節目から離れすぎている場合

**期待勝率**: 58-65% / **PF**: 1.7-2.3 / **頻度**: 4〜10回/年（厳選）

---

### Variant D — 失敗 V 逆張りショート

> V 字回復シグナルが出たあと、**右肩の上抜けに失敗** したら、踏み上げ後の踏み戻し
> ショートを狙う逆張り。"大衆の希望売り" のフロー。

**ロジック:**
1. Variant A〜G のいずれかの V シグナル発火
2. シグナル足から N=5〜10 H4 バー以内に以下が起きる:
   - close が V 低 − 0.10 ATR を下抜け（明確失敗）
   - **または** signal high を上抜けせずに N バー経過（沈黙失敗）
3. 確認できた瞬間にショートエントリ
4. SL = signal high + 0.25 ATR
5. TP = 1.5R（カウンタートレンドなので小さめ）

**期待勝率**: 48-55% / **PF**: 1.5-1.9 / **頻度**: V シグナルの 30-40% が失敗

---

### Variant E — 二段底 V (Multi-leg V)

> 1 回目の V が失敗したあと、**より高い谷** で 2 回目の V が出るパターン。
> "本物の底" の典型形。

**追加条件:**
- 直近 30 H4 バーで「V シグナル発火 → SL ヒット」が 1 回起きている
- 2 回目の V 谷 > 1 回目の V 谷（higher low）
- 2 回目の V がベース条件をすべて満たす
- HTF 環境変化なし（D1 トレンド維持）

**期待勝率**: 60-68% / **PF**: 2.0-2.6 / **頻度**: 2〜6回/年（稀少）

---

### Variant F — セッション特化 V

> ロンドン / NY オープン後の最初の V のみ採用。流動性が厚い時間帯限定。

**追加条件:**
- シグナル足の hour（UTC） ∈ {7, 8, 9, 13, 14, 15}（London Open + NY Open）
- 同じ日に既に V シグナルが出ていない（1 日 1 シグナル）

**期待勝率**: 52-58% / **PF**: 1.5-1.9 / **頻度**: ベースの 40-50%

---

### Variant G — 右肩優位 V (純度フィルタ強化版)

> ベースロジックをそのまま使うが、純度フィルタを最大化し、HTF を問わず採用。

**追加条件:**
- 右肩速度 / 左肩速度 ≥ 1.5（既存 1.2 から強化）
- 回復本数 / 下落本数 ≤ 0.7
- シグナル足実体比率 ≥ 0.70
- 終値位置 ≥ 0.75
- ATR(14) > ATR(14)[60] × 1.0

**期待勝率**: 50-56% / **PF**: 1.4-1.7 / **頻度**: ベースの 50%

---

## 4. 除外条件マスター

すべての Variant に共通で適用すべき除外条件。

| # | 条件 | 数値判定 | 理由 |
|---|---|---|---|
| E1 | ATR が極端に低い | ATR(14) / ATR(14)[120] < 0.6 | 動かない相場でダマシ多発 |
| E2 | 直近 D1 大陰線連発 | 過去 5 D1 バーで陰線が 4 本以上 | 強い下落圧力継続中 |
| E3 | 既存下降トレンドが過熱 | D1 RSI(14) < 30 かつ ADX > 25 | デッドキャット率高 |
| E4 | 直近高値まで距離不足 | (直近 60H4 swing high − Entry) < 1.5R | TP 到達前に頭打ち |
| E5 | 年末年始 | 12/15〜1/10 (UTC) | 流動性歪み |
| E6 | イベント前 | NFP/CPI/FOMC 前 6 H4 バー | 予測不可能 |
| E7 | アジア単独 | hour ∈ {22, 23, 0, 1, 2, 3, 4, 5} のみ | 流動性薄い（任意） |
| E8 | V 谷が直前 V 谷より低い | 一段下げの初動 | 下降継続中 |
| E9 | 急落前にすでに大幅下落 | 急落前 20H4 で −5 ATR 以上 | 反発力が枯れている |
| E10 | スプレッド・ギャップ | 当日 open vs 前日 close ギャップ > 1 ATR | ニュースギャップ |

> E6 (イベント前) は TradingView 単体では実装困難。経済カレンダー連携が必要なので
> 検証では「水曜深夜 + 木曜全日」を粗い代理変数として除外する手も。

---

## 5. 検証マトリクス（網羅すべき切り口）

### 5.1 通貨ペア

| ペア | TF | 想定特性 |
|---|---|---|
| XAUUSD | H4 | ボラ大、急落多い→ V 多発、ダマシも多い |
| USDJPY | H4 | 中庸、最も再現性高い |
| EURJPY | H4 | USDJPY 相関、独自性低い |
| GBPJPY | H4 | 高ボラ、V 形状崩れやすい |
| CHFJPY | H4 | リスクオフで急落、V 後の戻りが弱いことがある |
| EURUSD | H4 | 低ボラ、Variant C 向き |
| AUDJPY | H4 | リスクオン依存、V 機能しにくい |

### 5.2 時間足

| TF | 用途 |
|---|---|
| H1 | 比較。V 検出多すぎてダマシ増。`maxDropBars` を 30 → 60 程度に |
| H4 | **本命** |
| H8 / 12H | 通貨ペアによってはノイズ減で奇麗 |
| D1 | 検出頻度低すぎ。むしろフィルタ側に使う |

### 5.3 パラメータ感度

| パラメータ | 検証グリッド |
|---|---|
| `minDropAtr` | 2.5 / 3.0 / 3.5 / 4.0 / 5.0 |
| `rightVsLeftSpeed` | 1.0 / 1.2 / 1.5 / 2.0 |
| `recoveryBarsMaxRatio` | 0.6 / 0.8 / 1.0 |
| `bodyRatioMin` | 0.5 / 0.6 / 0.7 |
| `closeLocationMin` | 0.5 / 0.6 / 0.75 |
| `crossBufferAtr` | 0.0 / 0.05 / 0.10 / 0.15 |

### 5.4 Entry / SL / TP の網羅

| 項目 | 候補 |
|---|---|
| Entry タイミング | シグナル足終値 / 次足始値 |
| SL | V 谷 − 0.10 / 0.25 / 0.50 ATR |
| TP | 1.5R / 2R / 2.5R / 3R |
| 部分利確 | 1R で 50% 決済 + 残り 2.5R / 3R 利伸ばし |
| トレーリング | breakeven 移動 (1R 到達後) / ATR トレール |

### 5.5 出力すべき統計

1. 勝率 (Win Rate)
2. プロフィットファクター (PF)
3. 平均 R (Expected R per trade)
4. 最大 DD (R 基準 / % 基準)
5. トレード数（年あたり / 通貨ペアあたり）
6. 連敗数（最大連敗、95%信頼区間）
7. 通貨ペア別成績
8. 時間足別成績
9. Entry: close vs next open 比較
10. TP: 1.5R / 2R / 2.5R / 3R 比較
11. SL: -0.10 / -0.25 / -0.50 ATR 比較
12. 月別 / 曜日別 / 時間帯別成績
13. MFE / MAE 分布
14. 保有時間分布

---

## 6. 最有望案: Variant A "D1 トレンド整合プルバック V" 完全仕様

### 6.1 概要

D1 上昇トレンドの押し目で形成される H4 急落 V 字回復のみを採用。

**狙う局面:**
- 強い上昇トレンドの中で、ニュース/ロスカで一時的に急落
- 大衆が「トレンド終了か？」と疑い始めた瞬間
- 機関がトレンド再開を見越して買い戻し始めるポイント

### 6.2 入力パラメータ (Pine 化想定)

| グループ | 入力名 | 既定値 | 説明 |
|---|---|---|---|
| 基本 | `pivotLen` | 3 | Pivot 検出の左右本数 |
| 基本 | `atrLen` | 14 | ATR 期間 |
| V 検出 | `minDropAtr` | 3.5 | 急落幅最小 (ATR 倍) |
| V 検出 | `minDropBars` | 2 | 急落最小本数 |
| V 検出 | `maxDropBars` | 30 | 急落最大本数 |
| V 検出 | `maxRecoveryRatio` | 1.0 | 回復/下落 本数比 上限 |
| V 検出 | `minSpeedRatio` | 1.20 | 右肩速度/左肩速度 |
| V 検出 | `crossBufferAtr` | 0.05 | 終値 reclaim 余白 (ATR) |
| 品質 | `minBodyRatio` | 0.60 | シグナル足実体比率 |
| 品質 | `minCloseLocation` | 0.60 | シグナル足終値位置 |
| HTF | `useTrendFilter` | true | D1 トレンド整合必須 |
| HTF | `htfTF` | "D" | 上位足 |
| HTF | `htfEmaFast` | 50 | D1 EMA Fast |
| HTF | `htfEmaSlow` | 200 | D1 EMA Slow |
| HTF | `htfEmaSlopeBars` | 10 | EMA 傾き判定本数 |
| HTF | `htfRsiAvoid` | 35 | D1 RSI 下限 (これ未満は見送り) |
| HTF | `vNearEmaAtr` | 1.0 | V 低が D1 EMA50 から何 ATR 以内か |
| 除外 | `lowVolMin` | 0.6 | ATR(14)/ATR(120) この値未満で除外 |
| 除外 | `skipHoliday` | true | 12/15〜1/10 除外 |
| 除外 | `nearHighMinR` | 1.5 | 直近高値までの距離が何 R 以下なら除外 |
| 除外 | `nearHighLookback` | 60 | 直近高値判定 H4 バー数 |
| リスク | `stopBufferAtr` | 0.25 | SL = V 低 − この値 × ATR |
| リスク | `tpR` | 2.0 | TP = Entry + R × この値 |
| リスク | `maxHoldBars` | 180 | 最大保有 H4 バー |
| 実行 | `entryMode` | "next_open" | "signal_close" / "next_open" |

### 6.3 検出ロジック（疑似コード）

```
on each H4 close:
    update pivot stream (alternating high/low)
    new_pivot = pivot just confirmed

    if new_pivot is pivot_low:
        ph = last pivot_high before this pivot_low
        if ph is None: skip
        drop_bars = bars(ph -> this pivot_low)
        drop = ph.price - this.price
        if drop < minDropAtr * ATR: skip
        if drop_bars < minDropBars or drop_bars > maxDropBars: skip
        # store as candidate V
        active_V = { ph, pl: this, drop, drop_bars, expire_bar: bar_index + maxDropBars * 3 }

    if active_V exists and not yet triggered:
        if low < active_V.pl.price - lowBreakInvalidAtr * ATR:
            # V invalidated (lower low)
            drop active_V; continue
        if bar_index > active_V.expire_bar: drop; continue

        recovery_bars = bars(active_V.pl -> current)
        if recovery_bars > active_V.drop_bars * maxRecoveryRatio: drop; continue

        # check reclaim
        if close >= active_V.ph.price + crossBufferAtr * ATR:
            # speed ratio
            left_speed  = active_V.drop / active_V.drop_bars / ATR
            right_speed = (close - active_V.pl.price) / recovery_bars / ATR
            if right_speed < left_speed * minSpeedRatio: drop; continue

            # signal bar quality
            body  = abs(close - open)
            range = high - low
            body_ratio = body / range
            close_loc  = (close - low) / range
            if body_ratio < minBodyRatio: drop; continue
            if close_loc < minCloseLocation: drop; continue

            # HTF filter (request.security with lookahead_off, [1])
            if useTrendFilter:
                d_ema_fast  = D1 EMA(htfEmaFast)
                d_ema_slow  = D1 EMA(htfEmaSlow)
                d_ema_slope = d_ema_fast - d_ema_fast[htfEmaSlopeBars]
                d_rsi       = D1 RSI(14)
                d_close     = D1 close
                if not (d_close > d_ema_fast): drop; continue
                if not (d_ema_fast > d_ema_slow): drop; continue
                if not (d_ema_slope > 0): drop; continue
                if d_rsi < htfRsiAvoid: drop; continue
                d_atr = D1 ATR(14)
                if abs(active_V.pl.price - d_ema_fast) > vNearEmaAtr * d_atr: drop; continue

            # exclusion
            if ATR / ATR[120] < lowVolMin: drop; continue
            if holiday: drop; continue
            recent_high = highest(high, nearHighLookback)
            risk = (close - (active_V.pl.price - stopBufferAtr * ATR))  # for next-open use open[1]; here approximate
            if (recent_high - close) / risk < nearHighMinR: drop; continue

            # === SIGNAL ===
            entry = entryMode == "signal_close" ? close : open[-1]  # next open
            sl = active_V.pl.price - stopBufferAtr * ATR
            tp = entry + (entry - sl) * tpR
            strategy.entry("V", strategy.long)
            strategy.exit("X", "V", stop=sl, limit=tp)
            drop active_V
```

### 6.4 重要な実装注意

| 項目 | 対応 |
|---|---|
| `request.security` の lookahead | `lookahead=barmerge.lookahead_off` を**必ず明示**。さらに当日 D1 値を当日中に参照しないよう `[1]` シフトする |
| Pivot 確定遅延 | `pivotLen=3` なら 3 H4 バー遅延（12時間）。シグナル発火は遅れる前提 |
| 翌足始値エントリ | TradingView の `strategy.entry` は次足始値約定が標準（`process_orders_on_close=false`） |
| 同足 SL/TP 衝突 | デフォルト SL 優先。本仕様では TP 距離 > SL 距離なので問題小 |
| `calc_on_order_fills` | **false** にする（Python との parity 優先） |
| 描画ラベル数 | `var label[]` で間引き管理、上限 80 程度 |
| 休場除外 | `month/dayofmonth` で UTC ベース判定 |
| 最大保有 | `strategy.close` で `bar_index >= entry_bar + maxHoldBars` 判定 |

### 6.5 期待される統計プロファイル

> 過去ノートの V 字 + フィルタ系の実績を踏まえた **目論見値**。実測は要検証。

| 項目 | 期待値 | 許容下限 |
|---|---|---|
| 勝率 | 55-62% | 50% |
| PF | 1.6-2.2 | 1.3 |
| 平均 R | +0.4〜+0.7 | +0.2 |
| 最大 DD | 6-10 R | < 15 R |
| 年間トレード数 | 8-15 / 通貨 | > 5 |
| 最大連敗 | 4-6 | < 9 |
| 推奨通貨数 | 5-6 同時 | 同時運用で DD 平準化 |

### 6.6 OOS / 健全性チェック

- **学習期間**: 2015-2022 (8 年)
- **OOS**: 2023-2025 (3 年)
- 学習で PF ≥ 1.5、OOS で PF ≥ 1.2 を維持できればロバスト
- 学習 PF / OOS PF の比が 0.7 を下回ったら過剰最適化疑い

---

## 7. 期待される統計プロファイル比較表

| Variant | 勝率 | PF | 頻度/年/通貨 | コメント |
|---|---|---|---|---|
| **A: D1 整合プルバック** | **55-62%** | **1.6-2.2** | **8-15** | ★最有望 / 安定 |
| B: レンジ下限反発 | 50-58% | 1.4-1.8 | 10-20 | 中庸 / 多発 |
| C: 節目 + ボラ拡大 | 58-65% | 1.7-2.3 | 4-10 | 高勝率 / 低頻度 |
| D: 失敗 V ショート | 48-55% | 1.5-1.9 | A の 30-40% | 逆張り上級者向け |
| E: 二段底 V | 60-68% | 2.0-2.6 | 2-6 | 稀少 / ハイクオリティ |
| F: セッション特化 V | 52-58% | 1.5-1.9 | A の 40-50% | 安定だが頻度減 |
| G: 右肩優位純度版 | 50-56% | 1.4-1.7 | A の 50% | フィルタ強化 |

**ポートフォリオ最適化案:**
- **コア (70%)**: Variant A を 6 通貨で運用
- **サテライト (20%)**: Variant C を XAUUSD / USDJPY 限定で
- **逆張り (10%)**: Variant D を Variant A の失敗を狙う形で

---

## 8. 実装ロードマップ

### Phase 1: ベース検証（最優先）

1. Variant A を Pine v5 ストラテジで実装
2. H4 / 6 通貨で 10 年バックテスト
3. 学習 (2015-2022) × OOS (2023-2025) で PF を比較
4. パラメータ感度（Section 5.3 のグリッド）

### Phase 2: 感度・除外条件詰め

5. 除外条件 E1〜E10 を 1 つずつ ON/OFF し、寄与度を測定
6. Entry mode (signal_close vs next_open) 比較
7. TP/SL 感度比較

### Phase 3: 応用 Variant 拡張

8. Variant C (節目+ボラ拡大) 実装
9. Variant D (失敗 V ショート) 実装
10. ポートフォリオ統合バックテスト

### Phase 4: 本番化

11. アラート設定
12. 実弾運用（低リスク 0.25R から）30 トレード後に通常リスク

---

## 9. 参考: V 字検出の Python ↔ Pine 整合チェックリスト

> 既存 `clean_h4_v_reclaim_strategy.pine` の TradingView 警告
> 「先読みバイアスを利用している可能性があります」対策。

| チェック | 実装方法 |
|---|---|
| `strategy(..., calc_on_order_fills=false)` | デフォルト false に戻す |
| `process_orders_on_close=false` | デフォルト |
| `request.security` で `lookahead=barmerge.lookahead_off` を明示 | `lookahead=barmerge.lookahead_off` |
| HTF 値を当日中に参照しない | `request.security(..., expr[1])` 形で確定足のみ参照 |
| Pivot は `ta.pivotlow(low, left, right)` の `right` 確定後にのみ参照 | デフォルト動作 |
| Entry は **シグナル足の終値確定 → 次足始値約定** | デフォルト動作 |
| `barstate.isconfirmed` を使った発火条件 | シグナル発火条件に `and barstate.isconfirmed` |
| 同足 SL/TP 衝突は TradingView の "Recalculate after order is filled" を OFF | `calc_on_order_fills=false` で達成 |

これらをすべて満たすことで「先読みバイアス警告」は消える。
