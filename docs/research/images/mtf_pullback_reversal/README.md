# MTF 仮説 — チャート画像（TradingView 実スクショ）

**ここには TradingView の実スクリーンショットのみを置く。**  
AI 生成の再現画像は `_archive/generated_placeholder/` に退避済み（使用禁止）。

---

## 重要: チャット添付だけでは保存できない場合がある

Cloud Agent 環境では、チャットに貼った画像の **生ファイル（PNG）** が VM に届かず、  
説明文だけ渡されることがあります。その場合 **下記 B または C** で保存してください。

---

## 必要なファイル（7枚）

| incoming に置く名前 | 保存後のファイル名 | 銘柄 | TF |
|---|---|---|---|
| `usdjpy_d1.png` | `2026-06-08_usdjpy_d1_pullback_context.png` | USDJPY | 日足 |
| `usdjpy_h4.png` | `2026-06-08_usdjpy_h4_pullback_context.png` | USDJPY | 4時間 |
| `usdjpy_h1.png` | `2026-06-08_usdjpy_h1_reversal_detail.png` | USDJPY | 1時間 |
| `usdjpy_m5.png` | `2026-06-08_usdjpy_m5_reversal_entry.png` | USDJPY | 5分 |
| `gbpjpy_d1.png` | `2026-06-08_gbpjpy_d1_pullback_context.png` | GBPJPY | 日足 |
| `gbpjpy_h4.png` | `2026-06-08_gbpjpy_h4_pullback_context.png` | GBPJPY | 4時間 |
| `gbpjpy_h1.png` | `2026-06-08_gbpjpy_h1_reversal_detail.png` | GBPJPY | 1時間 |

---

## 保存方法

### A. incoming フォルダ（推奨）

1. TradingView で **スクリーンショット保存**（加工しない）
2. 上表の **incoming 名** にリネーム（例: `usdjpy_d1.png`）
3. このフォルダの **`incoming/`** にドラッグ＆ドロップ
4. ターミナルで:

```bash
bash scripts/install_mtf_screenshots.sh
git add docs/research/images/mtf_pullback_reversal/
git commit -m "docs: add real MTF TradingView screenshots"
git push
```

5. チャットで「incoming に置いた」と送る

### B. GitHub Web UI

1. [mtf_pullback_reversal/](.) を開く
2. **Add file → Upload files**
3. **保存後のファイル名**（右列）のままアップロード

### C. 直接このフォルダへ

保存後ファイル名で `docs/research/images/mtf_pullback_reversal/` に直接置いても可。

---

## 注意

- **GenerateImage / AI 再生成禁止**
- オレンジ・緑の手描きラインは **そのまま** 残す
- リサイズ・クロップ以外の加工禁止

---

## 状態（2026-06-08）

| ファイル | 状態 |
|---|---|
| USDJPY D1 / H4 / H1 / M5 | ⏳ 添付確認済み・**生 PNG 未着** → incoming 待ち |
| GBPJPY D1 / H4 / H1 | ⏳ incoming 待ち |
