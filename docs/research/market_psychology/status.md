# 市場心理研究 ステータス & 判定 (Status)

> 個別研究の **判定** と **本番昇格条件** を一覧化したスナップショット。
> 数字の出典は各研究ノートおよびバックテストレポート。

**最終更新**: 2026-05-30
**親ドキュメント**: [`README.md`](./README.md)

---

## 1. 判定スキーマ

| ラベル | 意味 | 基準 |
|---|---|---|
| 🟢 本線採用 | 本番運用 (このリポジトリの2本柱に編入) | PF ≥ 1.8 / DD ≤ Total R の 1/3 / OOS 再現 / フォワード ≥ 30件 |
| 🟡 フォワード候補 | Pine照合 + フォワード記録中。本番昇格を判断中 | PF ≥ 1.7 / DD 小 / 構造説明可 / OOS プラス |
| 🟠 準本命 (件数不足) | 期待値はあるが trades < 20。デモ/小ロット監視 | PF 高 / OOS プラス / 件数のみ不足 |
| 🟣 文脈フィルタ | Entry triggerには使わず、見送り判定に使う | 既存戦略に重ねた時にPF/DD改善 |
| 🔵 アンチパターン | 単独使用は不採用と確認済み | PF < 1.3 または OOS で崩れる |
| ⚪ 辞書 / 枠組み | パターンの定義そのもの | — |

---

## 2. ステータス表

| # | 研究 | パターン | TF | 判定 | 主要指標 | 次の行動 |
|---|---|---|---|---|---|---|
| R1 | [Pattern Library](../market_psychology_pattern_library_2026-05-30.md) | 01-10 | — | ⚪ 枠組み | — | Long Liquidation / Capitulation / Dormant Breakout の独立検証 |
| R2 | [Indicator Denial Reaction](../indicator_denial_reaction_2026-05-29.md) | 04, 09 | D1 | 🟣 文脈フィルタ | D1 Don20否定L 368 / +63R / PF 1.32 (OOS PF 3.59) | Clean H4 V Reclaim へ統合済み |
| R3 | [D1 Bear Trap + H4 V Reclaim](../d1_bear_trap_h4_v_reclaim_2026-05-29.md) | 04 (逆発見) | H4 | 🟣 文脈フィルタ | AVOID_D20_OR_RSI_30D 73 / +30.55R / PF 2.08 | Clean H4 V Reclaim Pineで実装済み |
| R4 | [Trap / False Break Reaction](../trap_false_break_reaction_2026-05-30.md) | 04 | D1/H4 | 🔵 単独不採用 | D1 CLOSEFAIL_L120 287 / PF 1.31 → OOS PF 0.95 | Entry triggerには使わない。文脈用途のみ |
| R5 | [D1 Trap Delayed H4 Shelf Strict](../d1_trap_h4_shelf_strict_2026-05-30.md) | 04 + 02 | H4 | 🟠 準本命 (9件) | 9 / 100% / +13.35R / PF inf / DD 0 / OOS +4.46R | フォワード20件記録 |
| R6 | [Market Psychology Squeeze Strict](../market_psychology_squeeze_strict_2026-05-30.md) | 02 | H4 | 🟡 フォワード候補 | 43 / +24.72R / PF 2.21 / DD 3.09R / OOS +8.89R | フォワード30件 + volume ON/OFF比較 |
| R7 | [Squeeze 通貨相性](../market_psychology_squeeze_currency_compatibility_2026-05-30.md) | 02 補助 | H4 | 🟣 補助分析 | XAUUSD PF 4.45 / GBPJPY PF 0.07 | XAUUSDを本命、GBPJPYを除外として固定 |

---

## 3. 本番昇格チェックリスト

新しい市場心理手法を **本番採用 (🟢)** にするためのチェックリスト。

### 必須

- [ ] **Python検証**: Research 2015-2024 で trades ≥ 30、PF ≥ 1.7、DD ≤ Total R の 1/3
- [ ] **OOS 2025-2026** で PF ≥ 1.3、Total R がプラス
- [ ] **構造説明**: 「なぜ勝ちやすいか」を1ページ以内で日本語で書ける
- [ ] **Pine parity**: Pythonとシグナル時刻 / 方向が一致 (timezone, [1] off-by-one, request.security lookahead 等の罠を確認)
- [ ] **フォワード20〜30件**: TradingView上で実際にシグナルが出ること、再現されること
- [ ] **通貨スクリーニング**: 弱い通貨を除外 (例: Squeeze→GBPJPY、D1 Trap Delayed→XAUUSD/CHFJPY/SILVER)
- [ ] **コスト込み**: spread + slippage 控除後も PF/DD 要件を満たす
- [ ] **連敗想定**: max losing streak と DD が運用許容内 (例: 1Rリスクで DD 5R以内)

### 推奨

- [ ] **Volumeフィルタ比較**: TradingView実volume `volume > sma(volume,20) × 1.3` のON/OFFで挙動を確認
- [ ] **重複ルール**: 他戦略 (TrendBreakV1 / H4 T5 / Clean H4 V Reclaim) と同時シグナル時の取捨選択を決める
- [ ] **DDストップ**: 累計DD 20%でPineの売買を自動停止 (`STRATEGY_GUIDE.md` の運用ガード)

---

## 4. 「やらないこと」 リスト (アンチパターン)

| # | やったこと | なぜダメだったか | 教訓 |
|---|---|---|---|
| AP1 | H4 Trap単独逆張り | 上位でも `CLOSEFAIL_L55_W8_STRICT_RR15` で 360 / -17R / PF 0.92 | Trapは Entry trigger にしない |
| AP2 | D1売り否定直後の H4 V右肩買い | trades減 + PF/DD悪化 (4-17件で全てマイナス〜悪化) | D1売り否定は「直近にあったら見送る」 |
| AP3 | Capitulation 単独 (D1なし) | `CAP_NO_D1_RR2` 300 / -2.28R / PF 0.99 | ヒゲ底だけでは反転継続を確認できない |
| AP4 | Long Liquidation の単純ミラー (短側Squeeze) | 強くなかった (旧検証) | 短側は別定義が必要 (急騰後の買い投げに限定) |
| AP5 | GBPJPYで Squeeze Strict | 8 / -6.66R / PF 0.07 | 通貨除外を固定 |

---

## 5. ロードマップ (短期)

| 順位 | 内容 | 完了条件 |
|---|---|---|
| 1 | Squeeze Strict の Pine parity + volume ON/OFF比較 | Python/TVのシグナル時刻が一致、volumeでPF/DDが改善するか結論 |
| 2 | Squeeze Strict のフォワード30件記録 | 30件到達時の Total R / PF / DD を再評価 |
| 3 | D1 Trap Delayed H4 Shelf Strict のフォワード20件記録 | 20件到達時に件数不足解消 / 本番昇格判断 |
| 4 | Long Liquidation 独立検証 | 急騰後の買い投げ定義 + 短側Squeezeミラーとの差分 |
| 5 | Capitulation + 実volume の独立検証 | TradingView volume 1.3〜2.0倍で trades / PF / DD |
| 6 | Dormant Breakout 独立検証 | 120/360/1250本休眠節目更新 + 初押し + 再ブレイク |

---

## 6. 数字のスナップショット

各研究の **代表ルール** だけを集めた、変更追跡用の数字スナップショット。
更新時はこの表を上書きする。

| 研究 | 代表ルール | trades | WR | total R | PF | DD | OOS R | 取得日 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| R2 | D1 Don20 False Break L (Q) | 368 | 47.28% | +63.29R | 1.32 | 14.87R | +16.20R | 2026-05-29 |
| R3 | RS120_BODY45_CLOSE60 + AVOID_D20/RSI_30D (ex XAU) | 73 | 57.53% | +30.55R | 2.08 | 4.51R | +9.06R | 2026-05-29 |
| R4 | D1 CLOSEFAIL_L120_W6_BODY_RR15 | 287 | 49.83% | +42.27R | 1.31 | 10.55R | -1.25R | 2026-05-30 |
| R5 | D1 Trap A30_180 + Shelf6 + SIGADX30 | 9 | 100% | +13.35R | inf | 0.00R | +4.46R | 2026-05-30 |
| R6 | SQZ_STRICT_RR2 ex GBPJPY | 43 | 53.49% | +24.72R | 2.21 | 3.09R | +8.89R | 2026-05-30 |
| R7 | SQZ Strict XAUUSD単独 | 10 | 70.0% | +10.73R | 4.45 | 2.07R | +5.95R | 2026-05-30 |

---

## 7. 関連リンク

- 全戦略の判定マトリクス: [`docs/BACKTEST_INDEX.md`](../../BACKTEST_INDEX.md)
- 本番戦略 (2本柱) の運用ガイド: [`STRATEGY_GUIDE.md`](../../../STRATEGY_GUIDE.md)
- 市場心理ハブ: [`README.md`](./README.md)
- 共通枠組み: [`framework.md`](./framework.md)
