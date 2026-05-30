# 個別研究 ステータススナップショット

> このスキルを適用して進めた研究の **判定** と **本番昇格条件** を記録するスナップショット。
> 新しい研究を追加するたび、ここに 1 行追記する。
> [`SKILL.md`](./SKILL.md) / [`framework.md`](./framework.md) / [`pattern_library.md`](./pattern_library.md) の運用ログにあたる。

**最終更新**: 2026-05-30

---

## 1. 判定スキーマ

| ラベル | 意味 | 基準 |
|---|---|---|
| 🟢 本線採用 | 本番運用 | PF ≥ 1.8 / DD ≤ Total R の 1/3 / OOS 再現 / フォワード ≥ 30 件 |
| 🟡 フォワード候補 | Pine 照合 + フォワード記録中 | PF ≥ 1.7 / DD 小 / 構造説明可 / OOS プラス |
| 🟠 準本命 (件数不足) | 期待値はあるが trades < 20。デモ / 小ロット | PF 高 / OOS プラス / 件数のみ不足 |
| 🟣 文脈フィルタ | Entry trigger には使わず、見送り判定に使う | 既存戦略に重ねた時に PF / DD 改善 |
| 🔵 アンチパターン | 単独使用は不採用と確認済み | PF < 1.3 または OOS で崩れる |
| ⚪ 辞書 / 枠組み | パターンの定義そのもの | — |

---

## 2. ステータス表 (実装例: F87104/- リポジトリの研究)

| # | 研究 | パターン | TF | 判定 | 主要指標 |
|---|---|---|---|---|---|
| R1 | Pattern Library | 01-10 | — | ⚪ 枠組み | — |
| R2 | Indicator Denial Reaction | 04 / 09 | D1 | 🟣 文脈フィルタ | D1 Don20 否定 L 368 / +63R / PF 1.32 (OOS PF 3.59) |
| R3 | D1 Bear Trap + H4 V Reclaim | 04 (逆発見) | H4 | 🟣 文脈フィルタ | AVOID_D20_OR_RSI_30D 73 / +30.55R / PF 2.08 |
| R4 | Trap / False Break Reaction | 04 | D1 / H4 | 🔵 単独不採用 | D1 CLOSEFAIL_L120 287 / PF 1.31 → OOS PF 0.95 |
| R5 | D1 Trap Delayed H4 Shelf Strict | 04 + 02 | H4 | 🟠 準本命 (9 件) | 9 / 100% / +13.35R / PF inf / DD 0 / OOS +4.46R |
| R6 | Market Psychology Squeeze Strict | 02 | H4 | 🟡 フォワード候補 | 43 / +24.72R / PF 2.21 / DD 3.09R / OOS +8.89R |
| R7 | Squeeze 通貨相性 | 02 補助 | H4 | 🟣 補助分析 | XAUUSD PF 4.45 / GBPJPY PF 0.07 |

---

## 3. 数字スナップショット

各研究の **代表ルール** だけを集めた、変更追跡用の数字スナップショット。

| 研究 | 代表ルール | trades | WR | total R | PF | DD | OOS R | 取得日 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| R2 | D1 Don20 False Break L (Q) | 368 | 47.28% | +63.29R | 1.32 | 14.87R | +16.20R | 2026-05-29 |
| R3 | RS120_BODY45_CLOSE60 + AVOID_D20/RSI_30D (ex XAU) | 73 | 57.53% | +30.55R | 2.08 | 4.51R | +9.06R | 2026-05-29 |
| R4 | D1 CLOSEFAIL_L120_W6_BODY_RR15 | 287 | 49.83% | +42.27R | 1.31 | 10.55R | -1.25R | 2026-05-30 |
| R5 | D1 Trap A30_180 + Shelf6 + SIGADX30 | 9 | 100% | +13.35R | inf | 0.00R | +4.46R | 2026-05-30 |
| R6 | SQZ_STRICT_RR2 ex GBPJPY | 43 | 53.49% | +24.72R | 2.21 | 3.09R | +8.89R | 2026-05-30 |
| R7 | SQZ Strict XAUUSD 単独 | 10 | 70.0% | +10.73R | 4.45 | 2.07R | +5.95R | 2026-05-30 |

---

## 4. アンチパターン (毎回確認する)

| # | やったこと | なぜダメだったか | 教訓 |
|---|---|---|---|
| AP1 | H4 Trap 単独逆張り | 上位でも `CLOSEFAIL_L55_W8_STRICT_RR15` で 360 / -17R / PF 0.92 | Trap は Entry trigger にしない |
| AP2 | D1 売り否定直後の H4 V 右肩買い | trades 減 + PF / DD 悪化 (4-17 件で全てマイナス〜悪化) | D1 売り否定は「直近にあったら見送る」 |
| AP3 | Capitulation 単独 (D1 なし) | `CAP_NO_D1_RR2` 300 / -2.28R / PF 0.99 | ヒゲ底だけでは反転継続を確認できない |
| AP4 | Long Liquidation の単純ミラー (短側 Squeeze) | 強くなかった (旧検証) | 短側は別定義が必要 (急騰後の買い投げに限定) |
| AP5 | GBPJPY で Squeeze Strict | 8 / -6.66R / PF 0.07 | 通貨除外を固定 |

---

## 5. 短期ロードマップ

| 順位 | 内容 | 完了条件 |
|---|---|---|
| 1 | Squeeze Strict の Pine parity + volume ON / OFF 比較 | Python / TV のシグナル時刻が一致、volume で PF / DD が改善するか結論 |
| 2 | Squeeze Strict のフォワード 30 件記録 | 30 件到達時の Total R / PF / DD を再評価 |
| 3 | D1 Trap Delayed H4 Shelf Strict のフォワード 20 件記録 | 20 件到達時に件数不足解消 / 本番昇格判断 |
| 4 | Long Liquidation 独立検証 | 急騰後の買い投げ定義 + 短側 Squeeze ミラーとの差分 |
| 5 | Capitulation + 実 volume の独立検証 | TradingView volume 1.3〜2.0 倍で trades / PF / DD |
| 6 | Dormant Breakout 独立検証 | 120 / 360 / 1250 本の休眠節目更新 + 初押し + 再ブレイク |

---

## 6. 新研究を追加する時のテンプレート

新しい研究を追加する時は、以下の節をこのファイルに 1 行追記する。

```
| R? | <研究名> | <パターンID> | <TF> | <判定> | <主要指標> |
```

そして数字スナップショット節にも 1 行追加:

```
| R? | <代表ルール> | <trades> | <WR> | <total R> | <PF> | <DD> | <OOS R> | <取得日> |
```

判定が変わった場合は **上書き** する (履歴は git log で追える)。
