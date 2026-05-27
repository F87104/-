# Google スプレッドシート用 検証結果一覧

> [`docs/BACKTEST_INDEX.md`](../BACKTEST_INDEX.md) の内容を、Google スプレッドシートで開きやすい CSV / TSV にまとめたもの。

---

## 📂 ファイル一覧

| ファイル | 内容 | 行数 |
|---|---|---:|
| **01_overall_judgment.csv** | 採用判定マトリクス (14手法を✅/⚠️/❌で一目で判定) | 16 |
| **02_method_catalog.csv** | 全検証ディレクトリ一覧 (パス + 概要 + 結論) | 43 |
| **03_by_symbol.csv** | 通貨別成績マトリクス (TB単独/T5実戦/両方フル) | 7 |
| **04_by_year.csv** | 年別成績 (TrendBreakV1 baseline) | 10 |
| **05_is_oos.csv** | IS / OOS 期間比較 | 9 |
| **06_anti_patterns.csv** | アンチパターン (やったけどダメだった10件) | 10 |
| **07_tf_compare.csv** | 時間軸比較 (H1/H4/D1 V字回復系) | 6 |
| **08_research_sub.csv** | 補助研究 (Pyramiding/Fakeout/Cost) | 10 |
| **99_glossary.csv** | 用語集 (R/PF/WR/Calmar など) | 20 |
| **ALL_SHEETS.tsv** | 全シートを1つにまとめた TSV (コピペ用) | - |

---

## 🚀 Google スプレッドシートへの取り込み方

### 方法 A: 各 CSV を別シートとしてインポート (推奨)

1. https://sheets.new で空のスプレッドシートを開く
2. **「ファイル」 → 「インポート」 → 「アップロード」**
3. `01_overall_judgment.csv` を選択
4. インポート位置: **「新しいシートとして挿入」** を選択
5. シート名を変更 (例: `判定一覧`)
6. 同じ手順で他のCSVもインポート

**メリット**: シート分けがキレイ。タブで切り替え可能。

### 方法 B: ALL_SHEETS.tsv をコピペ (簡易)

1. `ALL_SHEETS.tsv` をテキストエディタで開く
2. `=== 01_overall_judgment ===` の次の行から空行までを選択コピー
3. Google スプレッドシートで該当シートに貼り付け (Cmd+V / Ctrl+V)
4. TSV (タブ区切り) は自動的に列に分かれる
5. 各シートを繰り返し

**メリット**: 1ファイルで管理。ファイル送信が楽。

### 方法 C: GitHub のCSV URL を直接インポート

`IMPORTDATA` 関数で GitHub の raw URL を参照:

```
=IMPORTDATA("https://raw.githubusercontent.com/F87104/sai/main/docs/spreadsheet/01_overall_judgment.csv")
```

**メリット**: 元ファイル更新と同期。
**デメリット**: 1セルに1関数しか書けないので、シートごとにセットアップ必要。

---

## 📊 推奨スプレッドシート構成

```
[Sheet 1] 判定一覧 (01_overall_judgment)   ← まずココを見る
[Sheet 2] 検証カタログ (02_method_catalog)
[Sheet 3] 通貨別 (03_by_symbol)
[Sheet 4] 年別 (04_by_year)
[Sheet 5] IS_OOS (05_is_oos)
[Sheet 6] アンチパターン (06_anti_patterns)
[Sheet 7] TF比較 (07_tf_compare)
[Sheet 8] 補助研究 (08_research_sub)
[Sheet 9] 用語集 (99_glossary)
```

---

## 🔄 更新方法

新しい検証結果が出たら:

1. `docs/BACKTEST_INDEX.md` を更新
2. `docs/spreadsheet/build_spreadsheet_csvs.py` の該当データを更新
3. `python3 docs/spreadsheet/build_spreadsheet_csvs.py` を実行
4. CSV/TSV が再生成される
5. Google スプレッドシートに再インポート

---

## 📎 関連リンク

- [`../BACKTEST_INDEX.md`](../BACKTEST_INDEX.md) — markdown 版 (こちらが本体)
- [`../../README.md`](../../README.md) — リポジトリ入口
- [`../../STRATEGY_GUIDE.md`](../../STRATEGY_GUIDE.md) — 戦略運用説明書
