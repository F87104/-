# アーカイブ — 心理・恐怖ゾーン研究スプリント（2026-05〜06）

**ステータス: フラット化（参照用のみ・新研究の前提にしない）**

このフォルダ群は「受講生の失敗心理 → Pine可視化 → Liveマップ → TBフィルタ」の一連の探索です。  
**収益検証の結論**: TrendBreak に心理 STOP を載せると **総Rが減る**（エントリー足の S を見送っても約 -43R/10年）。  
本番の収益軸は **TB + T5** のまま。心理系は **手動の追い抑制・教材** に留める。

---

## 確定したこと（捨てない事実だけ）

| 事実 | 根拠 |
|------|------|
| TB baseline 2015–24: **+194.6R / PF1.79**（6通貨） | `fakeout_before_after_2015_2024` |
| TB+T5: **+219.9R / PF1.86** | `ultimate_method_validation_results_2026-06-01.md` |
| 24h 内 H1 STOP と TB は **~99%重複** → 自動ブロック不可 | `psychology_practical_validation_2026-06-01.md` |
| エントリー足の S 付き TB は **+43R/50件** → 見送りは収益↓ | 同上 |
| 850件の主因は **損切遅れ・節目追い**（定性） | `trade_psychology_failure_reason_research_2026-05-31.md` |

---

## アーカイブ一覧（触らなくてよい）

### ドキュメント

- `fear_psychology_*` / `psychology_*` / `psychology_liquidity_param_sweep_*`
- `psychology_practical_*`
- `trade_psychology_*`（850件・つまずき・失敗Pine化）
- `student_stumble_*` / `fear_psychology_zones_v0_1.csv` 等

### Pine（研究・可視化 — 本番エントリーに使わない）

- `pine/visual/psychology_map_live.pine` — ルールベース STOP/WAIT（参考）
- `pine/visual/psychology_map_simple_*`
- `pine/research/psychology_map_live_validation_*`
- `pine/research/student_stumble_zones_*`
- `pine/visual/fear_psychology_*` / `trade_psychology_failure_inversion_visual.pine`

### スクリプト

- `scripts/build_fear_psychology_zones.py`
- `scripts/validate_psychology_map_live.py`
- `scripts/validate_psychology_practical.py`
- `scripts/sweep_psychology_liquidity_params.py`

---

## 本番で残すもの（心理スプリントとは別ライン）

| 用途 | パス |
|------|------|
| 売買本体 | `pine/production/TrendBreakV1_Final.pine` · `h4_t5_macd_bb_live_ready.pine` |
| 数値根拠 | `ultimate_method_v1_2026-06-01.md` |
| 第3候補検証 | `near_main_validation_roadmap_2026-06-01.md` |

新しいオリジナル研究は [ORIGINAL_RESEARCH_2026-06.md](ORIGINAL_RESEARCH_2026-06.md) から。
