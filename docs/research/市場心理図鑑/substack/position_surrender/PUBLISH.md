# Substack 投稿手順

## ファイル構成

```
position_surrender/
├── article.md          ← 本文（Substack にコピペ）
├── PUBLISH.md          ← このファイル
└── images/
    ├── 00_hero.png              カバー / 冒頭
    ├── 02_three_types.png       3類型まとめ
    ├── chart_01_seller_surrender.png
    ├── chart_05_denial.png
    ├── chart_07_exhaustion.png
    ├── chart_09_last_believer.png
    ├── 04_four_stages.png       6段階フロー
    ├── 03_real_vs_fake.png      投げ vs 反発
    └── 05_usdjpy_case.png       USDJPY 事例
```

## 画像の再生成

```bash
cd docs/research/市場心理図鑑/substack
python3 generate_substack_images.py
```

## Substack への貼り付け

1. **New post** を作成
2. **Title:** `ポジションを持っている人が投げ出す瞬間`
3. **Subtitle:** `ローソク足の形ではなく、降伏の心理を読む`
4. `article.md` の本文をセクションごとに貼り付け
5. 各 `![...](images/xxx.png)` の位置で **画像をアップロード**（ドラッグ&ドロップ）
6. 画像下に *イタリックのキャプション* を手動で追加（article.md 内の `*` 行）
7. **Cover image:** `00_hero.png` を設定

## 推奨タグ

`FX` `トレード心理学` `テクニカル分析` `USDJPY` `市場心理`

## 時間足の注記（読者向け）

記事内チャートはすべて **H4（4時間足）** ベース。  
図鑑の示意図は合成ローソク、USDJPY 図は実 OHLC。
