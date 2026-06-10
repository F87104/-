#!/usr/bin/env python3
"""TradingView 日足スクショに 4100 割れシナリオの注釈を書き込む。

使い方:
  python3 scripts/annotate_xauusd_d1_chart.py \\
    docs/trade_diary/practice/images/incoming/xauusd_d1.png \\
    docs/trade_diary/practice/images/2026-06-10_xauusd_04_d1_structure.png
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw, ImageFont

from chart_fonts import get_japanese_font


ANNOTATIONS = [
    {
        "xy": (24, 24),
        "lines": [
            "XAUUSD D1 — 4100 割れシナリオ（E-2026-06-10-001）",
            "5750 天井 → 暴落中（約 -27%）",
        ],
        "fill": (20, 24, 36, 220),
        "text": (255, 220, 100),
    },
    {
        "xy": (24, 120),
        "lines": [
            "4100 = 暴落途上の小足場（最後の踏み台）",
            "日足終値で下抜け → 下降加速シナリオ強化",
            "下は 3359 / 3137 まで支持薄（真空地帯）",
        ],
        "fill": (40, 20, 20, 210),
        "text": (255, 180, 180),
    },
    {
        "xy": (24, 240),
        "lines": [
            "建値 4164.77 ｜ OCO: SL 4236 / TP 4000",
            "加速確認: 終値<4100 → 翌日も4100下",
            "無効化: 4100下ヒゲ+終値4120上 / 4236タッチ",
        ],
        "fill": (20, 36, 28, 210),
        "text": (180, 255, 200),
    },
]


def load_font(size: int):
    return get_japanese_font(size)


def draw_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    text_color: tuple[int, int, int],
) -> None:
    line_h = 22
    pad = 10
    max_w = max(draw.textlength(line, font=font) for line in lines)
    box_w = int(max_w) + pad * 2
    box_h = line_h * len(lines) + pad * 2
    x, y = xy
    draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=8, fill=fill)
    for i, line in enumerate(lines):
        draw.text((x + pad, y + pad + i * line_h), line, font=font, fill=text_color)


def annotate(src: Path, dst: Path) -> None:
    img = Image.open(src).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(16)

    for spec in ANNOTATIONS:
        draw_box(draw, spec["xy"], spec["lines"], font, spec["fill"], spec["text"])

    # 4100 ライン付近（右側 75% 高さ）に矢印ラベル
    w, h = img.size
    ax, ay = int(w * 0.72), int(h * 0.58)
    draw.line((ax - 80, ay, ax, ay), fill=(255, 140, 0, 255), width=3)
    draw.polygon([(ax, ay), (ax - 12, ay - 8), (ax - 12, ay + 8)], fill=(255, 140, 0, 255))
    draw.text((ax - 200, ay - 28), "4100 足場", font=font, fill=(255, 180, 80))

    out = Image.alpha_composite(img, overlay).convert("RGB")
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, quality=95)
    print(f"Saved: {dst}")


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    annotate(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
