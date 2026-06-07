#!/usr/bin/env bash
# 市場心理図鑑 Substack 記事を F87104/skill.git へ同期する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/sync-to-skill/skills/market_psychology_atlas"
DEST="${SKILL_REPO:-$ROOT/../skill}"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: $SRC がありません"
  exit 1
fi

if [[ ! -d "$DEST/.git" ]]; then
  echo "skill リポジトリを clone します..."
  git clone https://github.com/F87104/skill.git "$DEST"
fi

mkdir -p "$DEST/skills"
rsync -a --delete "$SRC/" "$DEST/skills/market_psychology_atlas/"

cd "$DEST"
BRANCH="cursor/market-psychology-substack-04aa"
git checkout -B "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"

# README にスキル行がなければ追記（手動確認推奨）
if ! grep -q "market_psychology_atlas" README.md; then
  echo ""
  echo "README.md に以下を追記してください:"
  echo "| **市場心理図鑑 (market_psychology_atlas)** | Substack記事・画像9枚 | [SKILL.md](./skills/market_psychology_atlas/SKILL.md) |"
fi

git add skills/market_psychology_atlas/
git status --short

if git diff --cached --quiet; then
  echo "変更なし"
  exit 0
fi

git commit -m "Add market_psychology_atlas skill with Substack surrender article"
git push -u origin "$BRANCH"

echo ""
echo "完了: https://github.com/F87104/skill/tree/$BRANCH/skills/market_psychology_atlas"
