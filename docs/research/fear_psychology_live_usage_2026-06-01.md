# 恐怖ゾーン — 未来相場での使い方

> **アーカイブ** — 新研究は [ORIGINAL_RESEARCH_2026-06.md](ORIGINAL_RESEARCH_2026-06.md)。本番TBを心理マップで止めない（収益検証済み）。参照用のみ。


作成日: 2026-06-01

## 2種類のツール

| 種類 | ファイル | いつ使う |
|------|----------|----------|
| **過去の学習** | `pine/visual/psychology_map_simple_gbpjpy.pine` | 受講生が実際に負けた価格帯の復習・教材 |
| **未来の運用** | `pine/visual/psychology_map_live.pine` v1.0.4（通貨プリセット・CHECK） | これから先の相場（ルールが自動で動く） |
| **実践検証** | [psychology_practical_validation_2026-06-01.md](psychology_practical_validation_2026-06-01.md) | TB/T5×心理ゲート・チェックリスト |

過去データは **固定配列** なので、価格が新しい節目（例: GBPJPY 215円台）には出てきません。  
未来用は **節目・高安・伸び切り** のルールだけで判定します（研究の F1/F2/F3 と同系統）。

## TradingView 設定（推奨）

1. 他の研究インジは **OFF**（TB、心理マトリクス、旧 Stumble など）
2. **`Psychology Map Live v1.0`** だけを **GBPJPY / USDJPY / XAUUSD の 1H** に追加
3. 初期設定のまま運用 → 必要なら F1 の「整数±」だけ微調整

## 表示の意味（3つ）

| 表示 | 意味 | あなたの行動 |
|------|------|----------------|
| **赤帯 STOP** | 今は群衆が飛び乗りやすい | 新規エントリー禁止 |
| **青緑帯 WAIT** | STOP のあと、ここまで押す想定 | 指値・待ちの候補 |
| **橙 ◇** | STOP 後に同方向で再追い（どテン候補） | 入り直し禁止 |

右上の **S** マークは、その足で STOP 条件が成立した印です。

## ルールの中身（研究との対応）

- **F1**: 整数・50銭（XAU は 10/50 ドル）付近 × 20本高安/安値端 × 同方向足  
  → 199円台・140円・2950ドル追いの一般化
- **F2**: 大足（≥1.05ATR）の直後 1〜2 本の同方向  
  → 「伸び切り直後の飛び乗り」
- **節目抜け**: 48本スイング高安を抜けた直後  
  → 「ダマシの節目抜け」型
- **◇**: STOP から 72 本以内の同方向 F1/F2 再発  
  → データ上の「損切後72hどテン」の近似

## アラート

インジ設定 → アラート → 次のいずれか:

- `Psychology STOP` … 入るな
- `Psychology WAIT` … 押し待ち
- `Psychology REVENGE` … どテン候補

## v2.x 本命との併用

- **エントリー抑制**: [stumble_chase_suppression_filter_v0_1.md](stumble_chase_suppression_filter_v0_1.md) の **F1** を matrix に載せる（バックテスト済み）
- **目視**: Live インジで「今まさに STOP か」を確認
- **復習**: Simple（通貨別）で「過去に何人が負けたか」を確認

## データの更新（任意）

新しい受講生チャートが溜まったら:

```bash
python3 scripts/build_fear_psychology_zones.py
```

→ CSV 更新 → 通貨別 Simple Pine を再生成（Live は再生成不要）。

## 本番エンジンとの併用（TB+T5）

[psychology_practical_validation_2026-06-01.md](psychology_practical_validation_2026-06-01.md) より:

- **TBを心理マップで自動全停止しない**（6h/24h内STOPはTBの約99%と重なる）
- **手動見送り**: エントリー足に **S** があるとき（約13%）
- **CHECK（C）**: STOP条件だが直前6本が停滞 → TBは可（T5停滞と同思想）
- **T5**: 心理ゲート不要

## 検証コード（受講生は参考・未来はルール）

| 用途 | ファイル |
|------|----------|
| **TV Strategy 検証** | `pine/research/psychology_map_live_validation_v0_2.pine`（v0.1はF2過多で非推奨） |
| **OHLC オフライン検証** | `scripts/validate_psychology_map_live.py` |
| **レポート出力** | `docs/research/psychology_map_live_validation_report.md` |

### TV 手順

1. GBPJPY **1H** — 他のインジはすべて OFF
2. **`psychology_map_live_validation_v0_2.pine`** を貼る
3. まずモード **STOPのみ(推奨)** → Trades=0、薄い赤背景と **S** だけ確認
4. 比較するときだけ **比較(追いブレイク)** に切替 → フィルタ OFF/ON で Trades と **×ブロック** を比較
5. チャート設定 → スタイル → **トレードの表示をオフ**（L/S/LX/SX の矢印を消す）

**PF 0.8 前後は正常** — わざと負けやすい追いブレイクの実験台。見るのは「フィルタで件数と損失が減るか」。

### Python 手順

```bash
python3 scripts/validate_psychology_map_live.py
```

STOP 後24本の「逆行率」と、受講生全敗帯で STOP が何本出たかを集計します。

## 節目＝一概にダメではない（重要）

受講生の失敗は **「節目の数字に惹かれて、停滞も再ブレイクも待たず飛び乗った」** ケースが多い。  
一方、本命の **T5** は **節目付近で停滞 → 力が上に湧いてブレイク** するパターンを狙う（stagnation / rebreak、practical で PF が高い）。

| 状況 | 心理 | Live の読み（目標） |
|------|------|---------------------|
| 節目手前で **直線追い** | FOMO・恐怖の天井 | **STOP**（入るな） |
| 節目付近で **停滞→再上抜け** | エネルギー蓄積後の解放 | **CHECK**（T5/TB と確認） |
| 節目抜けの **直後1本** | ダマシ・損切集中 | **STOP**（抜け直後は待つ） |
| 押し戻り帯 | 待てた側 | **WAIT** |

現行 Live v0.2.x の F1 は「節目初タッチ×高安端」を **粗い STOP** として使っている。  
**停滞検知が付いたら STOP を CHECK に降格する** のが次の実装ステップ（H4 停滞は `sai_mtf_visual_checker` / T5 Pine と同系）。

> 形（節目・抜け）だけ見ると STOP。  
> **停滞＋再加速が出たら「禁止」ではなく「確認してから EXECUTE」** — これが TB/T5 との接続点。

## 限界（正直な注意）

- Live は **あなた個人の損切** ではなく、**群衆が犯しやすい形** の検出です。
- どテン ◇ は「再追いの形」の近似で、必ずしも口座の損切タイミングと一致しません。
- 確定足 ON のとき、リアルタイムは **足確定後** に STOP が出ます（早めたい場合は OFF、ただしダマシ増）。
