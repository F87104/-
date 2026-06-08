# 億勝ちFX スライド

書籍『億勝ちFX 10年負け続けた凡人がたどり着いた「型と戦略」』（投資家メンタリスト Sai 著, KADOKAWA, 2026）に基づくスライド資料。

## スライド一覧

| ファイル | 内容 | 枚数 |
|----------|------|------|
| `kate-nai-riyuu-simple.md` | **勝てない理由は驚くほど単純**（序章要点） | 約15枚 |
| `oku-gachi-fx.md` | 全章サマリー版（別ブランチ `cursor/book-to-slides-27ba`） | 77枚 |

## ビルド方法

```bash
cd slides
npm install

# HTML
npx marp kate-nai-riyuu-simple.md --no-stdin -o kate-nai-riyuu-simple.html

# PDF
npx marp kate-nai-riyuu-simple.md --no-stdin --pdf --allow-local-files -o kate-nai-riyuu-simple.pdf

# PowerPoint
npx marp kate-nai-riyuu-simple.md --no-stdin --pptx --allow-local-files -o kate-nai-riyuu-simple.pptx
```

## 原著 PDF

著者より依頼のあった原著 PDF はリポジトリ直下に含まれています。

- `億勝ちFX _最終チェック1218のコピー.pdf`

## 注意事項

- スライドは原著の要点を整理した学習用資料です。
- 詳細・チャート図解は原著をご参照ください。
- 著作権は原著者・出版社に帰属します。
