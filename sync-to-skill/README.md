# F87104/skill への同期パッケージ

`skills/market_psychology_atlas/` を https://github.com/F87104/skill.git に配置するためのコピー元です。

## 含まれるもの

- `SKILL.md` — エージェント用スキル定義
- `articles/position_surrender_moment.md` — 研究版
- `substack/position_surrender/article.md` — **Substack 投稿用本文**
- `substack/position_surrender/images/` — **画像9枚**
- `substack/generate_substack_images.py` — 画像再生成

## あなたの PC で push する

```bash
# 方法1: スクリプト（skill を隣に clone して同期）
./scripts/sync_market_psychology_to_skill.sh

# 方法2: 手動
git clone https://github.com/F87104/skill.git
cp -r sync-to-skill/skills/market_psychology_atlas skill/skills/
cd skill
git checkout -b cursor/market-psychology-substack-04aa
git add skills/market_psychology_atlas/
git commit -m "Add market_psychology_atlas Substack article"
git push -u origin cursor/market-psychology-substack-04aa
```

## Substack 投稿

`skills/market_psychology_atlas/substack/position_surrender/PUBLISH.md` を参照。
