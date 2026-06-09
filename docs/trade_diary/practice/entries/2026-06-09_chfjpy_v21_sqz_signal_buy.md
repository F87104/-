# 2026-06-09 CHFJPY H4 買い — 本命v2.1 SQZ ロング

[← 実践日誌](../README.md) ／ [← トレード日誌トップ](../../README.md)

## サマリー

| 項目 | 内容 |
|---|---|
| 日時 | 2026-06-09 22:22 (JST) |
| 銘柄 | CHFJPY（スイスフラン/円） |
| 時間足 | H4 |
| 方向 | 買い |
| 数量 | 20（20万通貨） |
| 建値 | 201.319 |
| エントリー理由 | **本命v2.1 Market Psychology Matrix — SQZ v2.1 Long** |
| インジケータ | 本命v2.1 Market Psychology Matrix (Sqz + Cap + LL) |
| ブローカー | GMOあおぞらFX |
| 状態 | 建玉中（OCO 設定済み） |
| 備考 | シグナルレビュー GO 候補。Cap / LL ではなく ① Squeeze 正式シグナル |

## シグナル値（TradingView / v2.1 Matrix）

| 項目 | 価格 |
|---|---:|
| Entry (SQZ) | 201.319 |
| Stop Loss (SL) | 200.251 |
| Take Profit (TP) | 203.456 |
| リスク幅 | 1.068（約 106.8 pips） |
| リスクリワード | 2.0R |
| 構造 | SQZ（踏み上げ棚ブレイク） |
| マトリクス | CHFJPY: Sqz ✅ / Cap ✅ / LL ✅（今回は Sqz のみ発火） |

## OCO（GMOあおぞらFX）

| 項目 | 内容 |
|---|---|
| 注文種類 | OCO（決済） |
| 指値（利確） | **203.456** |
| 逆指値（損切） | **200.251** |
| 有効期限 | 無期限 |
| 設定時刻 | 22:22 (JST) |

## シグナルレビュー（エントリー前）

| チェック | 結果 |
|---|---|
| 正式 SQZ シグナル（Entry/SL/TP ライン付き） | ✅ |
| H4 チャート | ✅ |
| 通貨マトリクス（CHFJPY Sqz ON） | ✅ |
| 踏み上げマーカーのみ（WAIT 対象） | ❌ 該当せず |
| OCO 設定 | ✅ |

## 構造メモ

- 6 月初旬 204 付近から 200.3 付近までの急落後、下値で棚形成 → 棚高値（201.319）を上抜け。
- D1 は下降トレンド中の戻り押し目狙い。TP 203.456 は 6 月初旬の押し安値付近（最初の抵抗）。
- v2.1 早期撤退: 12 本経過時点で MFE < 0.5R なら約 −0.35R で手仕舞い検討。

## 写真

### 1. TradingView — 本命v2.1 SQZ ロングシグナル

![CHFJPY H4 — SQZ 201.319 Entry / SL 200.251 / TP 203.456](../images/2026-06-09_chfjpy_01_tradingview_sqz_signal.png)

- FOREXCOM H4、急落後の棚上抜け
- 緑ラベル **SQZ 201.319**、SL/TP ライン表示

### 2. GMOあおぞらFX — OCO 決済注文確認

![GMO OCO — 指値 203.456 / 逆指値 200.251](../images/2026-06-09_chfjpy_02_oco_gmo.png)

- CHF/JPY 売り決済 OCO（ロングの利確・損切）
- 取引数量 20万通貨、有効期限 無期限

## メモ

- 主力とは別系統の **本命v2.1**（H4 市場心理マトリクス）。本命1 V1 / 本命2 H4 T5 とは独立。
- 関連 Pine（deep-research ブランチ）: `pine/research/market_psychology_v2_matrix_strategy.pine`
- フォワード記録対象（v2.1 Matrix 検証 30 件目標の 1 件目候補）。
- 決済後は [index.csv](../index.csv) の `status` と損益を更新する。
