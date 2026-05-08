# Security Policy

## Reporting a Vulnerability

このリポジトリで脆弱性を発見した場合は、**公開 Issue を作成しないでください**。
GitHub の **Security Advisories** から非公開で報告してください:

- https://github.com/icchie/yayoi-csv-skill/security/advisories/new

報告内容に含めてほしい情報:

- 影響を受けるファイル / コミット SHA
- 再現手順（最小限の入力例があると助かります）
- 想定される影響範囲（例: Skill 利用者の Claude に意図しない動作をさせられるか、ローカルファイルに任意書き込みができるか、など）

レスポンスの目安:

| 種別 | 目安 |
|------|------|
| 初回応答 | 5 営業日以内 |
| 修正方針の共有 | 14 日以内 |
| パッチリリース | 影響度に応じて 7〜30 日 |

## Skill 固有の注意点

このリポジトリは Claude の Agent Skill として配布されます。Skill は Claude が読み込んで指示として解釈するため、`SKILL.md` や `scripts/` 配下のスクリプトを改ざんされると、利用者の Claude が改ざんされた指示に従って動作する可能性があります。

利用者には以下を推奨します:

- インストール時はタグ（例: `v0.1.0`）など固定された参照点をチェックアウトする
- フォークやミラーではなく、本家リポジトリ `icchie/yayoi-csv-skill` から直接取得する
- アップデート時は `git diff` で変更内容を確認する

## サポート対象

最新の `main` ブランチおよび最新リリースのみがセキュリティパッチの対象です。

## 依存関係更新の運用ルール

供給元（GitHub Actions のリリース等）が侵害されたバージョンを掴まないよう、Dependabot が起票する PR は以下のルールでマージします。

- **リリース公開から 14 日以上経過していること**を確認してからマージする
  - PR 内のリリース日時、または該当リポジトリの Releases ページで確認
  - 14 日経っていなければ PR を保留しておく（自動マージはしない）
- メジャーバージョンアップは特に変更点 / changelog を読み、CI が通っていることを確認する
- CVE 由来の **security update** はこのルールの対象外で、確認のうえ速やかにマージする

NOTE: Dependabot の `cooldown` 機能は本リポジトリで唯一使う `github-actions` ecosystem では未対応 ([dependabot/dependabot-core#14628](https://github.com/dependabot/dependabot-core/issues/14628)) のため、この運用ルールで代替している。
