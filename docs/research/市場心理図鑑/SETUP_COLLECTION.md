# パターンライブラリ — 収集ガイド

様々なチャートパターン（心理イベント）を **大量に抜き出して集める** ための手順。

## 出力先

```
docs/research/市場心理図鑑/collection/
├── index.md           ← ブラウズ用ギャラリー
├── manifest.json      ← 全メタデータ
├── events.csv         ← スプレッドシート用
└── images/
    ├── 01_売り方降伏/
    │   ├── USDJPY_20260127_0400.png
    │   └── ...
    ├── 02_期待先行/
    └── ...
```

## クイックスタート

```bash
pip install matplotlib yfinance pandas

# yfinance（直近2年）で各パターン最大10件ずつ収集
python3 docs/research/市場心理図鑑/collect_pattern_library.py

# F87104_test（2015年〜）で本格収集
./scripts/collect_atlas_patterns.sh
```

## オプション

| オプション | デフォルト | 説明 |
|---|---:|---|
| `--max-per-pattern` | 10 | パターンあたり最大件数 |
| `--max-per-symbol` | 3 | 通貨あたり最大件数 |
| `--min-gap` | 36 | 同一通貨でイベント間隔（H4本数） |
| `--patterns 01 02 11` | 全12 | 対象パターンを限定 |
| `--no-render` | off | カタログのみ（PNG省略） |
| `--require-local` | off | F87104_test 必須 |

### 例

```bash
# 売り方降伏だけ20件集める
python3 docs/research/市場心理図鑑/collect_pattern_library.py \
  --patterns 01 --max-per-pattern 20

# 全パターン、通貨ごと5件、合計15件/パターン
python3 docs/research/市場心理図鑑/collect_pattern_library.py \
  --max-per-symbol 5 --max-per-pattern 15 \
  --data-root ./F87104_test --require-local
```

## 代表1枚 vs ライブラリ

| 用途 | スクリプト | 出力 |
|---|---|---|
| 図鑑トップ用・代表例 | `render_real_events.py` | `images/real/` 12枚 |
| **パターン研究・大量収集** | `collect_pattern_library.py` | `collection/` |

## 本番収集（F87104_test / 2015年〜）

`./scripts/collect_atlas_patterns.sh` のデフォルト設定:

| 項目 | 値 |
|---|---:|
| パターンあたり最大 | 25 |
| 通貨あたり最大 | 8 |
| イベント間隔 | 24 H4本 |
| データ期間 | 2013〜2026（7通貨） |
| 合計 | 約278イベント |

> **08 静寂の蓄圧** は検出条件が厳しく、全期間スキャンでも約3件のみ。Vol.1 の定義を緩めるか Vol.2 で別条件を検討。

## GitHub へ反映

```bash
git add docs/research/市場心理図鑑/collection/
git commit -m "Update psychology pattern collection library"
git push
```

大量 PNG はリポジトリが肥大化するため、必要に応じて `--max-per-pattern` を調整してください。
