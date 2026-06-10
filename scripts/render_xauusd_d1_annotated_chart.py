#!/usr/bin/env python3
"""4100 割れシナリオ注釈付き D1 ゴールドチャート図を PNG 生成する。"""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/ から chart_fonts を import 可能にする
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw

from chart_fonts import get_japanese_font

OUT = Path("docs/trade_diary/practice/images/2026-06-10_xauusd_04_d1_structure_annotated.png")
W, H = 1400, 900


def font(size: int, bold: bool = False):
    return get_japanese_font(size, bold=bold)


def text_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    title: str,
    lines: list[str],
    title_color: tuple[int, int, int],
    bg: tuple[int, int, int],
    border: tuple[int, int, int],
    f_title,
    f_body,
    width: int = 440,
) -> None:
    x, y = xy
    pad = 14
    lh = 24
    h = pad * 2 + 28 + lh * len(lines)
    draw.rounded_rectangle((x, y, x + width, y + h), radius=10, fill=bg, outline=border, width=2)
    draw.text((x + pad, y + pad), title, font=f_title, fill=title_color)
    ty = y + pad + 30
    for line in lines:
        draw.text((x + pad, ty), line, font=f_body, fill=(226, 232, 240))
        ty += lh


def main() -> None:
    img = Image.new("RGB", (W, H), (11, 15, 23))
    draw = ImageDraw.Draw(img)
    f_title = font(22, True)
    f_head = font(17, True)
    f_body = font(15)
    f_small = font(13)

    draw.text((40, 24), "XAUUSD D1 — 4100 割れシナリオ注釈", font=f_title, fill=(229, 231, 235))
    draw.text((40, 54), "E-2026-06-10-001 手法外ショート | FXCM 日足 | 2026-06-10", font=f_small, fill=(156, 163, 175))

    # chart panel
    draw.rounded_rectangle((80, 95, 1260, 715), radius=12, outline=(51, 65, 85), width=2, fill=(15, 23, 42))

    # levels y mapping
    levels = [
        (130, "5750 天井", (239, 68, 68), True),
        (250, "4236 SL", (248, 113, 113), True),
        (310, "4164 建値", (34, 197, 94), False),
        (370, "4100 足場", (251, 146, 60), False),
        (430, "4000 TP", (74, 222, 128), True),
        (550, "3359 支持", (251, 191, 36), False),
        (610, "3137 支持", (203, 213, 225), True),
    ]
    for y, label, color, dashed in levels:
        if dashed:
            for x in range(80, 1260, 16):
                draw.line((x, y, x + 8, y), fill=color, width=2)
        else:
            draw.line((80, y, 1260, y), fill=color, width=3 if "4100" in label else 2)
        draw.text((1270, y - 6), label, font=f_small, fill=(148, 163, 184))

    # schematic path
    path_flat = [(120, 560), (320, 520), (520, 470), (720, 360), (920, 190), (980, 130)]
    path_drop = [(980, 130), (1120, 260), (1180, 370), (1220, 500), (1240, 560)]
    draw.line(path_flat, fill=(100, 116, 139), width=3)
    draw.line(path_drop, fill=(239, 68, 68), width=5)

    # vacuum zone
    draw.rectangle((1180, 430, 1240, 610), fill=(127, 29, 29, 60))
    draw.text((1195, 500), "真空", font=f_small, fill=(252, 165, 165))

    # 4100 arrow
    draw.line((880, 370, 1040, 370), fill=(251, 146, 60), width=3)
    draw.polygon([(1040, 370), (1024, 362), (1024, 378)], fill=(251, 146, 60))
    draw.text((820, 348), "4100 暴落途上の小足場", font=f_body, fill=(253, 186, 116))

    text_box(
        draw, (110, 125), "仮説（記録）", [
            "下降の勢いが止まらない。",
            "日足 4100 足場を終値で下抜け",
            "→ 下降加速シナリオ強化",
            "※4100は直近安値より小さな踏み台",
        ],
        (253, 224, 71), (30, 41, 59), (251, 146, 60), f_head, f_body,
    )
    text_box(
        draw, (110, 295), "日足構造", [
            "5750 パラボリック天井 → 約-27%調整",
            "4100下は 3359/3137 まで支持薄",
            "現在4166付近 = 4100手前の攻防",
        ],
        (147, 197, 253), (23, 37, 84), (96, 165, 250), f_head, f_body,
    )
    text_box(
        draw, (110, 430), "建玉 OCO", [
            "売り 50 @ 4164.77 | SL 4236 | TP 4000",
            "4100割れ=保有継続確認 | 4236=撤退",
            "手法外 — フォワード検証対象外",
        ],
        (134, 239, 172), (5, 46, 22), (74, 222, 128), f_head, f_body,
    )
    text_box(
        draw, (760, 125), "加速シナリオ確認", [
            "1. 日足終値 < 4100（下ヒゲだけ不可）",
            "2. 翌日も 4100 を戻せない",
            "3. H4 で 4100 下の棚 → 再下落",
            "無効化: 4100下ヒゲ+終値4120上",
            "　　　　4236タッチ / 4200上2本",
        ],
        (196, 181, 253), (31, 41, 55), (167, 139, 250), f_head, f_body, width=460,
    )
    text_box(
        draw, (760, 360), "価格マップ", [
            "5750 ─ パラボリック天井",
            "4236 ─ SL / V1 TPゾーン",
            "4164 ─ 建値",
            "4100 ─ 小足場（割れで加速）",
            "4000 ─ OCO指値TP",
            "3359 / 3137 ─ 次の支持",
        ],
        (229, 231, 235), (17, 24, 39), (100, 116, 139), f_head, f_body, width=460,
    )

    draw.text((40, 850), str(OUT), font=f_small, fill=(100, 116, 139))
    draw.text(
        (40, 872),
        "実スクショへ書込: python3 scripts/annotate_xauusd_d1_chart.py incoming/*.png ...",
        font=f_small,
        fill=(100, 116, 139),
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=95)
    print(f"Saved {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
