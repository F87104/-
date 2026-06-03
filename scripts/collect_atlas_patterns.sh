#!/usr/bin/env bash
# 市場心理図鑑 — パターンライブラリを F87104_test から大量収集
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_ROOT="${F87104_DATA_ROOT:-$ROOT/F87104_test}"
COLLECT="$ROOT/docs/research/市場心理図鑑/collect_pattern_library.py"

echo "=== パターンライブラリ収集 ==="
echo "data root: $DATA_ROOT"
echo ""

if [[ ! -d "$DATA_ROOT" ]]; then
  echo "WARN: F87104_test なし → yfinance フォールバックで収集"
  python3 "$COLLECT" \
    --max-per-symbol 3 \
    --max-per-pattern 8
  exit 0
fi

python3 "$COLLECT" \
  --data-root "$DATA_ROOT" \
  --require-local \
  --max-per-symbol 8 \
  --max-per-pattern 25 \
  --min-gap 24 \
  --symbols XAUUSD USDJPY SILVER EURJPY GBPJPY AUDJPY CHFJPY

echo ""
echo "=== 完了 ==="
echo "一覧: docs/research/市場心理図鑑/collection/index.md"
