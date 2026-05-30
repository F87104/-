# Pine Strategy化用 完全ロジック仕様

## State

- `active`: V候補監視中
- `vStartPrice`, `vLowPrice`, `vStartBar`, `vLowBar`
- `contextBar`: 回復率条件が最初に成立した足
- `usedPair`: 同じVペアの重複使用を禁止
- `inTrade`: `strategy.position_size != 0`

## Signal Flow

1. confirmed pivot high/lowを交互に管理する。
2. H -> L のペアで急落条件を満たすか見る。
3. 回復率65%-125%、速度条件、V谷再更新なしを確認する。
4. V左肩時点のPRECALM条件を確認する。
5. context成立後、最大36本だけ棚ブレイクを待つ。
6. 直近6本の棚を、シグナル足を含めず計算する。
7. closeが棚高値+0.05ATRを上抜け、実体/終値位置条件を満たしたらロング。
8. SLは棚安値-0.25ATR。
9. TPは約定後にEntry基準1.5Rで設定。
10. ポジション保有中は新しいV候補もシグナルも無視する。