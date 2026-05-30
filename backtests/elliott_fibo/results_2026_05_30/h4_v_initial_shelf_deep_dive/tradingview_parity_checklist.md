# TradingView 照合チェックリスト

1. H4チャートで実行する。
2. Pineの対象通貨をPythonの `current_trades_detail.csv` と同じにする。
3. 年末年始除外をPythonと同じにする。
4. まずstrategy成績ではなく、signal_time一致だけを見る。
5. `current_trades_detail.csv` の各行について、symbol / signal_time / entry_timeを照合する。
6. 一致後、shelf_high / shelf_low / stop / target / entry を照合する。
7. targetはPython再現用ならsignal close基準、本番用ならentry基準。どちらで比較しているか明記する。
8. TradingViewのデータ提供元差で1-2本ずれる場合は、その通貨を別管理にする。
9. シグナル一致率が100%になるまでPFや勝率は採用判断に使わない。