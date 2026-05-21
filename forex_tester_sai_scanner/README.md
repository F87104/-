# Sai Forex Tester Scanner / EA Scaffold

Sai手法をForex Tester Desktop向けのスキャナー/EAにするための雛形です。

最初は完全自動売買ではなく、候補ポイントを検出してチャート上に印を出す「スキャナー」として使う前提です。検出精度が十分に確認できてから、注文を出すEAモードへ進めます。

## Why Scanner First

Sai手法には裁量判断が残る部分があります。

- 短期・中期の方向一致
- 抵抗線/支持線の重要度
- 停滞のきれいさ
- V字の勢い
- 暴落後や方向感なしの見送り

これらをいきなり自動注文にすると、誤検出がそのまま損失になります。まずは「人間が見てもSai手法っぽい場所にだけ印が出るか」を確認します。

## Files

- `src/SaiScannerCore.hpp`
- `src/SaiScannerCore.cpp`
  - Forex Tester非依存の判定ロジックです。
  - C++17で書いてあります。

- `adapter/ForexTesterStrategyAdapter.cpp`
  - Forex Tester APIへ接続するためのテンプレートです。
  - ユーザー側Windows環境の `C:\ForexTester6\Examples\Strategies` のヘッダに合わせてTODOを置き換えます。

## Current Detection Logic

実装済みの初期ロジック:

- 1時間足前提
- 短中一致
- モメンタム判定
- レンジ気味相場の見送り
- USDJPY低優先フィルター
- 12月中旬から年始の見送りフィルター
- 高安値停滞
- 抵抗線/支持線付近の停滞
- 広め/変則的な停滞
- V字/急な揺り戻し文脈
- レンジ抜け2回目以降のブレイクアウト
- 初期ストップ候補

まだ初期版なので、最初の目的は「正解を出すこと」ではなく「検証できる候補を安定して出すこと」です。

## Build Direction

Forex Tester公式ガイドでは、EAは戦略ルールに基づいて自動で注文を開閉でき、カスタムEAは `.dll` として追加します。実際のC++ APIヘッダとサンプルはForex TesterのWindowsインストール内にあります。

作業手順:

1. Windows側でForex Testerを開く。
2. `C:\ForexTester6\Examples\Strategies` を確認する。
3. サンプル戦略プロジェクトをコピーする。
4. `SaiScannerCore.hpp` と `SaiScannerCore.cpp` を追加する。
5. `ForexTesterStrategyAdapter.cpp` のTODOをサンプル戦略APIに合わせて置き換える。
6. DLLとしてビルドする。
7. Forex Testerで `File -> Install -> Install new strategy` から読み込む。
8. H1プロジェクトでスキャナーを有効化する。

## Scanner Mode Behavior

スキャナーでは注文を出しません。

候補が出たら、以下をチャートに表示する想定です。

- セットアップ名
- LONG/SHORT
- エントリー候補価格
- 停滞ゾーン上限/下限
- 初期ストップ候補
- 理由

## EA Mode Behavior

EAモードに進む場合の最低条件:

- 直近2から5年のXAUUSDで候補検出を目視確認
- 明らかな誤検出を減らす
- EURJPY/GBPJPYでも検証
- USDJPYは別扱い
- 年末年始フィルターを有効化
- 1回あたりの損失額を固定
- 月間損失上限で停止

## Important Parameters

`ScannerConfig` の主な値:

- `mediumTrendLookbackBars = 520`
- `shortTrendLookbackBars = 72`
- `recentTrendBars = 8`
- `stagnationMinBars = 7`
- `stagnationMaxAtr = 1.20`
- `wideStagnationMaxAtr = 2.50`
- `keyLevelLookbackBars = 720`
- `rangeMinBars = 480`
- `vShapeRecoveryRatio = 0.80`

これらは最初の仮置きです。銘柄ごとの検証で調整します。

## Next Needed From Windows

この雛形を実際にForex Tester DLLへ接続するには、次のどちらかが必要です。

- `C:\ForexTester6\Examples\Strategies` のサンプル一式
- 使っているForex Testerのバージョン、APIヘッダ名、サンプルEAのコード

それがあれば、TODO部分を実際のForex Tester API名に置き換えて、より実装に近い形にできます。
