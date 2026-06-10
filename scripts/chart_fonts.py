"""Pillow 用日本語フォント解決（トレード日誌チャート注釈）。"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

# 日本語グリフを含むフォント（優先順）
JP_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def get_japanese_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """日本語表示可能な TrueType フォントを返す。見つからなければ例外。"""
    paths = list(JP_FONT_CANDIDATES)
    if bold:
        paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            *paths,
        ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError(
        "日本語フォントが見つかりません。"
        " sudo apt install fonts-wqy-microhei fonts-noto-cjk を実行してください。"
    )
