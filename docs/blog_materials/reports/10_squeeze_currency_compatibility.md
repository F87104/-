# Market Psychology Squeeze 通貨相性分析

作成日: 2026-05-30

対象:

- `Market Psychology Squeeze Strict`
- H4
- Short Squeezeのみ
- Capitulation直買いは主役から外す

## 結論

この手法と一番相性が良いのは **XAUUSD**。

次点は **USDJPY / AUDJPY**。ただし件数はまだ多くない。

**SILVER** は数字だけ見ると強いが、OOS件数がゼロなので監視候補。

**EURJPY** は strict 版では悪化するが、default 版ではかなり良い。つまりEURJPYは「厳選しすぎない棚上抜け」と相性がある。

**GBPJPYは除外候補**。今回の踏み上げ棚ブレイクでは明確に合っていない。

## 通貨別判定

| symbol | 判定 | 使い方 | 根拠 |
|---|---|---|---|
| XAUUSD | A 本命 | strictで使う | default/strict両方で高PF。OOSも強い |
| USDJPY | B strict候補 | strictで小さく監視 | strictでプラス。OOSもプラス |
| AUDJPY | B strict候補 | strictで小さく監視 | strictでプラス。ただし件数少なめ |
| SILVER | B- 監視候補 | strictでアラート監視 | strictは強いがOOSゼロ |
| EURJPY | B default向き | strictではなくdefault寄り | defaultは安定、strictで悪化 |
| CHFJPY | C 保留 | 現時点では主力にしない | strictは1件のみ、defaultも弱い |
| GBPJPY | 除外候補 | 原則除外 | strict/defaultとも弱い |

## Short Squeeze 通貨別成績

| symbol | default trades | default total R | default PF | strict trades | strict total R | strict PF | strict DD | strict OOS R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | 16 | +16.19R | 4.14 | 10 | +10.73R | 4.45 | 2.07R | +5.95R |
| USDJPY | 22 | +1.78R | 1.13 | 13 | +4.87R | 1.69 | 2.02R | +1.98R |
| AUDJPY | 19 | +6.93R | 1.68 | 6 | +2.90R | 1.95 | 2.04R | +1.99R |
| SILVER | 16 | +0.62R | 1.06 | 7 | +7.33R | 4.47 | 1.03R | 0.00R |
| EURJPY | 25 | +13.27R | 2.09 | 6 | -3.09R | 0.39 | 3.05R | -1.02R |
| CHFJPY | 9 | +0.76R | 1.15 | 1 | +1.97R | inf | 0.00R | 0.00R |
| GBPJPY | 28 | -3.19R | 0.83 | 8 | -6.66R | 0.07 | 5.64R | -1.02R |

## 組み合わせ別

| combo | symbols | trades | winrate | total R | PF | max DD | OOS R | 判定 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A core | XAUUSD, USDJPY, AUDJPY | 29 | 55.17% | +18.51R | 2.40 | 3.11R | +9.92R | 現実的な本線 |
| A plus SILVER | XAUUSD, USDJPY, AUDJPY, SILVER | 36 | 58.33% | +25.84R | 2.68 | 2.07R | +9.92R | 数字は最良。ただしSILVER OOS不足 |
| Metals only | XAUUSD, SILVER | 17 | 70.59% | +18.06R | 4.46 | 2.07R | +5.95R | 強いが件数少なめ |
| All ex GBP | XAUUSD, USDJPY, AUDJPY, SILVER, EURJPY, CHFJPY | 43 | 53.49% | +24.72R | 2.21 | 3.09R | +8.89R | 広めの候補 |
| JPY strict positive | USDJPY, AUDJPY | 19 | 47.37% | +7.77R | 1.77 | 3.03R | +3.96R | 補助候補 |

## 実戦での監視リスト

### strict設定で監視

1. XAUUSD
2. USDJPY
3. AUDJPY

### strict設定でアラートだけ監視

1. SILVER

### default寄りで別監視

1. EURJPY

EURJPYは、strict設定で悪化しているため、同じPineのまま使うなら優先度を下げる。もしEURJPYを活かすなら、`棚幅上限 2.5ATR / 急落幅 3.0ATR` のdefault寄りで別検証する。

### 除外

1. GBPJPY

GBPJPYは、急落後の棚上抜けが踏み上げにならず、だましになりやすい。今回の手法では原則外す。

## なぜXAUUSDと相性が良いのか

推定される理由:

- 金は急落後の買い戻しが速い
- 急落後に安値圏で止まると、ショートカバーが一気に出やすい
- H4の6本棚が「売り切り後の再点火」として機能しやすい
- GBPJPYのように棚上抜け後に再び荒く沈むケースが少ない

これは、これまでのH4 V系でXAUUSDを除外候補にした話とは別。今回の手法は「Vの初動を買う」のではなく、**急落後の棚上抜けを買う**ため、XAUUSDがむしろ主役になる。

## 次の検証

1. XAUUSD / USDJPY / AUDJPY だけでPine照合
2. SILVERはフォワードで10件以上出るまで監視
3. EURJPY default設定を別にPine化して比較
4. GBPJPY除外を固定
5. TradingViewの実volumeで `volume > sma(volume,20) * 1.3` をON/OFF比較
