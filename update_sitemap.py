#!/usr/bin/env python3
"""サイトマップ自動更新スクリプト（記事生成後に実行）"""

import glob
from datetime import date
from pathlib import Path

BASE = "https://manegori-lab.com"
today = date.today().isoformat()

STATIC_URLS = [
    ("", "1.0", "weekly"),
    ("/about.html", "0.5", "monthly"),
    ("/contact.html", "0.3", "monthly"),
    ("/privacy.html", "0.3", "monthly"),
    ("/category/ai.html", "0.8", "weekly"),
]

urls = list(STATIC_URLS)
for path in sorted(glob.glob("articles/*.html")):
    slug = Path(path).name
    urls.append((f"/articles/{slug}", "0.9", "monthly"))

entries = []
for loc, priority, changefreq in urls:
    entries.append(f"""  <url>
    <loc>{BASE}{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "\n".join(entries)
sitemap += "\n</urlset>\n"

Path("sitemap.xml").write_text(sitemap, encoding="utf-8")
print(f"sitemap.xml 更新完了 ({len(urls)}件)")
