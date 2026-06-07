# 市場心理図鑑（Market Psychology Atlas）

ローソク足の「形」ではなく、**市場参加者の意思決定**を研究・記述するスキル。

## 目的

| やらないこと | やること |
|---|---|
| ダブルトップ、V字等の形で分類 | 心理・独白・需給で分類 |
| パターン名だけで売買 | 心理 → 検証可能条件へ翻訳 |
| 1本の巨大ストラテジー | Event scanner → Trigger → Strategy |

## コンテンツ一覧

### Substack 記事（投稿用）

| 記事 | 本文 | 画像 |
|---|---|---|
| **ポジションを持っている人が投げ出す瞬間** | [article.md](./substack/position_surrender/article.md) | [images/](./substack/position_surrender/images/)（9枚） |

投稿手順: [PUBLISH.md](./substack/position_surrender/PUBLISH.md)

### 研究版（GitHub 詳細）

- [articles/position_surrender_moment.md](./articles/position_surrender_moment.md) — 図鑑リンク・検証表付き完全版

## 画像の再生成

```bash
cd skills/market_psychology_atlas/substack
pip install matplotlib yfinance pandas
python3 generate_substack_images.py
```

出力: `position_surrender/images/`（9 PNG）

## Substack 投稿テンプレ

- **Title:** ポジションを持っている人が投げ出す瞬間
- **Subtitle:** ローソク足の形ではなく、降伏の心理を読む
- **Cover:** `position_surrender/images/00_hero.png`
- **時間足:** 記事内チャートはすべて **H4（4時間足）**

## 図鑑 Vol.1 関連パターン（本記事で使用）

| ID | パターン名 | 投げの文脈 |
|---:|---|---|
| 01 | 売り方降伏 | ショートの投げ（買い戻し） |
| 05 | 現実否認 | ロング投げの前段 |
| 07 | 正解待ち疲弊 | ロング投げ本番 |
| 09 | 最後の信念者 | 心理底の投げ |

## エージェント向け指示

記事・投稿を生成するとき:

1. **形の名前**（Capitulation 等）だけで説明しない → **独白**を書く
2. 投げは3類型（ロング清算 / ショートカバー / 最後の信念者）で整理
3. チャートは H4 を前提。TradingView 日常視野（数週間）の密度を意識
4. 投げ直後は「反転確信」ではなく「降伏の安堵」と明記
5. 画像は `substack/position_surrender/images/` を参照

## 関連リポジトリ

- 図鑑本体・スキャナ: `https://github.com/F87104/-`（`docs/research/市場心理図鑑/`）
- OHLC データ: `https://github.com/F87104/test.git` → `F87104_test/`
