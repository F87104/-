#!/usr/bin/env bash
# 市場心理図鑑 — 実OHLCチャートを F87104_test で再生成する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_ROOT="${F87104_DATA_ROOT:-$ROOT/F87104_test}"
ATLAS="$ROOT/docs/research/市場心理図鑑"

echo "=== 市場心理図鑑 実OHLC 再生成 ==="
echo "repo:      $ROOT"
echo "data root: $DATA_ROOT"
echo ""

if [[ ! -d "$DATA_ROOT" ]]; then
  echo "ERROR: F87104_test が見つかりません。"
  echo ""
  echo "  1. バックアップから F87104_test/ をリポジトリ直下に配置"
  echo "  2. または: export F87104_DATA_ROOT=/path/to/F87104_test"
  echo ""
  echo "参考: docs/research/市場心理図鑑/SETUP_REAL_CHARTS.md"
  exit 1
fi

# 最低1ファイルあるか確認
if ! find "$DATA_ROOT" -name '*H1*.csv' -print -quit | grep -q .; then
  echo "ERROR: $DATA_ROOT に H1 CSV がありません。"
  exit 1
fi

echo "依存パッケージ確認..."
python3 -c "import matplotlib, pandas, numpy" 2>/dev/null || {
  pip install matplotlib pandas numpy yfinance -q
}

echo ""
echo "スキャン開始（2015年〜 F87104_test / H4）..."
python3 "$ATLAS/render_real_events.py" \
  --data-root "$DATA_ROOT" \
  --require-local \
  --symbols XAUUSD USDJPY SILVER EURJPY GBPJPY AUDJPY CHFJPY

echo ""
echo "=== 完了 ==="
echo "ギャラリー: $ATLAS/real_gallery.md"
echo "画像:       $ATLAS/images/real/"
echo ""
echo "GitHub に反映する場合:"
echo "  git add docs/research/市場心理図鑑/images/real/ \\"
echo "          docs/research/市場心理図鑑/real_gallery.md \\"
echo "          docs/research/市場心理図鑑/real_events_manifest.json"
echo "  git commit -m 'Regenerate atlas real OHLC charts from F87104_test'"
echo "  git push"
