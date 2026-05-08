# yayoi-csv-skill

やよいの青色申告オンライン／弥生会計オンラインの「スマート取引取込」用 CSV を Claude に作らせる [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)。

領収書 PDF・レシート画像・取引明細などを Claude に渡すと、弥生にそのままインポートできる **Shift-JIS / CR+LF** の CSV を出力する。

## できること

- 1 取引 = 1 行の標準フォーマット（日付・入金・出金・摘要・軽減税率・部門・請求書区分）に変換
- Shift-JIS / CR+LF / 200KB 未満 / 9 桁以内の金額 / 80 文字以内の摘要 を満たす CSV を出力
- 軽減税率対象の自動マーキング（`※`）
- 西暦 4 桁・和暦・年月日分割など弥生が受け付ける日付フォーマットに対応

## 構成

```
.
├── SKILL.md                     # Claude が読み込むスキル本体
├── scripts/
│   └── build_csv.py             # 取引 JSON → 弥生 CSV 変換ヘルパー
├── references/
│   └── spec.md                  # 弥生 CSV の詳細仕様
└── examples/
    ├── transactions.json        # 入力サンプル
    ├── sample-with-header.csv   # 出力サンプル (ヘッダーあり)
    └── sample-no-header.csv     # 出力サンプル (ヘッダーなし)
```

## インストール

### Claude Code（プロジェクトに追加）

```bash
git clone https://github.com/icchie/yayoi-csv-skill.git ~/.claude/skills/yayoi-csv
```

または現在のプロジェクト直下の `.claude/skills/yayoi-csv` にクローンしてもよい。

### Claude.ai / Claude Desktop

1. このリポジトリ全体を zip 化する（`SKILL.md` がアーカイブ直下に来るようにする）

   ```bash
   cd yayoi-csv-skill
   zip -r ../yayoi-csv.skill SKILL.md scripts references examples
   ```

2. Claude.ai の設定 → Capabilities → Skills から `yayoi-csv.skill` をアップロード

## 使い方

Claude に「弥生にインポートする CSV を作って」と頼むと、SKILL.md がトリガーされてこのスキルが使われる。

### 例: レシート画像のディレクトリから CSV を作る

1. レシートをスキャンした画像（または写真）を 1 つのディレクトリにまとめる:

   ```
   receipts/
   ├── 2024-06-15-sakura-denki.jpg
   ├── 2024-08-22-maruyama-shoten.png
   ├── 2024-10-05-conveni-water.jpg
   └── 2024-11-03-cafe.heic
   ```

2. Claude（Claude Code・Claude.ai いずれも画像読み取り対応のもの）に次のように頼む:

   > `receipts/` にあるレシート画像を全部読み取って、やよいの青色申告オンラインに取り込む CSV を作って。食品・飲料は軽減税率対象として `※` をつけて。出力は `out.csv` に保存して。

3. Claude が行う処理（このスキルが誘導する）:
   - `receipts/` 配下の画像を 1 枚ずつ読み、日付 / 金額 / 店舗名 / 商品名 / 軽減税率対象かを抽出
   - 1 レシート（1 決済）= 1 行 になるよう取引 JSON を構築
   - `python3 scripts/build_csv.py --header --output out.csv` に JSON を渡し、Shift-JIS / CR+LF の CSV を生成
   - 結果を要約（件数・合計金額・軽減税率対象の件数・読み取れなかった画像があればその一覧）して報告

4. 生成された `out.csv` を、やよいの青色申告オンライン → スマート取引取込 → CSV ファイル取込 からアップロードする。

   読み取りが曖昧だった項目（手書きで読みづらい金額や、店舗名が省略されているレシートなど）は Claude がレポートで指摘してくれるので、必要に応じてその行だけ手で修正する。

### スクリプトを直接呼びたい場合

```bash
python3 scripts/build_csv.py --header --output out.csv < examples/transactions.json
```

入力 JSON のスキーマは [`scripts/build_csv.py`](scripts/build_csv.py) の docstring を参照。

## 仕様

弥生公式の取込仕様は [`references/spec.md`](references/spec.md) にまとめてある。

出典: 弥生サポート [CSVファイル取込のファイル形式（やよいの青色申告 オンライン）](https://support.yayoi-kk.co.jp/faq_Subcontents.html?page_id=27075&grade_id=Blue)

## ライセンス

MIT。詳細は [LICENSE](LICENSE) を参照。
