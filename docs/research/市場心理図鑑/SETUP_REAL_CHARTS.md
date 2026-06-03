# 実OHLCチャート — セットアップと再生成

## いま GitHub 上にあるもの

- **実OHLCギャラリー:** [real_gallery.md](real_gallery.md)
- **12枚の PNG:** [images/real/](images/real/)
- **イベント一覧:** [real_events_manifest.json](real_events_manifest.json)

データがない環境では **yfinance（直近約2年の1H）** を H4 にリサンプルして生成しています。

---

## 2015年〜の長期データで再生成する（推奨）

リポジトリ直下に `F87104_test/` を置くと、バックテストと同じ OHLC が使われます。

```
FX-AI/
├── F87104_test/
│   ├── XAUUSD2014-2024/XAUUSD_H1_*.csv
│   ├── USDJPY2014-2024/USDJPY_H1_*.csv
│   └── ...
└── docs/research/市場心理図鑑/
```

### コマンド

```bash
pip install matplotlib yfinance pandas

# デフォルト（F87104_test があれば自動使用、なければ yfinance）
python3 docs/research/市場心理図鑑/render_real_events.py

# データパスを明示
python3 docs/research/市場心理図鑑/render_real_events.py \
  --data-root /path/to/F87104_test

# 通貨を指定
python3 docs/research/市場心理図鑑/render_real_events.py \
  --data-root ./F87104_test \
  --symbols XAUUSD USDJPY SILVER EURJPY
```

### 出力

| ファイル | 内容 |
|---|---|
| `images/real/*.png` | 12パターン分の TradingView 風チャート |
| `real_events_manifest.json` | 通貨・時刻・スコア |
| `real_gallery.md` | ギャラリー（自動更新） |

---

## 示意図との違い

| 種類 | フォルダ | データ |
|---|---|---|
| 示意図（教育用） | `images/01.png` 〜 | 合成 OHLC |
| **実OHLC** | `images/real/` | 市場データ |

再生成コマンド（示意図）:

```bash
python3 docs/research/市場心理図鑑/generate_charts.py
```
