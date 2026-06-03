#!/usr/bin/env python3
"""Generate illustrative candlestick images for Market Psychology Atlas Vol.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT_DIR = Path(__file__).parent / "images"

# Prefer a CJK-capable font for Japanese labels
for _path in (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
):
    if Path(_path).exists():
        font_manager.fontManager.addfont(_path)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=_path).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

# Japanese chart convention: red = bullish, blue = bearish
BULL = "#d32f2f"
BEAR = "#1565c0"
WICK = "#37474f"
BG = "#fafafa"
GRID = "#eceff1"
ACCENT = "#ff6f00"
LABEL_BG = "#fff8e1"


@dataclass
class Annotation:
    x: float
    y: float
    text: str
    color: str = "#37474f"
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
    zones: list[tuple[float, float, str]] = field(default_factory=list)  # y0, y1, label


def draw_candlestick(ax, ohlc: list[tuple[float, float, float, float]]) -> None:
    width = 0.55
    for i, (o, h, l, c) in enumerate(ohlc):
        bull = c >= o
        color = BULL if bull else BEAR
        body_low = min(o, c)
        body_high = max(o, c)
        body_h = max(body_high - body_low, 0.08)
        ax.plot([i, i], [l, body_low], color=WICK, linewidth=1.2, zorder=2)
        ax.plot([i, i], [body_high, h], color=WICK, linewidth=1.2, zorder=2)
        ax.add_patch(
            Rectangle(
                (i - width / 2, body_low),
                width,
                body_h,
                facecolor=color,
                edgecolor=color,
                linewidth=0.8,
                zorder=3,
            )
        )


def render(chart: PatternChart, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    lows = [x[2] for x in chart.ohlc]
    highs = [x[1] for x in chart.ohlc]
    y_min, y_max = min(lows) - 0.8, max(highs) + 1.2
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(-0.8, len(chart.ohlc) - 0.2)

    for y0, y1, label in chart.zones:
        ax.axhspan(y0, y1, color="#e3f2fd", alpha=0.55, zorder=0)
        ax.text(
            len(chart.ohlc) - 0.5,
            (y0 + y1) / 2,
            label,
            fontsize=8,
            color="#1565c0",
            va="center",
            ha="right",
            bbox=dict(boxstyle="round,pad=0.25", fc=LABEL_BG, ec="#ffe082", alpha=0.9),
        )

    for level, label in chart.hlines:
        ax.axhline(level, color="#78909c", linestyle="--", linewidth=1.0, alpha=0.8)
        ax.text(
            -0.55,
            level,
            label,
            fontsize=8,
            color="#546e7a",
            va="center",
            ha="right",
        )

    draw_candlestick(ax, chart.ohlc)

    for ann in chart.annotations:
        ax.text(
            ann.x,
            ann.y,
            ann.text,
            fontsize=ann.fontsize,
            color=ann.color,
            ha=ann.ha,
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cfd8dc", alpha=0.95),
            zorder=5,
        )
        if ann.arrow_to:
            ax.annotate(
                "",
                xy=ann.arrow_to,
                xytext=(ann.x, ann.y - 0.05),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4),
                zorder=5,
            )

    ax.set_title(f"{chart.pattern_id}  {chart.title}", fontsize=14, fontweight="bold", pad=12)
    ax.text(
        0.01,
        0.98,
        chart.emotion,
        transform=ax.transAxes,
        fontsize=10,
        color=ACCENT,
        va="top",
        bbox=dict(boxstyle="round,pad=0.35", fc=LABEL_BG, ec="#ffcc80"),
    )
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor=BG)
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
            (15.9, 16.0, 14.5, 14.8),  # capitulation wick
            (14.8, 15.6, 14.7, 15.4),
            (15.4, 16.2, 15.3, 16.0),
            (16.0, 16.8, 15.9, 16.6),
            (16.6, 17.2, 16.5, 17.0),
        ],
        annotations=[
            Annotation(4, 13.8, "長い下ヒゲ\n最後の投げ", ACCENT, arrow_to=(4, 14.5)),
            Annotation(1, 18.6, "左肩起点", "#546e7a", arrow_to=(1, 18.0)),
            Annotation(7, 17.5, "回収・踏み上げ", BULL, arrow_to=(7, 16.8)),
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
            (12.2, 13.2, 12.1, 13.0),  # break
            (13.0, 13.1, 12.0, 12.2),  # denial close inside
            (12.2, 12.3, 11.5, 11.6),
            (11.6, 11.8, 11.0, 11.1),
        ],
        annotations=[
            Annotation(3, 13.5, "期待先行\n「抜けた!」", ACCENT, arrow_to=(3, 13.0)),
            Annotation(4, 12.6, "終値で否定\n→ 後悔", BEAR, arrow_to=(4, 12.2)),
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
            Annotation(5, 11.2, "上も下も\n説明がつく", "#546e7a"),
            Annotation(10, 9.2, "新規参加が止まる", "#546e7a"),
        ],
    ),
    PatternChart(
        "04",
        "損失回収モード",
        "主感情: 回収欲求 ｜ 負け側が需給を支える",
        [
            (16, 16.1, 15.2, 15.3),
            (15.3, 15.5, 14.5, 14.6),
            (14.6, 15.2, 14.4, 15.0),  # weak bounce
            (15.0, 15.1, 14.2, 14.3),
            (14.3, 14.9, 14.1, 14.7),
            (14.7, 14.8, 13.8, 13.9),
            (13.9, 14.4, 13.7, 14.2),
            (14.2, 14.3, 13.3, 13.4),
        ],
        annotations=[
            Annotation(2, 15.5, "戻り売り\n(損失回収)", BEAR),
            Annotation(4, 15.2, "高値更新\n失敗", ACCENT, arrow_to=(4, 14.9)),
            Annotation(6, 14.6, "燃料が尽きる", "#546e7a"),
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
            (11.8, 12.1, 11.0, 11.5),  # wick hold
            (11.5, 11.7, 10.9, 11.2),  # wick hold
            (11.2, 11.4, 10.8, 11.0),  # weaker
            (11.0, 11.1, 10.2, 10.3),  # close break
            (10.3, 10.4, 9.5, 9.6),
        ],
        annotations=[
            Annotation(3, 10.6, "ヒゲだけで\n「まだ大丈夫」", "#546e7a", arrow_to=(3, 11.0)),
            Annotation(6, 9.8, "終値割れ\n→ 清算", ACCENT, arrow_to=(6, 10.2)),
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
            (12.3, 12.9, 12.1, 12.6),  # upper wick grows
            (12.6, 13.2, 12.4, 12.8),
        ],
        annotations=[
            Annotation(1, 11.3, "浅い押し目なし", BULL),
            Annotation(5, 13.2, "上ヒゲ増加\n不安のサイン", ACCENT, arrow_to=(5, 12.9)),
            Annotation(3, 12.3, "高値更新連発", BULL),
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
            (11.4, 11.5, 10.0, 10.2),  # sharp reversal
            (10.2, 10.3, 9.2, 9.3),
        ],
        annotations=[
            Annotation(5, 11.8, "「正しいはず」\nと耐える", "#546e7a"),
            Annotation(7, 11.8, "限界→一斉投げ", ACCENT, arrow_to=(7, 10.5)),
        ],
    ),
    PatternChart(
        "08",
        "静寂の蓄圧",
        "主感情: 無関心→期待 ｜ 退屈の後に急拡大",
        [(10 + (i % 3) * 0.05, 10.25, 9.75, 10 + (i % 2) * 0.1) for i in range(14)]
        + [
            (10.1, 11.5, 10.0, 11.3),  # expansion bar
            (11.3, 12.0, 11.1, 11.8),
        ],
        zones=[(9.7, 10.3, "ATR低下\n参加者離脱")],
        annotations=[
            Annotation(6, 10.6, "誰も見ていない", "#546e7a"),
            Annotation(14, 12.0, "TR急拡大\nブレイク", ACCENT, arrow_to=(14, 11.3)),
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
            (13.5, 13.6, 12.5, 12.8),  # test 1
            (12.8, 13.0, 11.8, 12.0),
            (12.0, 12.1, 10.5, 11.2),  # capitulation long wick
            (11.2, 12.0, 11.1, 11.8),
            (11.8, 12.6, 11.7, 12.4),
        ],
        annotations=[
            Annotation(5, 12.0, "2度目の底値\nテスト", "#546e7a", arrow_to=(5, 12.8)),
            Annotation(7, 10.0, "最後の投げ\n長い下ヒゲ", ACCENT, arrow_to=(7, 10.5)),
            Annotation(9, 13.0, "反転確認", BULL, arrow_to=(9, 12.4)),
        ],
    ),
    PatternChart(
        "10",
        "休眠節目の覚醒",
        "主感情: 期待 ｜ 長く触れなかった節目を超える",
        [(11.5, 11.8, 11.2, 11.4) for _ in range(8)]
        + [
            (11.4, 12.5, 11.3, 12.3),  # awakening break
            (12.3, 12.4, 11.8, 12.0),
            (12.0, 12.2, 11.7, 12.1),
            (12.1, 12.8, 12.0, 12.7),  # shelf break
        ],
        hlines=[(12.0, "休眠高値\n(360本)"), (12.2, "棚高値")],
        annotations=[
            Annotation(3, 12.2, "長期間\n触れない", "#546e7a"),
            Annotation(8, 12.8, "覚醒\n初回更新", ACCENT, arrow_to=(8, 12.3)),
            Annotation(11, 13.1, "棚→再ブレイク", BULL, arrow_to=(11, 12.7)),
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
            (13.0, 13.5, 12.8, 13.3),  # no new low
            (13.3, 14.0, 13.2, 13.8),
            (13.8, 14.5, 13.7, 14.3),
            (14.3, 15.0, 14.2, 14.8),
        ],
        annotations=[
            Annotation(1, 16.4, "左肩", "#546e7a", arrow_to=(1, 15.8)),
            Annotation(4, 12.2, "安値更新\n停止", ACCENT, arrow_to=(4, 12.8)),
            Annotation(7, 15.3, "続落期待\n崩壊", BULL, arrow_to=(7, 14.8)),
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
            (12.5, 13.2, 12.3, 12.7),  # upper wick chase bar
            (12.7, 12.9, 12.0, 12.2),
        ],
        annotations=[
            Annotation(0, 10.9, "最初は\n見送り", "#546e7a"),
            Annotation(4, 13.0, "5本連続\n高値更新", BULL),
            Annotation(5, 13.5, "遅れて来た\n買い＋上ヒゲ", ACCENT, arrow_to=(5, 13.0)),
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
