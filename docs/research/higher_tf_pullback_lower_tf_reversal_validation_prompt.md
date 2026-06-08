# 検証指示プロンプト: 上位足押し目 ＝ 下位足転換（MTF）

作成日: 2026-06-08  
対象仮説: [higher_tf_pullback_lower_tf_reversal_2026-06-08.md](higher_tf_pullback_lower_tf_reversal_2026-06-08.md)

---

## 使い方

1. 下の **「コピー用プロンプト」** をそのまま AI / 検証担当に渡す
2. 段階1（手動）→ 段階2（集計）→ 段階3（コード化）の順で実行
3. 結果は [validation_results_template.csv](validation_results_template.csv) に追記

---

## コピー用プロンプト（全文）

```
# 役割
あなたは FX リポジトリ（F87104/-）の研究担当です。
仮説「上位足の押し目 = 下位足の転換」を、主観ではなく再現可能な条件で検証してください。

# 仮説（検証対象）
上位足（H4/D1）で「押し目」と見える1 leg の内部に、下位足（H1/M15/M5）では
逆方向の zigzag → 転換（higher low + high ブレイク等）が現れる。
この「転換確認後」に上位足方向へエントリーすると、
「転換なしで押し目に飛び乗る」より MAE が浅く MFE が大きい。

# 参照ドキュメント（リポジトリ内）
- 仮説メモ: docs/research/higher_tf_pullback_lower_tf_reversal_2026-06-08.md
- 参考画像: docs/research/images/mtf_pullback_reversal/
- 反例: docs/trade_diary/practice/entries/2026-06-04_gbpjpy_nagekiri_signal_buy.md（転換未確認で E01 エントリー → -11.2万）
- シグナル判断: docs/trade_diary/reference/signal_review_protocol.md
- 市場心理4段階: docs/research/市場心理図鑑/README.md（Event scanner → Trigger study → Strategy）

# MTF ペア（固定）
| 上位足 | 中位足 | 下位足（任意） |
|--------|--------|----------------|
| D1     | H4     | H1             |
| H4     | H1     | M15 or M5      |

# 操作定義 v0.1（必ずこの定義でラベル付け）

## A. 上位足トレンド（必須）
- 上昇押し目検証: 上位足 close > 上位足 SMA(20) かつ直近20本で higher high が1回以上
- 下降押し目検証: 上位足 close < 上位足 SMA(20) かつ lower low が1回以上

## B. 上位足「押し目 leg」（必須）
- swing high 確定後、swing low までの調整幅 >= 1.5 × ATR(14)（上位足）
- または trendline / 水平節目 ± 0.5 × ATR 以内で反発

## C. 下位足「転換」（検証の核心）
上昇トレンド中の押し目買い候補の場合:
1. 押し目区間内に lower high が2回以上（zigzag）
2. swing low 確定（安値更新停止）
3. 転換トリガー: 直近 lower high を下位足 **終値** で上抜け
4. （任意）M5/M15 で neckline ブレイク

下降トレンド中の押し目売り候補は上記を鏡像（higher low 連続 → high ブレイク）。

## D. 対照群（必須）
各銘柄・各方向について:
- **Group GO**: B + C を満たす
- **Group NO-GO**: B は満たすが C 未満（6/4 GBPJPY 投げ切り型）

# 検証タスク（段階的に実行）

## 段階1: Event scanner（手動20件 × 2群）
対象銘柄: USDJPY, GBPJPY, XAUUSD
期間: 2020-01-01 〜 2026-06-08
各銘柄あたり:
- Group GO: 10件
- Group NO-GO: 10件

各イベントについて以下を記録:
- symbol, htf, ltf, direction (long/short)
- event_date_htf, pullback_start, pullback_low/high, reversal_trigger_date_ltf
- entry_price（転換トリガー次足始値 or 首ブレイク）
- sl_price（転換 swing の外側 - 0.25×ATR）
- tp_price（上位足の次の節目 or 2R）
- mfe_24h, mfe_48h, mfe_120h（時間ベースでも可: 24/48/120 本）
- mae_24h, mae_48h, mae_120h
- outcome (+1 利確方向に2R到達 / 0 未到達 / -1 SL到達)
- notes（だまし、指標、E01 該当等）

出力: CSV（validation_results_template.csv 形式）

## 段階2: Trigger study（集計）
Group GO vs NO-GO を比較:
- 平均 MAE（24/48/120）
- 平均 MFE（24/48/120）
- 勝率（2R 到達率）
- SL 到達率
- PF, avg R（SL=1R 換算）

仮説が支持される条件:
- GO の avg MAE < NO-GO の avg MAE（有意差がなくても方向一致で可 v0.1）
- GO の MFE >= NO-GO の MFE
- GO の 2R 到達率 > NO-GO

## 段階3: レポート
Markdown で以下を出力:
1. 研究の問い（1行）
2. サンプル数と銘柄内訳
3. GO vs NO-GO 比較表
4. 支持 / 部分支持 / 棄却 の判定
5. 操作定義の修正案（X ATR, zigzag 本数等）
6. 実運用ルール案（signal_review_protocol 追記用1段落）
7. Pine 化の可否（段階4へ進むか）

# 禁止事項
- チャート形状の「なんとなく」だけで GO/NO-GO を分けない
- 転換未確認の投げ切り単独を GO に含めない（E01）
- 結果已知のトレード日誌だけで検証を完結させない（OHLC サンプル必須）
- 検証なしに売買ルール化しない

# 出力形式（段階2完了時）
```markdown
## MTF 押し目×転換 検証結果 v0.1

### 判定: 支持 / 部分支持 / 棄却

### 比較表
| 指標 | GO (n=) | NO-GO (n=) |
...

### 実運用ルール案
...

### 次のアクション
...
```

# 最初にやること
1. validation_results_template.csv を読む
2. GBPJPY / USDJPY の既存6枚画像事例を GO サンプル #1 #2 として登録
3. 6/4 GBPJPY 投げ切りを NO-GO サンプル #1 として登録
4. 残り17件を OHLC から抽出して CSV を埋める
```

---

## 段階別チェックリスト

| 段階 | 完了条件 | 担当 |
|---|---|---|
| 1 Event scanner | CSV 30行以上（GO/NO-GO 各15+） | 手動 + AI |
| 2 Trigger study | 比較表 + 判定1行 | AI / Python |
| 3 レポート | `mtf_pullback_validation_report_YYYY-MM-DD.md` | AI |
| 4 Pine | ラベルのみ（エントリーなし） | 後回し可 |

---

## 成功基準（v0.1）

| 結果 | 条件 |
|---|---|
| **支持** | GO の avg MAE < NO-GO かつ GO の 2R 到達率が +10pt 以上 |
| **部分支持** | MAE か MFE のどちらか一方のみ改善 |
| **棄却** | 差がない、または NO-GO の方が良い |

---

## 関連ファイル

| ファイル | 用途 |
|---|---|
| [validation_results_template.csv](validation_results_template.csv) | 結果入力テンプレ |
| [higher_tf_pullback_lower_tf_reversal_2026-06-08.md](higher_tf_pullback_lower_tf_reversal_2026-06-08.md) | 仮説本体 |
| [signal_review_protocol.md](../trade_diary/reference/signal_review_protocol.md) | 実運用への反映先 |
