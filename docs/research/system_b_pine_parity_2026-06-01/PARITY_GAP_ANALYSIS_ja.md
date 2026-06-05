# B06 VIS — 照合未達の原因と完全一致の方法

作成日: 2026-06-05

## 前提

- **Python 内部は完全一致**（34件・再現監査で entry/stop/target 差 ≈ 0）
- 未達は **TradingView（OANDA）と Python（`load_instrument`）の差** が主因
- USDJPY: Python 13件 / TVテスター 約9件（OK 4 / MISS 9 / EXTRA 3+）

---

## 未達の原因（影響度順）

### 1. OHLC データ源の違い（最大）

| | Python | TradingView |
|---|--------|-------------|
| データ | リポジトリ `load_instrument`（検証用CSV/DB） | OANDA ブローカー足 |
| 影響 | 高安1pip違い → ピボット確定が1本ずれる → Vペア・棚ブレイクが別日になる |

→ **MISS（Pythonのみ）** と **EXTRA（TVのみ）** が同時に起きる典型パターン。

### 2. H4 バーの時刻定義

- Python: `resample_ohlc` の index（UTC相当）
- TV: チャートのタイムゾーン表示（JSTだと +9h 表示）
- セッション境界（日足の切り方）が違うと **同一「4時間足」でも中身が異なる**

### 3. インジケータ微差

PRECALM・棚・リスクはすべて以下に依存:

- ATR(14)
- ADX(14)
- EMA50 傾き（20本）
- 60本レンジ幅

TV の `ta.*` と Python の `kickoff.add_features` で **端数・初期化・NaN処理** が違うと、  
「PRECALM不足」「棚が広い」など **見送りコード** が変わる。

### 4. ピボット確定ロジックの端数

両方とも width=3 の confirmed pivot だが:

- 同値高安の tie-break（H/L 同時）
- `minSwingAtr` 閾値比較の ATR 参照足
- Pine は `ta.pivothigh/low`、Python は window max/min

→ **数日ずれたシグナル**（例: Python 11/12 vs TV 11/07・12/12）

### 5. 設定の取り違え（解消済みだが再確認）

- **TP計算:** Python照合は **Signal基準(36d90e6再現)** 必須
- Entry基準だと TP/RR がずれ、成績比較も不可
- `シグナル表示=ON`、`2015〜2026`、`12/15〜1/10停止`、`4通貨のみ`

### 6. ストラテジーテスター vs Python の「シグナル時刻」

- Python **signal_time** = 棚ブレイク足の close 確定時刻
- TV strategy.entry = 同足で注文 → 約定は次足始値（これは一致設計）
- テスター一覧の「日時」は **約定・TZ表示** で、signal_time と **数時間ずれて見える**（OK扱い: 16, 19, 24, 27）

### 7. コスト・スリッページ

- Pine: `slippage=2` など
- Python: `r_after_cost`

シグナル一致には通常影響しないが、**テスター件数・出口タイミング** に影響しうる。

---

## 完全一致させる方法（現実的な順）

### レベルA — データを同一にする（唯一の「真の100%」）

1. Python 側の H4 OHLC を CSV エクスポート（USDJPY 全期間）
2. TradingView で **カスタムシンボル / インポート** または同一フィードを契約
3. 同じ index で Pine を再照合

**効果:** ピボット・棚・PRECALM が揃えば signal_time 100% に近づく。  
**コスト:** TV での運用データと検証データが二系統になる場合あり。

### レベルB — Python 期待値を TV に重ねる（運用向け・推奨）

1. `python_expected_b06_vis_precalm_all.csv` を読む **参照用インジ** を作る  
   （signal_time に縦線・ラベル「Py #22」）
2. Pine シグナルと **同じバーか** だけ人間 or スクリプトで判定
3. ズレは **DATA** として記録、執行は Python 通知

**効果:** 完全一致しなくても **誤発注を防ぐ**。系統B本番に最適。

### レベルC — Pine を Python に寄せる（開発工数大）

1. **1件ずつデバッグ**（例: 2016-10-03 MISS）  
   - `showSkips=ON` で skipCode を見る  
   - Python の `v_start_time`, `v_low_time`, `shelf_high` を CSV からラベル表示と比較
2. ADX/EMA/ATR を Python と同式・同ソースで再実装（Pine だけでは限界）
3. `pair_key` / `usedPairs` の重複禁止をバイト一致まで追う

**効果:** OANDA のまま **一致率を上げる**（100%保証は難しい）。

### レベルD — 一致の定義を段階化（採用ゲート）

| ゲート | 条件 |
|--------|------|
| G0 | 設定一致（Signal TP・パラメータ固定） |
| G1 | **±0 H4 bar** で signal 一致 ≥ 80%（2019以降） |
| G2 | **±1 H4 bar** まで許容 ≥ 95% |
| G3 | 100%（レベルAのみ期待） |

**現状 USDJPY:** G1 相当で **4/13 ≈ 31%**（厳密一致）。2019以降に絞ると **4/8 = 50%** 程度。

### レベルE — 執行経路を分離（務実的結論）

- **検証・フォワード台帳:** Python のみ
- **Pine:** チャート可視化・アラートの補助
- **B06 `pine_ready`:** `partial` のまま（`yes` はレベルAまたはG2達成後）

---

## すぐできるチェックリスト（再照合時）

- [ ] TP計算 = **Signal基準(36d90e6再現)**
- [ ] 銘柄フィルタ = **4通貨のみ**
- [ ] シンボル = **USDJPY**（チャートとテスター一致）
- [ ] データ範囲 = 2015〜2026
- [ ] テスター日時は **signal ではなく entry** と混同しない
- [ ] 一致判定は **日付（年月日+H4足）** で行う

---

## 関連ファイル

- 期待値: `python_expected_b06_vis_precalm_all.csv`
- ログ: `parity_log_b06_filled.csv`
- 対照表: `tv_strategy_list_vs_python_usdjpy.md`
- 判定: `DECISION_usdjpy_b06_parity.md`
