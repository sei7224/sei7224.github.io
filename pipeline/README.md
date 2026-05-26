# Gadget Wire Japan Pipeline

メーカー発表や販売ページを基に、短い製品ニュース記事を安全に生成して `manegori-lab.com` に公開するためのパイプラインです。旧サイトの公開コンテンツは Gadget Wire Japan に刷新済みです。

## 現在できること

- 製品情報を `content/products/*.json` として受け取る
- Apple公式RSSなど、許可リスト化したフィードの見出しとURLを候補キューへ収集する
- 製品名、価格、発売日、特徴、出典、広告リンクを記事HTMLへ変換する
- 未確認記事を `build/drafts/` にのみ生成し、`noindex` を付ける
- 事実確認、編集レビュー、画像利用根拠が揃った記事だけ `dist/` に公開出力する
- GitHub Pagesへ配信できる静的HTML/CSSを生成する

記事本文の事実や短い解説は Codex が作成し、レンダラーは入力済みの内容だけを表示します。メーカー画像を自動取得したり、実機を使用したような文章を自動生成したりはしません。

## ディレクトリ

```text
config/site.json              サイト名、公開URL、広告表示の設定
config/automation_policy.json Codex自動公開で許可する範囲
content/products/             記事入力JSON
content/candidates/           収集Botが置く記事候補JSON
config/sources.json           監視する公式フィードの許可リスト
scripts/collect_candidates.py 記事候補の収集Bot
scripts/site_builder.py       下書き/公開HTML生成
scripts/sync_public_root.py   公開ルートへの管理対象HTML同期
static/assets/                CSSと自前の代替画像
build/drafts/                 レビュー用出力（デプロイ対象外）
dist/                         公開用出力（GitHub Pages配信対象）
tests/                        公開ゲートのテスト
```

## 使い方

```bash
cd pipeline
python3 scripts/collect_candidates.py --dry-run
python3 scripts/site_builder.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory build/drafts
```

サンプル下書きは `http://localhost:8000/articles/sample-usb-c-dock/` で確認できます。

## 記事追加フロー

1. `content/products/example-draft.json` を複製し、製品情報と発表元URLを入力する。
2. Codexでリリース内容を検証し、`article.lead` と `article.paragraphs` を作成する。
3. `python3 scripts/site_builder.py` で下書きを生成し、表示と出典を確認する。
4. 画像を掲載する場合は利用条件を確認し、`image.rights_basis` と `image.rights_verified` を設定する。
5. 最終確認後に `status` を `published`、各確認フラグを `true` にして再生成する。

公開には次の条件が必須です。

- `compliance.facts_verified: true`
- `compliance.editorial_reviewed: true`
- 画像URLを使用する場合は `image.rights_verified: true` と利用根拠
- アフィリエイトリンクを置く場合は広告表示文

## Codex自動公開

`config/automation_policy.json` で許可した公式ソースの記事は、Codexの定期ジョブが公式ニュースリリース本文を確認して記事化し、安全条件を満たす場合に限り自動公開できます。現在の許可範囲は Apple Newsroom（日本）の製品発表だけです。

自動公開の記事には次の追加制約があります。

- `source.id` が許可された公式ソースであり、URLホストが `www.apple.com` であること
- `source.allowed_for_automation: true` を設定すること
- `compliance.automation_policy`、`automation_verified_at`、`review_actor` を記録すること
- 外部画像を使用せず、サイト所有の代替画像のみ表示すること
- アフィリエイトリンクを含めないこと
- 使用感、評価、比較優位など、公式発表で確認できない主張を書かないこと

条件を外れる候補は自動公開せず、手動確認対象として残します。画像掲載やアフィリエイト導入は、権利確認と広告表示を別途整えた後の運用です。

## GitHub Pages

GitHub Pages はリポジトリ直下の静的ファイルを配信します。`.github/workflows/publish-reviewed-content.yml` は `pipeline/dist/` を生成し、マニフェストで管理される公開ファイルだけをルートへ同期します。記事を非公開へ戻した場合は、その記事の生成済みディレクトリも同期時に削除します。

現在は公開ブランチ内に `pipeline/` を置く構成のため、入力JSONや候補メタデータも公開リポジトリおよび直接URLから参照可能です。`robots.txt` ではクロールを除外しますが、機密情報、解禁前情報、秘密鍵やAPIキーはこの配下へ保存しません。

## 候補収集

収集Botは `config/sources.json` で有効化した公式RSS/Atomの見出し・URL・配信日だけを `content/candidates/` に保存します。現在はApple公式RSSを候補収集対象に設定していますが、本文や製品画像は複製しません。候補から `content/products/` の記事入力へ変換する段階では、Codex定期ジョブが公式リリース本文で価格、発売地域、主要仕様を確認します。

`.github/workflows/collect-candidates.yml` は6時間ごと、手動実行時、および収集元設定や収集コードの更新時に候補を取り込みます。収集で保存するのは見出し、URL、配信日と管理用メタデータだけで、記事本文や画像は自動取得しません。自動公開条件を満たさない候補は、Codexが公開せず手動確認対象として扱います。
