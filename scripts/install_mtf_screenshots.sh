#!/usr/bin/env bash
# TradingView 実スクショを incoming/ から本番ファイル名へコピー（加工なし）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IN="$ROOT/docs/research/images/mtf_pullback_reversal/incoming"
OUT="$ROOT/docs/research/images/mtf_pullback_reversal"

declare -A MAP=(
  ["gbpjpy_d1"]="2026-06-08_gbpjpy_d1_pullback_context.png"
  ["gbpjpy_h4"]="2026-06-08_gbpjpy_h4_pullback_context.png"
  ["gbpjpy_h1"]="2026-06-08_gbpjpy_h1_reversal_detail.png"
  ["usdjpy_d1"]="2026-06-08_usdjpy_d1_pullback_context.png"
  ["usdjpy_h4"]="2026-06-08_usdjpy_h4_pullback_context.png"
  ["usdjpy_h1"]="2026-06-08_usdjpy_h1_reversal_detail.png"
  ["usdjpy_m5"]="2026-06-08_usdjpy_m5_reversal_entry.png"
)

if [[ ! -d "$IN" ]]; then
  echo "missing: $IN" >&2
  exit 1
fi

installed=0
for key in "${!MAP[@]}"; do
  for ext in png PNG jpg jpeg webp; do
    src="$IN/${key}.${ext}"
    if [[ -f "$src" ]]; then
      cp -a "$src" "$OUT/${MAP[$key]}"
      echo "installed: ${MAP[$key]}  <=  ${key}.${ext}"
      installed=$((installed + 1))
      break
    fi
  done
done

if [[ "$installed" -eq 0 ]]; then
  echo "No files found in incoming/. Expected names like usdjpy_d1.png" >&2
  echo "See docs/research/images/mtf_pullback_reversal/README.md" >&2
  exit 1
fi

echo "Done: $installed file(s). Commit with:"
echo "  git add docs/research/images/mtf_pullback_reversal/*.png && git commit -m 'docs: add real MTF TradingView screenshots'"
