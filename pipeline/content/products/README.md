# Product Input Format

製品ニュース1本につきJSONファイルを1つ配置します。まず `example-draft.json` を複製してください。

## 公開前の必須確認

| 項目 | 意味 |
| --- | --- |
| `source.url` | 根拠となるメーカー発表または正規販売ページ |
| `facts.checked_at` | 価格・発売日等を最終確認した日 |
| `image.rights_basis` | 外部画像を表示する場合の利用根拠 |
| `compliance.facts_verified` | 本文と出典の一致を確認済み |
| `compliance.editorial_reviewed` | 誤認表示やリンクを公開前に編集確認済み |

`status: "draft"` の記事は、確認フラグにかかわらず公開用 `dist/` には入りません。外部製品画像を掲載しない場合、サイト所有の代替画像が表示されます。

## Codex自動公開記事

`config/automation_policy.json` の範囲でCodexが自動公開する場合は、通常の必須確認に加えて次を設定します。

| 項目 | 値または意味 |
| --- | --- |
| `source.id` | `apple-newsroom-jp`、`google-devices-jp`、`samsung-newsroom-jp`、`sony-press-jp` のいずれか |
| `source.allowed_for_automation` | `true` |
| `compliance.automation_policy` | `official_release_no_image_no_affiliate_v1` |
| `compliance.automation_verified_at` | 公式ページを確認した日 |
| `compliance.review_actor` | `Codex automation` |

このモードでは `image.src` と `affiliate_links` は空でなければ公開に失敗します。
