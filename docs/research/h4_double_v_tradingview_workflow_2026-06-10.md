# H4 Double V — TradingView データ起点ワークフロー

作成日: 2026-06-10

## 方針

**TradingView の OHLC と Strategy Tester を正** とする。  
ローカル `F87104_test` CSV や Python リサンプル結果は、TV 照合が終わるまで採用しない。

Market Psychology Squeeze で使ったのと同じ流れ:

1. TV から H4 OHLC をエクスポート
2. TV Strategy Tester で Pine を回す
3. Python は **同じ CSV** で件数・日付・方向を照合

---

## Phase 0 — データ準備（いまここ）

### 1. TradingView でエクスポート

| 項目 | 設定 |
|------|------|
| ブローカー | **OANDA**（本番 Pine と同じ） |
| 時間足 | **H4（240分）** |
| 通貨 | GBPJPY, USDJPY, EURJPY, CHFJPY, AUDJPY（+ XAUUSD は D1 V 研究用に任意） |
| 期間 | できるだけ長く（2015〜現在。Pine の `2015〜2026` フィルタと合わせる） |
| 列 | `time,open,high,low,close`（unix 秒） |

手順: チャート → 右上 `···` → **Export chart data…** → CSV

ファイル名例: `OANDA_GBPJPY, 240_a1b2c.csv`

### 2. リポジトリへ配置

```bash
mkdir -p data/raw/tv_oanda/h4
cp "~/Downloads/OANDA_GBPJPY, 240_xxxx.csv" data/raw/tv_oanda/h4/GBPJPY_H4.csv
```

GitHub Web アップロードでも可（root 置きでもスクリプトが glob 検索）。

### 3. カバレッジ確認

```bash
python3 backtests/h4_double_v/run_tv_data_coverage_check.py
```

出力: `backtests/h4_double_v/results_tv_data_coverage/`

- `median_minutes` が **240** 前後であること
- `bars_2015_2026` が十分あること（H4 で 1万本超が目安）

---

## Phase 1 — Strategy Tester（TV 本体）

### 優先 Pine

| 順 | Pine | チャート |
|----|------|----------|
| 1 | [d1_v_context_h4_strategy.pine](../../pine/production/d1_v_context_h4_strategy.pine) | **H4** |
| 2 | [h4_double_v_reclaim_strategy.pine](../../pine/production/h4_double_v_reclaim_strategy.pine) | **H4** |

### 入力はデフォルトのまま最初は触らない

- D1 V Context: `押し目高値突破+EMA20上向き`, RR 1.5, SL=H4押し目安値
- Double V: 探索モードではなく Strategy デフォルト

### メモする項目

| 通貨 | trades | PF | Net | Max DD | 備考 |
|------|-------:|---:|----:|-------:|------|
| GBPJPY | | | | | |
| USDJPY | | | | | |
| … | | | | | |

### トレードリスト CSV も保存

Strategy Tester → **List of trades** → Export  
→ `data/raw/tv_oanda/trades/d1_v_context_GBPJPY_trades.csv` など

---

## Phase 2 — Python 照合（これから実装）

TV CSV + トレードリストが揃ったら:

```bash
# 予定
python3 backtests/h4_double_v/run_d1_v_context_tv_parity_check.py \
  --csv data/raw/tv_oanda/h4/GBPJPY_H4.csv \
  --tv-trades data/raw/tv_oanda/trades/d1_v_context_GBPJPY_trades.csv
```

目標:

- **エントリー日時 15/15 一致**（Market Psychology XAGUSD 照合と同レベル）
- 不一致は Pine の約定モデル（次足始値）か D1 pivot 差を切り分け

---

## Phase 3 — 目視（並行可）

可視化 Pine（エントリーなし）:

| Pine | チャート |
|------|----------|
| [d1_v_context_daily_visual.pine](../../pine/visual/d1_v_context_daily_visual.pine) | D1 |
| [d1_v_context_h4_visual.pine](../../pine/visual/d1_v_context_h4_visual.pine) | H4 |
| [h4_double_v_short_denial_visual.pine](../../pine/visual/h4_double_v_short_denial_visual.pine) | H4 |

SIGNAL / EXEC が「売り手の損切り連鎖」に見えるか、勝ち負け各5件をメモ。

---

## 注意

| 項目 | 内容 |
|------|------|
| タイムゾーン | Python は `Asia/Tokyo` に変換（Squeeze 照合と同じ） |
| H1 CSV との混同 | `60_` = H1、`240_` = H4。Double V 研究は **H4 のみ** |
| XAUUSD | Double V Strategy は初期設定で除外可。D1 V Context は別途検証 |
| 損益の単位 | 照合第一段階は **件数と日時**。損益は TV 基準を正とする |

---

## 関連

- 研究メモ: [h4_double_v_reclaim_2026-06-02.md](h4_double_v_reclaim_2026-06-02.md)
- Squeeze TV 照合の先例: [market_psychology_tv_ohlc_check/report_ja.md](../../backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_ohlc_check/report_ja.md)
