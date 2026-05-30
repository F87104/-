# F87104/skill リポジトリ用 配送バンドル

このフォルダは、**別リポジトリ [F87104/skill](https://github.com/F87104/skill)** に追加するための準備済みファイル一式です。

Cursor クラウドエージェントは現時点で `F87104/-` (本リポジトリ) にしかインストールされていないため、`F87104/skill` に直接 push できません。
そのためバンドルをここに配置し、ユーザー側で取り込めるようにしています。

---

## 中身

```
external/F87104-skill-bundle/
├── README.md                       ← このファイル (取り込み手順)
├── UPDATED_ROOT_README.md          ← F87104/skill の README.md に上書きする版
├── skills/
│   └── market_psychology/          ← 新スキル一式 (4ファイル)
│       ├── SKILL.md                   主マニュアル
│       ├── framework.md               共通の数値化軸
│       ├── pattern_library.md         10心理パターン辞書
│       └── status.md                  個別研究ステータススナップショット
└── market_psychology_skill.patch   ← git apply 用のパッチ (オプション)
```

---

## 取り込み方法 (どれか1つを選ぶ)

### 方法 A: Cursor を F87104/skill にも導入して再実行 (推奨)

1. https://github.com/apps/cursor を開く
2. F87104/skill リポジトリに対して Cursor をインストール
3. Cursor 上で同じタスクを再実行する

クラウドエージェントが直接 F87104/skill にコミット & プッシュできるようになります。

### 方法 B: 手動コピー

```bash
git clone https://github.com/F87104/skill.git
cd skill

cp -r ../<このリポジトリのclone>/external/F87104-skill-bundle/skills/market_psychology ./skills/
cp ../<このリポジトリのclone>/external/F87104-skill-bundle/UPDATED_ROOT_README.md ./README.md

git add skills/market_psychology README.md
git commit -m "Add market_psychology skill"
git push origin main
```

### 方法 C: パッチ適用

```bash
git clone https://github.com/F87104/skill.git
cd skill

git am < ../<このリポジトリのclone>/external/F87104-skill-bundle/market_psychology_skill.patch

git push origin main
```

---

## 追加されるスキル

**市場心理構造リサーチャー (Market Psychology Structure Researcher)**

- チャート形状を参加者心理 (Capitulation / Short Squeeze / Long Liquidation / Trap / Expectation Failure / Compression / FOMO / Relief Rally / Pain Trade / Dormant Breakout) に変換
- Python / Pine で検証可能な数値条件 (急落 / 棚 / 否定 / ボラ拡大 等)
- 4 段階フロー (Event scanner → Trigger study → Strategy → Pine parity)
- 本番昇格チェックリスト
- 個別研究 R1〜R7 のステータススナップショット (実装例)

実装の本体は本リポジトリ ([F87104/-](https://github.com/F87104/-)) の [`docs/research/market_psychology/`](../../docs/research/market_psychology/) を参照。

---

## 取り込み後にこのフォルダを消す

取り込みが終わったら、本リポジトリ側のこのフォルダは不要です。

```bash
git rm -r external/F87104-skill-bundle
git commit -m "Remove F87104/skill delivery bundle (applied)"
git push
```

または、`external/` 自体を `.gitignore` 化しても構いません。
