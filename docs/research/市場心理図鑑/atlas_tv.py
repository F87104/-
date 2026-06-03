"""TradingView-style chart renderer for Market Psychology Atlas."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
import pandas as pd

_FONT_READY = False


class TV:
    BG = "#131722"
    TOOLBAR = "#1e222d"
    GRID = "#363a45"
    TEXT = "#d1d4dc"
    MUTED = "#787b86"
    BULL = "#26a69a"
    BEAR = "#ef5350"
    ACCENT = "#f7931a"
    LINE = "#2962ff"
    LABEL_BG = "#2a2e39"
    LABEL_EDGE = "#434651"
    ZONE = "#2962ff"
    SIGNAL = "#e040fb"


@dataclass
class ChartAnnotation:
    x: float
    y: float
    text: str
    color: str = TV.TEXT
    fontsize: int = 9
    ha: str = "center"
    arrow_to: tuple[float, float] | None = None


@dataclass
class RealChartSpec:
    pattern_id: str
    title: str
    emotion: str
    symbol: str
    timeframe: str
    event_time: pd.Timestamp
    ohlc: pd.DataFrame
    signal_i: int
    annotations: list[ChartAnnotation] = field(default_factory=list)
    hlines: list[tuple[float, str]] = field(default_factory=list)
    zones: list[tuple[float, float, str]] = field(default_factory=list)


def setup_font() -> None:
    global _FONT_READY
    if _FONT_READY:
        return
    for path in (
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ):
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    _FONT_READY = True


def draw_candles(ax, ohlc: pd.DataFrame, width: float = 0.62) -> None:
    for i, row in enumerate(ohlc.itertuples()):
        o, h, l, c = float(row.open), float(row.high), float(row.low), float(row.close)
        bull = c >= o
        color = TV.BULL if bull else TV.BEAR
        body_low = min(o, c)
        body_high = max(o, c)
        body_h = max(body_high - body_low, (h - l) * 0.04)
        ax.plot([i, i], [l, body_low], color=color, linewidth=1.0, solid_capstyle="round", zorder=3)
        ax.plot([i, i], [body_high, h], color=color, linewidth=1.0, solid_capstyle="round", zorder=3)
        ax.add_patch(
            Rectangle(
                (i - width / 2, body_low),
                width,
                body_h,
                facecolor=color,
                edgecolor=color,
                linewidth=0,
                zorder=4,
            )
        )


def _price_ticks(y_min: float, y_max: float, n: int = 6) -> list[float]:
    step = (y_max - y_min) / max(n - 1, 1)
    return [y_min + step * i for i in range(n)]


def render_real_chart(spec: RealChartSpec, out_path: Path) -> None:
    setup_font()
    ohlc = spec.ohlc.reset_index(drop=True)
    n = len(ohlc)

    fig = plt.figure(figsize=(11, 6.2), dpi=150, facecolor=TV.BG)
    toolbar_h = 0.09
    ax = fig.add_axes([0.07, 0.11, 0.76, 0.76])
    ax.set_facecolor(TV.BG)

    lows = ohlc["low"].astype(float)
    highs = ohlc["high"].astype(float)
    pad = (highs.max() - lows.min()) * 0.12
    y_min, y_max = float(lows.min() - pad), float(highs.max() + pad)
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(-0.8, n - 0.2)

    tb = fig.add_axes([0, 1 - toolbar_h, 1, toolbar_h])
    tb.set_facecolor(TV.TOOLBAR)
    tb.axis("off")
    ts = spec.event_time.strftime("%Y-%m-%d %H:%M")
    tb.text(0.02, 0.55, "市場心理図鑑", fontsize=11, color=TV.TEXT, va="center", fontweight="bold")
    tb.text(0.13, 0.55, "·", fontsize=11, color=TV.MUTED, va="center")
    tb.text(0.145, 0.55, f"{spec.symbol} {spec.timeframe}", fontsize=10, color=TV.MUTED, va="center")
    tb.text(0.28, 0.55, "·", fontsize=11, color=TV.MUTED, va="center")
    tb.text(0.295, 0.55, f"{spec.pattern_id}  {spec.title}", fontsize=11, color=TV.ACCENT, va="center")
    tb.text(0.98, 0.55, spec.emotion, fontsize=8.5, color=TV.MUTED, va="center", ha="right")

    for tick in _price_ticks(y_min, y_max, 6):
        ax.axhline(tick, color=TV.GRID, linewidth=0.6, alpha=0.55, zorder=0)

    for y0, y1, label in spec.zones:
        ax.axhspan(y0, y1, color=TV.ZONE, alpha=0.10, zorder=1)
        ax.text(
            n - 0.2,
            (y0 + y1) / 2,
            label,
            fontsize=8,
            color=TV.LINE,
            va="center",
            ha="right",
            bbox=dict(boxstyle="round,pad=0.28", fc=TV.LABEL_BG, ec=TV.LABEL_EDGE, alpha=0.95),
            zorder=6,
        )

    for level, label in spec.hlines:
        ax.axhline(level, color=TV.LINE, linewidth=1.2, alpha=0.85, zorder=2)
        ax.text(
            n - 0.05,
            level,
            f"  {label}",
            fontsize=7,
            color="white",
            va="center",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.18", fc=TV.LINE, ec=TV.LINE, alpha=0.95),
            zorder=6,
        )

    draw_candles(ax, ohlc)

    if 0 <= spec.signal_i < n:
        ax.axvline(spec.signal_i, color=TV.SIGNAL, linewidth=1.0, alpha=0.55, linestyle=":", zorder=5)
        ax.text(
            spec.signal_i,
            y_max - pad * 0.15,
            "EVENT",
            fontsize=7,
            color=TV.SIGNAL,
            ha="center",
            va="top",
            rotation=90,
        )

    for ann in spec.annotations:
        ax.text(
            ann.x,
            ann.y,
            ann.text,
            fontsize=ann.fontsize,
            color=ann.color,
            ha=ann.ha,
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.32", fc=TV.LABEL_BG, ec=TV.LABEL_EDGE, alpha=0.96),
            zorder=7,
        )
        if ann.arrow_to:
            ax.annotate(
                "",
                xy=ann.arrow_to,
                xytext=(ann.x, ann.y - (y_max - y_min) * 0.015),
                arrowprops=dict(arrowstyle="-|>", color=TV.ACCENT, lw=1.5),
                zorder=7,
            )

    ax_r = fig.add_axes([0.85, 0.11, 0.11, 0.76])
    ax_r.set_facecolor(TV.BG)
    ax_r.set_ylim(y_min, y_max)
    ax_r.set_xticks([])
    for tick in _price_ticks(y_min, y_max, 6):
        ax_r.axhline(tick, color=TV.GRID, linewidth=0.6, alpha=0.55)
        fmt = f"{tick:.2f}" if tick < 1000 else f"{tick:.1f}"
        ax_r.text(0.05, tick, fmt, fontsize=7.5, color=TV.MUTED, va="center")
    for spine in ax_r.spines.values():
        spine.set_visible(False)
    ax_r.tick_params(left=False, labelleft=False)

    # sparse datetime labels
    tick_idx = sorted({0, n // 2, n - 1, spec.signal_i})
    for idx in tick_idx:
        if 0 <= idx < len(spec.ohlc):
            dt = spec.ohlc.index[idx]
            if hasattr(dt, "strftime"):
                ax.text(idx, y_min - pad * 0.35, dt.strftime("%m/%d"), fontsize=7, color=TV.MUTED, ha="center")

    fig.text(
        0.07,
        0.03,
        f"実OHLC  ·  {spec.symbol} {spec.timeframe}  ·  イベント {ts}  ·  緑=陽線 赤=陰線",
        fontsize=7.5,
        color=TV.MUTED,
    )

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=TV.BG, edgecolor=TV.BG)
    plt.close(fig)
