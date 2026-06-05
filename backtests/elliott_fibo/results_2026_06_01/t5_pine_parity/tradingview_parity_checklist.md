# H4 T5 + MACD + BB — TradingView Pine Parity Checklist

Python を正とする。TradingView の strategy 成績（PF/勝率）は、**signal_time 一致率 100%** になるまで採用判断に使わない。

## Pine ファイル

- `pine/production/h4_t5_macd_bb_live_ready.pine`

## 照合の2フェーズ

| Phase | Python CSV | 件数 (IS/OOS) | Pine 設定 |
|---|---|---:|---|
| **A: BASE** | `python_expected_base_research_99.csv` | 99 / 15 | `騙し回避フィルタ` = **OFF** |
| **B: LIVE** | `python_expected_practical_research_34.csv` | 34 / 5 | `騙し回避フィルタ` = **ON**（デフォルト） |

共通設定（両フェーズ）:

1. チャート時間足: **H4**
2. `判定時間足`: 240
3. `判定時間足チャートでのみ売買する`: **ON**
4. `MACD + BBプリセット`: **Strict 0.75-1.00 + width<=7**
5. `V字速度プリセット`: **Balanced REC1.2**
6. `12/15〜1/10は新規停止`: **ON**
7. `運用判定 (FULL/HALF/SKIP)`: **OFF**（シグナル件数照合時）
8. `固定数量を使う`: **ON** でも可（件数照合のみなら数量は不問）

## 手順（推奨順）

### Step 0: タイムゾーン合わせ

1. Python の `signal_time` は **CSV index そのまま（UTC 相当）**。
2. TradingView 表示が JST 等なら **+9h 等の固定オフセット** を1件で確認してから全件照合する。
3. 最初の確認用: **USDJPY 2015-03-31** `signal_time=2015-03-31 00:00:00`（`expected_usdjpy_first5.csv` 参照）。

### Step 1: 単通貨スモーク（USDJPY）

1. USDJPY H4 に Pine を貼る。
2. Phase A 設定（ guards OFF ）で 2015–2024 を表示。
3. `expected_usdjpy_all.csv` の **16件** すべてで `signal_time` が一致するか目視。
4. 一致したら `signal_close` / `stop` / `target` を ±数 pip 以内で確認。

### Step 2: 全通貨 Phase A（99件）

1. 7通貨それぞれで `by_symbol/*_base.csv` と照合。
2. 結果を `parity_log_filled.csv` に記録（`tv_match` = OK / MISS / OFFSET / DATA）。

### Step 3: Phase B（live 34件）

1. `騙し回避フィルタ` = ON に戻す。
2. `python_expected_practical_research_34.csv` と照合。
3. ここまで一致すれば live ペーパー開始可。

## 一致判定ルール

| 項目 | 許容 |
|---|---|
| `signal_time` | **完全一致**（TZ 補正後） |
| `entry_time` | signal の **次の H4 足**（Python は次足始値） |
| `trigger_type` | stagnation / rebreak / stagnation+rebreak 一致 |
| `stop` | ±0.5 pip または ±0.01% |
| `target` | シグナル終値基準 RR2.0（Python/Pine 同じ定義） |
| 件数 | Phase A=99, Phase B=34（Research） |

## よくある不一致原因

1. **データ提供元差** — TV と F87104_test の H/L/C 差
2. **Pivot 確定タイミング** — pivotWidth=3 の確定本数
3. **年末年始除外** — 12/15–1/10
4. **Guard ON/OFF 取り違え** — 99件 vs 34件
5. **運用判定 ON** — SKIP/HALF で件数が減る
6. **REC プリセット** — REC1.2 以外を選んでいる

## 出力ファイル

| ファイル | 内容 |
|---|---|
| `python_expected_base_research_99.csv` | Phase A IS 99件 |
| `python_expected_base_oos_15.csv` | Phase A OOS 15件 |
| `python_expected_practical_research_34.csv` | Phase B IS 34件 |
| `parity_log_template.csv` | TV 記入用テンプレ |
| `by_symbol/*.csv` | 通貨別 |
| `report_ja.md` | サマリー |

## 採用ゲート

- Phase A: **99/99 signal match**（DATA差除く）
- Phase B: **34/34 signal match**
- その後: 0.25R フォワード 30件
