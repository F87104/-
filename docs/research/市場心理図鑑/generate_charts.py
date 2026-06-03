#!/usr/bin/env python3
"""Generate TradingView-style illustrative candlestick images for Market Psychology Atlas."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

OUT_DIR = Path(__file__).parent / "images"

for _path in (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
):
    if Path(_path).exists():
        font_manager.fontManager.addfont(_path)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=_path).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False


class TV:
    """TradingView dark theme palette."""

    BG = "#131722"
    TOOLBAR = "#1e222d"
    PANEL = "#2a2e39"
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


@dataclass
class Annotation:
    x: float
    y: float
    text: str
    color: str = TV.TEXT
    fontsize: int = 9
    ha: str = "center"
    arrow_to: tuple[float, float] | None = None


@dataclass
class PatternChart:
    pattern_id: str
    title: str
    emotion: str
    ohlc: list[tuple[float, float, float, float]]
    annotations: list[Annotation] = field(default_factory=list)
    hlines: list[tuple[float, str]] = field(default_factory=list)
    zones: list[tuple[float, float, str]] = field(default_factory=list)


def draw_candlestick(ax, ohlc: list[tuple[float, float, float, float]]) -> None:
    n = len(ohlc)
    width = 0.52 if n <= 16 else (0.46 if n <= 24 else 0.40)
    for i, (o, h, l, c) in enumerate(ohlc):
        bull = c >= o
        color = TV.BULL if bull else TV.BEAR
        body_low = min(o, c)
        body_high = max(o, c)
        body_h = max(body_high - body_low, 0.06)
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


def _price_ticks(y_min: float, y_max: float, n: int = 5) -> list[float]:
    step = (y_max - y_min) / (n - 1)
    return [y_min + step * i for i in range(n)]


def render(chart: PatternChart, out_path: Path) -> None:
    fig_w, fig_h = 10.5, 6.0
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150, facecolor=TV.BG)

    # TradingView-like layout: toolbar + chart + right price scale
    toolbar_h = 0.09
    ax = fig.add_axes([0.06, 0.10, 0.78, 0.78])
    ax.set_facecolor(TV.BG)

    lows = [x[2] for x in chart.ohlc]
    highs = [x[1] for x in chart.ohlc]
    y_min, y_max = min(lows) - 0.9, max(highs) + 1.4
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(-0.9, len(chart.ohlc) - 0.1)

    # Toolbar strip
    tb = fig.add_axes([0, 1 - toolbar_h, 1, toolbar_h])
    tb.set_facecolor(TV.TOOLBAR)
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    tb.axis("off")
    tb.text(0.02, 0.55, "市場心理図鑑", fontsize=11, color=TV.TEXT, va="center", fontweight="bold")
    tb.text(0.14, 0.55, "·", fontsize=11, color=TV.MUTED, va="center")
    tb.text(0.155, 0.55, "H4", fontsize=10, color=TV.MUTED, va="center")
    tb.text(0.19, 0.55, "·", fontsize=11, color=TV.MUTED, va="center")
    tb.text(0.205, 0.55, f"{chart.pattern_id}  {chart.title}", fontsize=11, color=TV.ACCENT, va="center")
    tb.text(0.98, 0.55, chart.emotion, fontsize=8.5, color=TV.MUTED, va="center", ha="right")

    # Grid (horizontal only, TV style)
    for tick in _price_ticks(y_min, y_max, 6):
        ax.axhline(tick, color=TV.GRID, linewidth=0.6, alpha=0.55, zorder=0)

    # Zone boxes
    for y0, y1, label in chart.zones:
        ax.axhspan(y0, y1, color=TV.ZONE, alpha=0.10, zorder=1)
        ax.axhline(y0, color=TV.ZONE, linewidth=0.8, alpha=0.35, zorder=1)
        ax.axhline(y1, color=TV.ZONE, linewidth=0.8, alpha=0.35, zorder=1)
        ax.text(
            len(chart.ohlc) - 0.15,
            (y0 + y1) / 2,
            label,
            fontsize=8,
            color=TV.LINE,
            va="center",
            ha="right",
            bbox=dict(boxstyle="round,pad=0.28", fc=TV.LABEL_BG, ec=TV.LABEL_EDGE, alpha=0.95),
            zorder=6,
        )

    # Horizontal levels (TradingView line + price tag)
    for level, label in chart.hlines:
        ax.axhline(level, color=TV.LINE, linewidth=1.2, alpha=0.85, zorder=2)
        ax.text(
            len(chart.ohlc) - 0.02,
            level,
            f"  {label}",
            fontsize=7,
            color="white",
            va="center",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.18", fc=TV.LINE, ec=TV.LINE, alpha=0.95),
            zorder=6,
        )

    draw_candlestick(ax, chart.ohlc)

    # Annotations
    for ann in chart.annotations:
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
                xytext=(ann.x, ann.y - 0.06),
                arrowprops=dict(arrowstyle="-|>", color=TV.ACCENT, lw=1.5, shrinkA=2, shrinkB=2),
                zorder=7,
            )

    # Right price scale
    ax_r = fig.add_axes([0.86, 0.10, 0.10, 0.78])
    ax_r.set_facecolor(TV.BG)
    ax_r.set_ylim(y_min, y_max)
    ax_r.set_xlim(0, 1)
    ax_r.set_xticks([])
    for tick in _price_ticks(y_min, y_max, 6):
        ax_r.axhline(tick, color=TV.GRID, linewidth=0.6, alpha=0.55)
        ax_r.text(0.05, tick, f"{tick:.2f}", fontsize=7.5, color=TV.MUTED, va="center")
    for spine in ax_r.spines.values():
        spine.set_visible(False)
    ax_r.tick_params(left=False, labelleft=False)

    # Bottom legend
    fig.text(
        0.06,
        0.03,
        "TradingView style  ·  "
        f"{chart.pattern_id} {chart.title}  ·  "
        "緑=陽線  赤=陰線  ·  示意図（教育用）",
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


PATTERNS: list[PatternChart] = [
    PatternChart(
        "01",
        "売り方降伏",
        "主感情: 降伏 ｜ ショートの損切り連鎖",
        [
            (18, 18.2, 17.8, 17.9),
            (17.9, 18.0, 17.2, 17.3),
            (17.3, 17.4, 16.5, 16.6),
            (16.6, 16.7, 15.8, 15.9),
            (15.9, 16.0, 14.5, 14.8),
            (14.8, 15.6, 14.7, 15.4),
            (15.4, 16.2, 15.3, 16.0),
            (16.0, 16.8, 15.9, 16.6),
            (16.6, 17.2, 16.5, 17.0),
        ],
        annotations=[
            Annotation(4, 13.8, "長い下ヒゲ\n最後の投げ", TV.ACCENT, arrow_to=(4, 14.5)),
            Annotation(1, 18.6, "左肩起点", TV.MUTED, arrow_to=(1, 18.0)),
            Annotation(7, 17.5, "回収・踏み上げ", TV.BULL, arrow_to=(7, 16.8)),
        ],
        hlines=[(18.0, "左肩")],
    ),
    PatternChart(
        "02",
        "期待先行",
        "主感情: 期待→後悔 ｜ 飛び乗り層が閉じ込められる",
        [
            (12, 12.3, 11.8, 12.1),
            (12.1, 12.4, 11.9, 12.0),
            (12.0, 12.3, 11.7, 12.2),
            (12.2, 13.2, 12.1, 13.0),
            (13.0, 13.1, 12.0, 12.2),
            (12.2, 12.3, 11.5, 11.6),
            (11.6, 11.8, 11.0, 11.1),
        ],
        annotations=[
            Annotation(3, 13.5, "期待先行\n「抜けた!」", TV.ACCENT, arrow_to=(3, 13.0)),
            Annotation(4, 12.6, "終値で否定\n→ 後悔", TV.BEAR, arrow_to=(4, 12.2)),
        ],
        hlines=[(12.8, "節目")],
    ),
    PatternChart(
        "03",
        "市場の迷い",
        "主感情: 迷い ｜ 参加者が決断を先延ばし",
        [(10 + i * 0.02, 10.4, 9.6, 10 + (i % 2) * 0.15) for i in range(12)],
        zones=[(9.5, 10.5, "小さなレンジ\nBB収縮")],
        annotations=[
            Annotation(5, 11.2, "上も下も\n説明がつく", TV.MUTED),
            Annotation(10, 9.2, "新規参加が止まる", TV.MUTED),
        ],
    ),
    PatternChart(
        "04",
        "損失回収モード",
        "主感情: 回収欲求 ｜ 負け側が需給を支える",
        [
            (16, 16.1, 15.2, 15.3),
            (15.3, 15.5, 14.5, 14.6),
            (14.6, 15.2, 14.4, 15.0),
            (15.0, 15.1, 14.2, 14.3),
            (14.3, 14.9, 14.1, 14.7),
            (14.7, 14.8, 13.8, 13.9),
            (13.9, 14.4, 13.7, 14.2),
            (14.2, 14.3, 13.3, 13.4),
        ],
        annotations=[
            Annotation(2, 15.5, "戻り売り\n(損失回収)", TV.BEAR),
            Annotation(4, 15.2, "高値更新\n失敗", TV.ACCENT, arrow_to=(4, 14.9)),
            Annotation(6, 14.6, "燃料が尽きる", TV.MUTED),
        ],
    ),
    PatternChart(
        "05",
        "現実否認",
        "主感情: 執着→降伏 ｜ ヒゲだけで守る→終値割れ",
        [
            (10, 10.8, 9.9, 10.6),
            (10.6, 11.5, 10.5, 11.3),
            (11.3, 12.0, 11.2, 11.8),
            (11.8, 12.1, 11.0, 11.5),
            (11.5, 11.7, 10.9, 11.2),
            (11.2, 11.4, 10.8, 11.0),
            (11.0, 11.1, 10.2, 10.3),
            (10.3, 10.4, 9.5, 9.6),
        ],
        annotations=[
            Annotation(3, 10.6, "ヒゲだけで\n「まだ大丈夫」", TV.MUTED, arrow_to=(3, 11.0)),
            Annotation(6, 9.8, "終値割れ\n→ 清算", TV.ACCENT, arrow_to=(6, 10.2)),
        ],
        hlines=[(11.0, "pivot")],
    ),
    PatternChart(
        "06",
        "利益取り逃し恐怖",
        "主感情: 利益防衛→期待 ｜ 利確した人が再参加",
        [
            (10, 10.5, 9.9, 10.4),
            (10.4, 11.0, 10.3, 10.9),
            (10.9, 11.5, 10.8, 11.4),
            (11.4, 12.0, 11.3, 11.9),
            (11.9, 12.5, 11.8, 12.3),
            (12.3, 12.9, 12.1, 12.6),
            (12.6, 13.2, 12.4, 12.8),
        ],
        annotations=[
            Annotation(1, 11.3, "浅い押し目なし", TV.BULL),
            Annotation(5, 13.2, "上ヒゲ増加\n不安のサイン", TV.ACCENT, arrow_to=(5, 12.9)),
            Annotation(3, 12.3, "高値更新連発", TV.BULL),
        ],
    ),
    PatternChart(
        "07",
        "正解待ち疲弊",
        "主感情: 執着→降伏 ｜ 片側参加者の限界",
        [
            (8, 8.5, 7.9, 8.4),
            (8.4, 9.0, 8.3, 8.9),
            (8.9, 9.5, 8.8, 9.4),
            (9.4, 10.0, 9.3, 9.9),
            (9.9, 10.5, 9.8, 10.4),
            (10.4, 11.0, 10.3, 10.9),
            (10.9, 11.5, 10.8, 11.4),
            (11.4, 11.5, 10.0, 10.2),
            (10.2, 10.3, 9.2, 9.3),
        ],
        annotations=[
            Annotation(5, 11.8, "「正しいはず」\nと耐える", TV.MUTED),
            Annotation(7, 11.8, "限界→一斉投げ", TV.ACCENT, arrow_to=(7, 10.5)),
        ],
    ),
    PatternChart(
        "08",
        "静寂の蓄圧",
        "主感情: 無関心→期待 ｜ 退屈の後に急拡大",
        [(10 + (i % 3) * 0.05, 10.25, 9.75, 10 + (i % 2) * 0.1) for i in range(14)]
        + [(10.1, 11.5, 10.0, 11.3), (11.3, 12.0, 11.1, 11.8)],
        zones=[(9.7, 10.3, "ATR低下\n参加者離脱")],
        annotations=[
            Annotation(6, 10.6, "誰も見ていない", TV.MUTED),
            Annotation(14, 12.0, "TR急拡大\nブレイク", TV.ACCENT, arrow_to=(14, 11.3)),
        ],
    ),
    PatternChart(
        "09",
        "最後の信念者",
        "主感情: 希望→降伏 ｜ 心理底＝売る人がいなくなった瞬間",
        [
            (18, 18.1, 17.0, 17.1),
            (17.1, 17.2, 16.0, 16.1),
            (16.1, 16.2, 15.0, 15.1),
            (15.1, 15.2, 14.0, 14.2),
            (14.2, 14.3, 13.2, 13.5),
            (13.5, 13.6, 12.5, 12.8),
            (12.8, 13.0, 11.8, 12.0),
            (12.0, 12.1, 10.5, 11.2),
            (11.2, 12.0, 11.1, 11.8),
            (11.8, 12.6, 11.7, 12.4),
        ],
        annotations=[
            Annotation(5, 12.0, "2度目の底値\nテスト", TV.MUTED, arrow_to=(5, 12.8)),
            Annotation(7, 10.0, "最後の投げ\n長い下ヒゲ", TV.ACCENT, arrow_to=(7, 10.5)),
            Annotation(9, 13.0, "反転確認", TV.BULL, arrow_to=(9, 12.4)),
        ],
    ),
    PatternChart(
        "10",
        "休眠節目の覚醒",
        "主感情: 期待 ｜ 長く触れなかった節目を超える",
        [(11.5, 11.8, 11.2, 11.4) for _ in range(8)]
        + [(11.4, 12.5, 11.3, 12.3), (12.3, 12.4, 11.8, 12.0), (12.0, 12.2, 11.7, 12.1), (12.1, 12.8, 12.0, 12.7)],
        hlines=[(12.0, "休眠高値"), (12.2, "棚高値")],
        annotations=[
            Annotation(3, 12.2, "長期間\n触れない", TV.MUTED),
            Annotation(8, 12.8, "覚醒\n初回更新", TV.ACCENT, arrow_to=(8, 12.3)),
            Annotation(11, 13.1, "棚→再ブレイク", TV.BULL, arrow_to=(11, 12.7)),
        ],
    ),
    PatternChart(
        "11",
        "続落期待の崩壊",
        "主感情: 期待→降伏 ｜ 「まだ下がるはず」が裏切られる",
        [
            (16, 16.1, 15.0, 15.1),
            (15.1, 15.2, 14.0, 14.1),
            (14.1, 14.2, 13.0, 13.2),
            (13.2, 13.4, 12.5, 13.0),
            (13.0, 13.5, 12.8, 13.3),
            (13.3, 14.0, 13.2, 13.8),
            (13.8, 14.5, 13.7, 14.3),
            (14.3, 15.0, 14.2, 14.8),
        ],
        annotations=[
            Annotation(1, 16.4, "左肩", TV.MUTED, arrow_to=(1, 15.8)),
            Annotation(4, 12.2, "安値更新\n停止", TV.ACCENT, arrow_to=(4, 12.8)),
            Annotation(7, 15.3, "続落期待\n崩壊", TV.BULL, arrow_to=(7, 14.8)),
        ],
        hlines=[(15.5, "左肩起点")],
    ),
    PatternChart(
        "12",
        "見送り後悔",
        "主感情: 後悔→期待 ｜ 見送った人が中盤で飛び乗る",
        [
            (10, 10.6, 9.9, 10.5),
            (10.5, 11.1, 10.4, 11.0),
            (11.0, 11.6, 10.9, 11.5),
            (11.5, 12.1, 11.4, 12.0),
            (12.0, 12.6, 11.9, 12.5),
            (12.5, 13.2, 12.3, 12.7),
            (12.7, 12.9, 12.0, 12.2),
        ],
        annotations=[
            Annotation(0, 10.9, "最初は\n見送り", TV.MUTED),
            Annotation(4, 13.0, "5本連続\n高値更新", TV.BULL),
            Annotation(5, 13.5, "遅れて来た\n買い＋上ヒゲ", TV.ACCENT, arrow_to=(5, 13.0)),
        ],
    ),
]


def main() -> None:
    for chart in PATTERNS:
        out = OUT_DIR / f"{chart.pattern_id}.png"
        render(chart, out)
        print(f"saved: {out}")


if __name__ == "__main__":
    main()
