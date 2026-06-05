# 系統B — TV CSV とレーンの対応

## B06 棚ブレイク — JPY4 本番（完了・pine_ready yes）

| 銘柄 | CSV | 件数 |
|------|-----|------|
| USDJPY | `tv_usdjpy_h4.csv` | 9 |
| EURJPY | `tv_eurjpy_h4.csv` | 9 |
| GBPJPY | `tv_gbpjpy_h4.csv` | 8 |
| AUDJPY | `tv_audjpy_h4.csv` | 11 |

## B06 棚ブレイク — 試験3銘柄（Pine照合完了 2026-06-05）

| 銘柄 | CSV | 備考 |
|------|-----|------|
| XAUUSD | `tv_xauusd_h4.csv` | **Pine9 = Python9 照合OK**（2026-06-05・FX 4H） |
| SILVER | `tv_xagusd_h4.csv` | **Pine2 = Python2 照合OK**（2026-06-05・OANDA XAGUSD） |
| CHFJPY | `tv_chfjpy_h4.csv` | **Pine9 = Python9 照合OK**（2026-06-05・FOREXCOM） |

## B07 DTS（TV-OHLC Python 基準・Pine照合中）

上記4 CSV をそのまま使用。**新規CSV不要。**

| 出力 | 件数 |
|------|------|
| `python_expected_b07_tv_oanda_all.csv` | **12** |
| 旧 `python_expected_b07_dts_all.csv` | 9（F87104・参照用のみ） |

手順: `B07_TV_EXECUTION_TRUTH_ja.md` / `DECISION_b07_tv_oanda_parity.md`

## 今回いただいたが B06/B07 対象外

| ファイル | レーン | 用途 |
|----------|--------|------|
| `FX_XAUUSD, 240` | **B01** SQZ XAU | フルサイズ候補・別照合 |
| `OANDA_XAGUSD, 240` | **B05** SQZ SILVER | フルサイズ候補・別照合 |

保存: `tv_xagusd_h4.csv`（XAGのみリポジトリ済み）

## 次にやること

**B07** → Pine 12件照合（baseline 済み）  
**B01/B05 SQZ** → XAU/XAG の TV 照合を別途
