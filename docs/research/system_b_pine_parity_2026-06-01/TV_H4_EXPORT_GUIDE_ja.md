# TradingView → H4 CSV（OHLC比較用）

## 保存先

```
docs/research/system_b_pine_parity_2026-06-01/tv_usdjpy_h4.csv
```

---

## 右クリックに「エクスポート」が無い理由

スクリーンショットの右クリックメニュー（アラート・注文・設定など）には、**そもそも CSV エクスポートは出ません**。以前の説明「右クリック → エクスポート」は誤りです。

TradingView 公式の入口は次のとおりです。

| 場所 | 操作 |
|------|------|
| **画面上部**（チャート右上・レイアウト名「保存」の近く） | **▼（レイアウト／チャート管理）** → **「チャートデータをダウンロード…」** / *Download chart data…* |
| 旧UIの場合 | 左上 **≡（ハンバーガー）** → **Export chart data** 系 |

公式: [How to export chart data](https://www.tradingview.com/support/solutions/43000537255-how-to-export-chart-data/)

### プラン制限（重要）

**チャートデータの CSV ダウンロードは Plus / Premium 以上** の機能です（無料プランではメニュー自体が無い、またはグレーアウト）。

- 無料のまま → 下の **「無料プランでの代替」** を使う  
- 一時的に比較だけ → TradingView の **トライアル** で 1 回ダウンロードも可  

---

## 有料プランでエクスポートするとき

### チャート設定

| 項目 | 値 |
|------|-----|
| 銘柄 | **USDJPY** |
| データ | **OANDA**（口座不要） |
| 時間足 | **4時間** |
| タイムゾーン | 画面右下の表示（例: **UTC+9**）をメモ |
| 履歴 | 左にスクロールして **2015〜** まで読み込んでからダウンロード |

### 手順

1. 上記チャートを開く  
2. **右上の ▼** → **チャートデータをダウンロード…**  
3. 時刻形式: **UNIXタイムスタンプ** で問題なし（スクリプトが秒/ミリ秒を自動判定）  
4. **ダウンロード**（CSV）→ `tv_usdjpy_h4.csv` にリネームして保存  

ダウンロード前にチャートを **左へスクロール** して 2015 年付近まで履歴を読み込むと、比較本数が増えます。

### 期待する列（スクリプト用）

TradingView の CSV は列が多いことがあります。次があれば足ります。

- 時刻: `time` / `datetime` / `date` のいずれか  
- `open`, `high`, `low`, `close`  

テンプレ: `tv_usdjpy_h4.template.csv`

### 実行

```bash
cd /Users/asamifujita/Documents/Codex/2026-05-31/f87104-git-https-github-com-f87104/github_repo_public_top
python3 scripts/analyze_b06_bar_drift.py
```

出力: `ohlc_diff_per_bar.csv`, `ohlc_diff_summary.csv`, `BAR_DRIFT_REPORT_ja.md` 更新

---

## 無料プランでの代替（TV CSV なし）

OHLC の全履歴比較はできませんが、**B06 パリティの主因切り分け**は既に可能です。

### A. すでに取れているデータ（推奨・追加作業なし）

| データ | 用途 |
|--------|------|
| ストラテジーテスター約定 | `tv_strategy_trades_usdjpy.csv` — 日時・価格のずれ（Type A/B） |
| Python 13 シグナル | `drift_python_signals.csv` / `BAR_DRIFT_REPORT_ja.md` |

→ **シグナル日が違う（Type A）** と **同日付付近で 0.2〜0.8 pip / 2〜4 本（Type B）** はこの時点で説明済み。

### B. 数本だけ手動で足を照合（無料・5分）

パリティ **OK の 4 件**（trade_id 16, 19, 24, 27）について:

1. チャートで該当 **signal 日時** の H4 バーに十字線  
2. 左上の **O H L C** をメモ  
3. Python 側は `drift_python_signals.csv` の `signal_bar_*` と比較  

→ 「価格はほぼ同じ・時刻ラベルだけ違う」か「足自体が違う」かを確認できます。

### C. Plus なしで「OANDA 足」に近い CSV を使う（任意）

TV チャートも OANDA フィードなので、**OANDA 公式ヒストリカル** を `tv_usdjpy_h4.csv` として置き、  
「TV そのもの」ではなく **「OANDA ブローカー足 vs Python(F87104)」** の差分として読む方法があります。

- 完全一致の代用にはなるが、TV ピクセル単位の一致証明にはならない  
- それでも **F87104 と OANDA の pip 差** は定量化できる  

### D. 1 回だけ TV CSV が欲しい

- Plus / Premium の **無料トライアル** で「チャートデータをダウンロード」を 1 回だけ実行  
- 取得後はトライアル終了しても、保存した CSV で `analyze_b06_bar_drift.py` は動く  

---

## タイムゾーン

エクスポート後、スクリプトが **0h / ±9h** でインデックスをずらし、Python H4 と重なる本数が最大の設定を自動採用します。  
チャート右下が **UTC+9**（スクリーンショットと同じ）なら、結果の `tv_index_shift_hours` をメモしてください。

---

## 注意

- 目的は **全履歴100%一致** ではなく **1バーあたりの pip ずれの目安**  
- 無料プランのままでも **テスター約定ベースの drift 分析は完了済み**  
- TV CSV は「ずれの数値化」を一段深くする **オプション**
