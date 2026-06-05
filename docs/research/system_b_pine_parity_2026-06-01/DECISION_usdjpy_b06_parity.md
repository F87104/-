# USDJPY B06 — Pine照合 判定（TV執行基準）

更新: 2026-06-05

## 結論

**TV OANDA + Pine: 完全一致（ユーザー確認 2026-06-05）**

| 基準 | 件数 | 状態 |
|------|------|------|
| TV-OHLC Python | **9** | 執行の正 |
| チャート照合 | **9/9 OK** | **TV執行可** |

## 運用

- エントリー・決済: TradingView（OANDA USDJPY 4H・B06 Pine）
- 期待値: `python_expected_b06_tv_oanda_usdjpy.csv`
- ログ: `parity_log_b06_tv_oanda_confirmed.csv`

## 技術メモ

- signal_time と TV entry は **約9〜13時間ずれて表示** されることがある（同一トレード）  
- 詳細: [B06_TV_EXECUTION_TRUTH_ja.md](B06_TV_EXECUTION_TRUTH_ja.md)

## ファイル

- 期待値: `python_expected_b06_tv_oanda_usdjpy.csv`
- 比較: `b06_f87104_vs_tv_oanda_usdjpy.csv`
- レポート: `B06_TV_OANDA_RERUN_USDJPY.md`
