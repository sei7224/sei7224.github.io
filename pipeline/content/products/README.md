# Product Input Format

製品ニュース1本につきJSONファイルを1つ配置します。まず `example-draft.json` を複製してください。

## 公開前の必須確認

| 項目 | 意味 |
| --- | --- |
| `source.url` | 根拠となるメーカー発表または正規販売ページ |
| `facts.checked_at` | 価格・発売日等を最終確認した日 |
| `image.rights_basis` | 外部画像を表示する場合の利用根拠 |
| `compliance.facts_verified` | 本文と出典の一致を人が確認済み |
| `compliance.editorial_reviewed` | 誤認表示やリンクを公開前に編集確認済み |

`status: "draft"` の記事は、確認フラグにかかわらず公開用 `dist/` には入りません。外部製品画像を掲載しない場合、サイト所有の代替画像が表示されます。
