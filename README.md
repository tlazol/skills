# tlazol/skills

0rga が管理する Agent Skills のコレクションです。

各ディレクトリは、[Agent Skills](https://agentskills.io/) の形式に従った独立したスキルです。

## インストール

`skills` CLI を使って、必要なスキルを追加できます。

```shell
npx skills add tlazol/skills --skill proofreading
npx skills add tlazol/skills --skill quiz-the-plan
npx skills add tlazol/skills --skill self-code-review
```

## 収録スキル

| スキル | 説明 |
| --- | --- |
| [`proofreading`](./proofreading/) | 原文を大きく書き換えず、表記、空白、誤字、文法、名称、文末を整えます。 |
| [`quiz-the-plan`](./quiz-the-plan/) | AI が提案したソフトウェア実装プランを一問ずつ進む適応型クイズに変換し、設計判断、トレードオフ、検証方法への理解を助けます。 |
| [`self-code-review`](./self-code-review/) | AI が実装結果を自己レビューし、要件との一致、設計の複雑さ、保守性、テストの妥当性を確認します。 |

## ライセンス

[MIT License](./LICENSE)
