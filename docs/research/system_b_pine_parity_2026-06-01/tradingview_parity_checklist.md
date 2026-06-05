# 系統B — B06 VIS / B07 DTS Pine 照合チェックリスト

作成日: 2026-06-01

Python を正とする。**signal_time 一致率 100%** になるまで PF・勝率で採用判断しない。

## Pine ファイル

| レーン | Pine |
|--------|------|
| B06 VIS PRECALM | `pine/research/h4_v_initial_shelf_breakout_strategy.pine` |
| B07 DTS SIGADX30 | `pine/research/d1_trap_h4_shelf_strict_strategy.pine` |

**注意:** B06 は *visual* 版ではなく **strategy** 版のみ。confirmed pivot 必須。

## 期待値 CSV

| ファイル | 件数 |
|----------|------|
| `python_expected_b06_vis_precalm_all.csv` | 34 |
| `python_expected_b06_vis_precalm_research.csv` | 29 |
| `python_expected_b06_vis_precalm_oos.csv` | 5 |
| `python_expected_b07_dts_all.csv` | 9 |
| `python_expected_b07_dts_research.csv` | 6 |
| `python_expected_b07_dts_oos.csv` | 3 |

## 手順

### Step 0 — タイムゾーン

1. Python `signal_time` は CSV の **UTC 相当**（indexそのまま）。
2. TV 表示が JST なら **+9h** を1件で確認してから全件照合。

### Step 1 — B06 スモーク（USDJPY）

1. [pine_required_settings.md](pine_required_settings.md) — **TP = Signal基準**（Pineデフォルトも2026-06-01に変更済み）
2. 詳細: [usdjpy_b06_smoke.md](usdjpy_b06_smoke.md)（**13件**）
3. 最初の3件だけ: `usdjpy_b06_first3.csv`
4. USDJPY H4 に B06 Pine を貼り、ラベル「棚B」の日時を表と照合
5. `parity_log_b06_filled.csv` の `tv_match` を更新（初期値 `pending`）

### Step 2 — B06 全銘柄（34件）

1. USDJPY / EURJPY / GBPJPY / AUDJPY（XAU・CHF・SIL は系統B対象外）
2. `parity_log_b06_filled.csv` に `tv_match` = OK / MISS / OFFSET / DATA

### Step 3 — B07（9件）

1. [usdjpy_b07_smoke.md](usdjpy_b07_smoke.md)（USDJPYは **2件**・いずれもB06と同一signal）
2. `selected_CURRENT_A30_180_SIGADX30`（trap 30–180、SIG ADX≤30、**TP = Entry基準**）
3. `parity_log_b07_filled.csv` を更新
4. B06と同一 signal_time は運用でB06優先（`overlap_b06_b07_signal_times.csv` 参照）

### Python再実行監査

```bash
python3 scripts/run_system_b_pine_parity_audit.py
```

→ [audit_report_ja.md](audit_report_ja.md)（exportとPython再実行の一致確認済み）

## 一致判定

| 項目 | 許容 |
|------|------|
| signal_time | **完全一致**（TZ補正後） |
| entry_time | signal の **次の H4 足**（next_open） |
| stop / target | ±0.5 pip または ±0.01% |
| 件数 | B06=34 / B07=9 |

## 採用ゲート

- B06: **34/34** signal match → 0.25R フォワード 30件
- B07: **9/9** signal match → 同上
- 両方完了後に `portfolio_slots.yaml` の `pine_ready` を `yes` に更新（手動）

## 再現

```bash
python3 scripts/export_system_b_pine_parity.py
```
