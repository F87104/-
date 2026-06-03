# 実OHLCチャート — セットアップと再生成

## クイックスタート（F87104_test がある場合）

```bash
# 1. リポジトリ直下に F87104_test/ を配置
# 2. ワンコマンド再生成
chmod +x scripts/regenerate_atlas_real.sh
./scripts/regenerate_atlas_real.sh
```

2015年〜の H1 CSV から H4 にリサンプルし、12心理パターンをスキャン → TradingView 風 PNG を出力します。

---

## いま GitHub 上にあるもの

- **実OHLCギャラリー:** [real_gallery.md](real_gallery.md)
- **12枚の PNG:** [images/real/](images/real/)
- **イベント一覧:** [real_events_manifest.json](real_events_manifest.json)

クラウド環境では **yfinance（直近約2年）** で生成した版が入っています。  
**あなたの PC で `F87104_test` を使って再生成すると、2015年〜の長期版に差し替わります。**

---

## フォルダ配置

```
FX-AI/
├── F87104_test/          ← ここ（gitignore 済み、GitHub には載せない）
│   ├── XAUUSD2014-2024/XAUUSD_H1_*.csv
│   ├── USDJPY2014-2024/USDJPY_H1_*.csv
│   └── ...
├── scripts/
│   └── regenerate_atlas_real.sh   ← ワンコマンド
└── docs/research/市場心理図鑑/
```

---

## 手動コマンド

```bash
pip install matplotlib yfinance pandas

# F87104_test 必須（yfinance フォールバックなし）
python3 docs/research/市場心理図鑑/render_real_events.py \
  --data-root ./F87104_test \
  --require-local

# データパスを環境変数で指定
export F87104_DATA_ROOT=/path/to/F87104_test
./scripts/regenerate_atlas_real.sh
```

### 出力

| ファイル | 内容 |
|---|---|
| `images/real/*.png` | 12パターン TradingView 風チャート |
| `real_events_manifest.json` | データソース・通貨・時刻・スコア |
| `real_gallery.md` | ギャラリー（自動更新） |

---

## GitHub へ反映

再生成後:

```bash
git add docs/research/市場心理図鑑/images/real/ \
        docs/research/市場心理図鑑/real_gallery.md \
        docs/research/市場心理図鑑/real_events_manifest.json
git commit -m "Regenerate atlas real OHLC charts from F87104_test (2015-2024)"
git push
```

---

## 示意図との違い

| 種類 | フォルダ | データ |
|---|---|---|
| 示意図（教育用） | `images/01.png` 〜 | 合成 OHLC |
| **実OHLC** | `images/real/` | F87104_test または yfinance |

示意図の再生成:

```bash
python3 docs/research/市場心理図鑑/generate_charts.py
```
