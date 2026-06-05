# B07 DTS — TV OANDA parity サマリ

> **退役（2026-06-01）:** 本番・研究ラインから外した。B06（棚抜）と H4 シグナル重複のため [lane_exclusions.md](../../operations/system_b/lane_exclusions.md#b07-dts-trap-shelf-retired)。以下は照合記録のアーカイブ。

更新: 2026-05-31

## 結論（現時点）

**執行の正 = 先ほどの4本 `tv_*_h4.csv` 上の Python（12件）**。

- TV-OHLC Python: **12** 件
- H4棚日時: **12/12** が B06 TV 照合済みと同一（`parity_log_b07_tv_oanda.csv` → `H4_OK`）
- 旧 F87104 export 9件: **使わない**（signal_time 一致 0/9）
- B06 重複: **12** 件 → 本番は **B06 優先**
- 残り: Pine で **D1 Trap ラベル** + **Entry基準** stop/target の最終確認

## 銘柄別（TV-OHLC）

- AUDJPY: 3
- EURJPY: 4
- GBPJPY: 3
- USDJPY: 2

## 使わないもの

- `python_expected_b07_dts_all.csv`（F87104 H1→H4、9件）

## 使うもの

- `python_expected_b07_tv_oanda_all.csv` および `_*_{symbol}.csv`
- `*_tv` 列 = TV チャート/テスター表示（UTC+9）
- Pine: `d1_trap_h4_shelf_strict_strategy.pine`

## 次

1. 銘柄ごと Pine で 12 件のラベル照合
2. **B07 専用**ストラテジーテスター CSV をエクスポートして `tv_strategy_trades_b07_{symbol}.csv` に保存
3. `parity_log_b07_tv_oanda.csv` に OK/MISS を記録

再現: `python3 scripts/run_b07_tv_oanda_parity.py`