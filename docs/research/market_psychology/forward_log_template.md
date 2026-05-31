# 市場心理 v2 フォワード記録 — テンプレート

> このファイルは **テンプレート** です。
> 実運用では、このファイルをコピーして
> `docs/research/market_psychology/forward_log_2026_06.md` のように **月ごと** にファイルを分けてください。

**目的**: v2 仕様の Pine が TradingView 上で出すシグナルを 1 件ずつ記録し、
30 件貯まった時点で **本番昇格判断 (🟡 → 🟢)** をするための一次データを取る。

---

## 1. 記録対象

| 構造 | Pine ファイル | 表示名 | 採用通貨 |
|---|---|---|---|
| Squeeze v2 | `pine/research/market_psychology_strict_v2_strategy.pine` | 本命v2 ... (`useSqz=true`) | XAUUSD / EURJPY / AUDJPY / USDJPY / SILVER / CHFJPY |
| Capitulation v2 | 同上 | 本命v2 ... (`useCap=true`) | XAUUSD / CHFJPY / AUDJPY / USDJPY / EURJPY |
| Long Liquidation | `pine/research/market_psychology_long_liquidation_strategy.pine` | 本命v2 Long Liquidation | ALL ex GBPJPY |
| Dormant Breakout | `pine/research/market_psychology_dormant_breakout_strategy.pine` | 本命v2 Dormant Breakout | ALL ex GBPJPY |

GBPJPY と (Capitulation の場合) SILVER は除外。

---

## 2. 30 件達成判定基準

各構造が独立して以下を満たした時に **🟢 本線採用** を検討:

- [ ] フォワード ≥ 30 件
- [ ] フォワード PF ≥ 1.7
- [ ] フォワード DD ≤ Total R の 1/3
- [ ] フォワード期間に **3 ヶ月以上の OOS** を含む
- [ ] Python ↔ Pine parity が確認済み (シグナル時刻が一致する)

達成しなければ **🟡 フォワード継続** のまま、件数を貯め続ける。

---

## 3. 記録フォーマット (1 シグナルにつき 1 行)

| # | 日時 (UTC) | 通貨 | TF | 構造 | バリアント | Setup R | SL 価格 | TP 価格 | Entry 価格 | 結果 | 終了 R | MFE R | MAE R | 経過バー | 終了理由 | メモ |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| 1 | 2026-06-01 04:00 | XAUUSD | H4 | SQZ | v2 default | 1.5R | 2455.2 | 2462.4 | 2458.0 | WIN | +2.0R | 2.34 | 0.42 | 18 | TP | SILVER と同時シグナル無し |
| 2 | ... |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

### 列の意味

- **構造**: SQZ / CAP / LL (Long Liquidation) / DB (Dormant Breakout)
- **バリアント**: v2 default / + hour_filter / + volume / + early_exit など、適用したオプション
- **Setup R**: エントリー時点の SL 距離 (= 1R 単位の絶対値)
- **結果**: WIN / LOSS / TIMEOUT / EARLY_EXIT / MANUAL
- **終了 R**: コスト込み (spread + slippage 想定値で控除)
- **MFE R**: ポジション中の含み益最大 R
- **MAE R**: ポジション中の含み損最大 R
- **終了理由**: TP / SL / TIMEOUT / EARLY_EXIT_MFE / MANUAL

---

## 4. 月次集計テンプレート

毎月末に以下を埋める:

### 4-1. 構造別集計 (今月分)

| 構造 | 件数 | WR | total R | PF | DD | 最大連敗 |
|---|---:|---:|---:|---:|---:|---:|
| SQZ v2 | 0 | — | 0 | — | 0 | 0 |
| CAP v2 | 0 | — | 0 | — | 0 | 0 |
| LL | 0 | — | 0 | — | 0 | 0 |
| DB | 0 | — | 0 | — | 0 | 0 |
| **合計** | 0 | — | 0 | — | 0 | 0 |

### 4-2. 構造別累計 (フォワード開始から)

| 構造 | 累計件数 | 累計 PF | 累計 DD | 30件達成? | 採用判定 |
|---|---:|---:|---:|---|---|
| SQZ v2 | 0 / 30 | — | — | ❌ | 🟡 フォワード中 |
| CAP v2 | 0 / 30 | — | — | ❌ | 🟡 フォワード中 |
| LL | 0 / 30 | — | — | ❌ | 🟡 フォワード中 |
| DB | 0 / 30 | — | — | ❌ | 🟡 フォワード中 |

### 4-3. 通貨別 (累計)

| 通貨 | SQZ | CAP | LL | DB | 合計 R |
|---|---:|---:|---:|---:|---:|
| XAUUSD | 0 / 0R | 0 / 0R | 0 / 0R | 0 / 0R | 0R |
| ... |  |  |  |  |  |

---

## 5. フォワード中に観察するべきこと

シグナルが出るたびに以下を確認してメモする (上の表「メモ」列):

### Squeeze 観察ポイント

- [ ] 棚は本当に圧縮していたか? (主観で 1-5 点)
- [ ] 急落の前提 (3.5 ATR 以上の下落) は **構造的に直近の高値からの落ち** だったか
- [ ] エントリ後 4 バーで 0.5R 進んだか? (Yes/No)
- [ ] 同時刻に他戦略 (TrendBreakV1 / H4 T5) のシグナルがあったか
- [ ] **TradingView 実 volume**: 直前 20 本平均の何倍だったか

### Capitulation 観察ポイント

- [ ] `signal_range_atr` ≥ 3.0 が成立していたか (主役の足の値幅)
- [ ] 下ヒゲの長さは絵としてキレイだったか
- [ ] D1 EMA50 はちゃんと下降中だったか
- [ ] **TradingView 実 volume**: 急増していたか (1.5-2.0 倍以上が理想)
- [ ] 急落幅 4 ATR 以上は満たしていたか

### Long Liquidation 観察ポイント

- [ ] 急騰 3 ATR の後の高値更新失敗が **明確** だったか
- [ ] 上側棚は **6 本以上密集** していたか (本数の感覚)
- [ ] 棚安値ブレイクは **終値** で確定したか (ヒゲのみのケースをカウントしない)

### Dormant Breakout 観察ポイント

- [ ] 休眠ライン (Donchian-N) は **少なくとも N バー以上** タッチされていなかったか
- [ ] N の選択 (120 / 360 / 1250) でどれが先に出たか
- [ ] ブレイクは **終値ベース** だったか
- [ ] 押し戻りが 5 本以内に収まったか

---

## 6. 注意 (フォワードを汚さないため)

- ❗ **過去のシグナルを後から「これがあった」と追加しない** (look-ahead bias)
- ❗ **同じシグナルを複数バリアントで多重カウントしない** (1 シグナル 1 行)
- ❗ Pine の `barstate.isconfirmed` で確定した足だけを採用
- ❗ Strategy Tester の値ではなく **alertcondition で発火した時刻** を記録
- ❗ Pine と Python のシグナル時刻が **必ず一致** することを並走で確認

---

## 7. 30 件達成後の昇格 / 棄却プロトコル

| 結果 | アクション |
|---|---|
| **PF ≥ 1.7 / DD ≤ 1/3 / OOS あり** | 🟢 本線採用、`status.md` を更新 |
| PF 1.3-1.7 (薄い勝ち) | 🟡 継続フォワード (件数 60-100 までデータ取り) |
| PF < 1.3 または DD 大 | 🔵 アンチパターン化、`status.md` の AP リストへ追加 |

---

## 8. 参照

- v2 仕様: [`v2_spec.md`](./v2_spec.md)
- 研究ハブ: [`README.md`](./README.md)
- ステータス: [`status.md`](./status.md)
- 検証コード: [`backtests/elliott_fibo/run_market_psychology_v2_deep_research.py`](../../../backtests/elliott_fibo/run_market_psychology_v2_deep_research.py)
- 詳細レポート: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md)

---

**運用ルール**: 月初にこのテンプレートをコピーして `forward_log_YYYY_MM.md` を作成 → 月の途中はシグナル発生のたびに 1 行追記 → 月末に集計を埋める。
