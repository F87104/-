# WaveBox Pine v1.2 Completion Note

作成日: 2026-05-26

## 完成版

- `/Users/asamifujita/Documents/Codex/2026-05-21/fx-ai/pine/research/wavebox_usdjpy_h1_rebreak_v1_2.pine`

## 方針

v1.2は、手法ロジックを変える版ではない。

目的は実戦安全化。

- v1.1の波形・Box・ブレイク・A/A+/B判定は維持
- デフォルトの内部R対象を `GO A+ / GO A` のみに変更
- strategy注文もデフォルトで `GO only`
- `SELECT A` / `OBS B` / `SKIP` は表示と記録用
- タイムゾーン照合が終わるまでstrategy注文をブロック
- 標準前提から外れた設定ではstrategy注文をブロック

## 追加された安全項目

- `TZ照合済み（Python/TV）`
- `内部R対象`
- `注文対象`
- `注文はTZ照合後のみ`
- `注文は標準前提のみ`
- テーブル表示 `TZ`
- テーブル表示 `除外hour`
- テーブル表示 `14時 暫定除外`
- テーブル表示 `標準前提`
- テーブル表示 `Raw signals`
- テーブル表示 `GO signals`
- テーブル表示 `Sim signals`
- テーブル表示 `Last action`

## デフォルト実戦設定

- Rule preset: `v0.4 filtered`
- Wave1 quality: `Strict`
- 内部R対象: `GO only`
- 注文対象: `GO only`
- strategy注文: OFF
- TZ照合済み: OFF

`TZ照合済み` は、PythonとTradingViewで最低5件の過去シグナル照合が終わるまでONにしない。

## 注意

TradingView上でのコンパイル確認はまだ必要。

コンパイルエラーが出た場合は、エラー行とメッセージをそのまま確認する。

## 表示ゼロ時の判定

2023-2026のPython検証では、標準1波剪定ありで候補が15件ある。

- `Raw signals = 0`: 通常の低頻度だけではなく、TradingView銘柄データ差、タイムゾーン、またはPine再現差を疑う。
- `Raw signals > 0 / GO signals = 0`: 候補は出ているが、BまたはSELECT A中心で実戦GO対象ではない。
- `GO signals > 0 / Sim signals = 0`: `内部R対象` 設定を確認する。
- `Sim signals > 0 / 内部 trades = 0`: エントリー後のrisk不成立、または表示範囲外を確認する。

なお、`strategy` の売買回数はデフォルトで0になる。v1.2は安全のため `参考strategy注文を出す = OFF`、かつ `TZ照合済み = OFF` ではstrategy注文を出さない。実力評価は左下テーブルの内部Rを優先する。
