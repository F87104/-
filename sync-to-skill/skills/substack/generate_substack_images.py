#!/usr/bin/env python3
"""Generate images for Substack article: position surrender moment."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "position_surrender" / "images"
PATTERN_IMG = Path(__file__).resolve().parents[1] / "images"

for _path in (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
):
    if Path(_path).exists():
        font_manager.fontManager.addfont(_path)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=_path).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

TV = dict(
    BG="#131722",
    PANEL="#1e222d",
    TEXT="#d1d4dc",
    MUTED="#787b86",
    BULL="#26a69a",
    BEAR="#ef5350",
    ACCENT="#f7931a",
    LINE="#2962ff",
    SIGNAL="#e040fb",
)


def save(fig, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, facecolor=TV["BG"], edgecolor=TV["BG"], dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", path)
    return path


def hero() -> None:
    fig, ax = plt.subplots(figsize=(12, 6.3), facecolor=TV["BG"])
    ax.set_facecolor(TV["BG"])
    ax.axis("off")
    ax.text(0.5, 0.62, "ポジションを持っている人が", fontsize=28, color=TV["TEXT"], ha="center", fontweight="bold")
    ax.text(0.5, 0.48, "投げ出す瞬間", fontsize=34, color=TV["ACCENT"], ha="center", fontweight="bold")
    ax.text(0.5, 0.30, "市場心理図鑑 — 降伏の解剖", fontsize=14, color=TV["MUTED"], ha="center")
    ax.text(0.5, 0.14, "形ではなく、独白と需給を読む", fontsize=11, color=TV["MUTED"], ha="center")
    # decorative candles
    for i, (o, h, l, c, col) in enumerate(
        [
            (0.12, 0.22, 0.08, 0.18, TV["BEAR"]),
            (0.18, 0.20, 0.14, 0.19, TV["BEAR"]),
            (0.24, 0.21, 0.15, 0.20, TV["BULL"]),
            (0.30, 0.24, 0.19, 0.23, TV["BULL"]),
            (0.72, 0.20, 0.14, 0.19, TV["BEAR"]),
            (0.78, 0.18, 0.12, 0.17, TV["BEAR"]),
            (0.84, 0.19, 0.15, 0.18, TV["BULL"]),
        ]
    ):
        ax.plot([i], [l], "o", color=col, markersize=0.1)
        ax.plot([i, i], [l, min(o, c)], color=col, lw=2)
        ax.plot([i, i], [max(o, c), h], color=col, lw=2)
        ax.add_patch(Rectangle((i - 0.015, min(o, c)), 0.03, max(abs(c - o), 0.01), fc=col, ec=col))
    save(fig, "00_hero.png")


def four_stages() -> None:
    stages = [
        ("確信", "«分析は合っている»", TV["LINE"]),
        ("逆行", "«一時的な調整»", TV["MUTED"]),
        ("執着", "«まだ損切らない»", TV["ACCENT"]),
        ("疲弊", "«もう限界»", TV["BEAR"]),
        ("投げ", "«降りる»", TV["SIGNAL"]),
        ("反動", "«安堵の反対売買»", TV["BULL"]),
    ]
    fig, ax = plt.subplots(figsize=(12, 4.2), facecolor=TV["BG"])
    ax.set_facecolor(TV["BG"])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.text(0.1, 3.55, "投げの前に来る6段階", fontsize=16, color=TV["TEXT"], fontweight="bold")
    for i, (title, quote, color) in enumerate(stages):
        x = 0.5 + i * 1.9
        box = FancyBboxPatch(
            (x, 1.2), 1.6, 1.8, boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor=TV["PANEL"], edgecolor=color, linewidth=2,
        )
        ax.add_patch(box)
        ax.text(x + 0.8, 2.55, title, fontsize=13, color=color, ha="center", fontweight="bold")
        ax.text(x + 0.8, 1.85, quote, fontsize=8.5, color=TV["MUTED"], ha="center")
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + 1.65, 2.1), (x + 1.95, 2.1), arrowstyle="-|>", color=TV["MUTED"], lw=1.5))
    save(fig, "04_four_stages.png")


def three_types_summary() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), facecolor=TV["BG"])
    items = [
        ("ロングの投げ", "05→07", "現実否認→清算", "成行売り", TV["BEAR"]),
        ("ショートの投げ", "01 / 11", "売り方降伏", "買い戻し", TV["BULL"]),
        ("最後の信念者", "09", "心理底", "損切り売り", TV["SIGNAL"]),
    ]
    for ax, (title, pid, sub, order, color) in zip(axes, items):
        ax.set_facecolor(TV["PANEL"])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.02", fc=TV["PANEL"], ec=color, lw=2))
        ax.text(0.5, 0.78, title, fontsize=13, color=color, ha="center", fontweight="bold")
        ax.text(0.5, 0.62, pid, fontsize=11, color=TV["ACCENT"], ha="center")
        ax.text(0.5, 0.48, sub, fontsize=9, color=TV["TEXT"], ha="center")
        ax.text(0.5, 0.28, f"動く注文: {order}", fontsize=9, color=TV["MUTED"], ha="center")
    fig.suptitle("投げは3種類ある", fontsize=16, color=TV["TEXT"], fontweight="bold", y=0.98)
    save(fig, "02_three_types.png")


def copy_patterns() -> None:
    mapping = {
        "01.png": "chart_01_seller_surrender.png",
        "05.png": "chart_05_denial.png",
        "07.png": "chart_07_exhaustion.png",
        "09.png": "chart_09_last_believer.png",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for src, dst in mapping.items():
        shutil.copy(PATTERN_IMG / src, OUT / dst)
        print("copied", OUT / dst)


def usdjpy_case() -> None:
    import yfinance as yf
    import pandas as pd

    raw = yf.download("USDJPY=X", interval="1h", period="60d", progress=False, auto_adjust=True)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.columns = [str(c).lower() for c in raw.columns]
    h1 = raw[["open", "high", "low", "close"]].dropna()
    if h1.index.tz is not None:
        h1.index = h1.index.tz_convert("UTC").tz_localize(None)
    h4 = h1.resample("4h", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()
    chunk = h4[(h4.index >= "2026-04-25") & (h4.index <= "2026-06-05")]
    if len(chunk) < 20:
        chunk = h4.tail(90)

    fig = plt.figure(figsize=(13.5, 6.5), dpi=150, facecolor=TV["BG"])
    ax = fig.add_axes([0.07, 0.12, 0.82, 0.72])
    ax.set_facecolor(TV["BG"])
    n = len(chunk)
    width = 0.22 if n > 80 else 0.35
    for i, (_, row) in enumerate(chunk.iterrows()):
        o, h, l, c = row.open, row.high, row.low, row.close
        col = TV["BULL"] if c >= o else TV["BEAR"]
        bl, bh = min(o, c), max(o, c)
        bh = max(bh, bl + (h - l) * 0.04)
        ax.plot([i, i], [l, bl], color=col, lw=0.7)
        ax.plot([i, i], [bh, h], color=col, lw=0.7)
        ax.add_patch(Rectangle((i - width / 2, bl), width, bh - bl, fc=col, ec=col))

    ylo, yhi = chunk.low.min() * 0.998, chunk.high.max() * 1.002
    ax.set_ylim(ylo, yhi)
    ax.set_xlim(-1, n)
    ax.axhline(162.086, color=TV["ACCENT"], lw=1.2, alpha=0.9)
    ax.text(n - 1, 162.086, " 162.09 抵抗", fontsize=8, color=TV["ACCENT"], va="center")
    ax.axhline(160.0, color=TV["MUTED"], lw=0.8, ls="--", alpha=0.7)
    ax.text(n - 1, 160.0, " 160", fontsize=7, color=TV["MUTED"], va="center")

    crash_t = chunk.low.idxmin()
    crash_i = list(chunk.index).index(crash_t)
    ax.axvline(crash_i, color=TV["SIGNAL"], lw=1, ls=":", alpha=0.7)
    ax.text(crash_i, yhi - (yhi - ylo) * 0.05, "介入急落\nショート投げ", fontsize=8, color=TV["SIGNAL"], ha="center")

    for idx in [0, n // 3, 2 * n // 3, n - 1]:
        if 0 <= idx < n:
            ax.text(idx, ylo - (yhi - ylo) * 0.04, chunk.index[idx].strftime("%m/%d"), fontsize=7, color=TV["MUTED"], ha="center")

    tb = fig.add_axes([0, 0.88, 1, 0.12])
    tb.set_facecolor(TV["PANEL"])
    tb.axis("off")
    tb.text(0.03, 0.5, "USDJPY H4 — 2026年5月ケース", fontsize=12, color=TV["TEXT"], va="center", fontweight="bold")
    tb.text(0.98, 0.5, "急落 → ショート投げ → 回復 → 160攻防", fontsize=9, color=TV["MUTED"], va="center", ha="right")
    fig.text(0.07, 0.03, "実OHLC（yfinance）・ 緑=陽線 赤=陰線", fontsize=7.5, color=TV["MUTED"])
    save(fig, "05_usdjpy_case.png")


def real_vs_fake() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=TV["BG"])
    for ax, title, bullets, color in zip(
        axes,
        ["本物の投げに近い", "ただの反発"],
        [
            ["既存ポジションの解消", "ATR×2以上の活動量", "15〜30本の一方向偏り", "棚→再ブレイク"],
            ["新規の確信エントリー", "平均的な活動量", "レンジ内の動き", "すぐ元方向へ回帰"],
        ],
        [TV["BULL"], TV["BEAR"]],
    ):
        ax.set_facecolor(TV["PANEL"])
        ax.axis("off")
        ax.text(0.5, 0.88, title, fontsize=14, color=color, ha="center", fontweight="bold", transform=ax.transAxes)
        for j, b in enumerate(bullets):
            ax.text(0.08, 0.68 - j * 0.18, f"• {b}", fontsize=10, color=TV["TEXT"], transform=ax.transAxes)
    fig.suptitle("投げと反発の見分け", fontsize=15, color=TV["TEXT"], fontweight="bold", y=0.98)
    save(fig, "03_real_vs_fake.png")


def main() -> None:
    hero()
    four_stages()
    three_types_summary()
    real_vs_fake()
    copy_patterns()
    try:
        usdjpy_case()
    except Exception as e:
        print("usdjpy skip:", e)
    print(f"\nAll images in {OUT}")


if __name__ == "__main__":
    main()
