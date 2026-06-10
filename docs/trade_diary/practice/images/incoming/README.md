# incoming — トレード日誌用スクショ受け口

TradingView / GMO の**実スクショ**をここに置いてから、注釈スクリプトを実行してください。

## XAUUSD 日足に説明を書き込む

```bash
# 1. このフォルダに PNG を保存（例: xauusd_d1.png）
# 2. 注釈を焼き込む
python3 scripts/annotate_xauusd_d1_chart.py \
  docs/trade_diary/practice/images/incoming/xauusd_d1.png \
  docs/trade_diary/practice/images/2026-06-10_xauusd_04_d1_structure.png
```

注釈なしの図解のみ必要な場合:

```bash
python3 scripts/render_xauusd_d1_annotated_chart.py
```

出力: `2026-06-10_xauusd_04_d1_structure_annotated.png`
