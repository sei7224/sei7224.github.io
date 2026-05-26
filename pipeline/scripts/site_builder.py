#!/usr/bin/env python3
"""Build a static product-news site from reviewed JSON inputs."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AUTOMATION_POLICY_FILE = ROOT / "config" / "automation_policy.json"


class BuildError(ValueError):
    """Raised when content cannot be safely rendered or published."""


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"{path}: invalid JSON: {exc}") from exc


def require_text(data: dict, key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{label} must be non-empty text")
    return value.strip()


def validated_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise BuildError(f"{label} must be an http/https URL")
    return value


def validate_product(product: dict, source_path: Path | None = None) -> None:
    prefix = f"{source_path}: " if source_path else ""
    try:
        slug = require_text(product, "slug", "slug")
        if not SLUG_RE.fullmatch(slug):
            raise BuildError("slug must contain lowercase letters, numbers, and hyphens only")
        status = require_text(product, "status", "status")
        if status not in {"draft", "published"}:
            raise BuildError("status must be draft or published")
        for key in ("title", "manufacturer", "product_name", "category", "published_at"):
            require_text(product, key, key)

        facts = product.get("facts")
        if not isinstance(facts, dict):
            raise BuildError("facts must be an object")
        for key in ("announcement_date", "release_date", "price", "checked_at"):
            require_text(facts, key, f"facts.{key}")
        features = facts.get("features")
        if not isinstance(features, list) or not features:
            raise BuildError("facts.features must contain at least one item")
        for item in features:
            if not isinstance(item, str) or not item.strip():
                raise BuildError("facts.features entries must be text")

        source = product.get("source")
        if not isinstance(source, dict):
            raise BuildError("source must be an object")
        require_text(source, "name", "source.name")
        validated_url(require_text(source, "url", "source.url"), "source.url")
        require_text(source, "retrieved_at", "source.retrieved_at")

        article = product.get("article")
        if not isinstance(article, dict):
            raise BuildError("article must be an object")
        require_text(article, "lead", "article.lead")
        paragraphs = article.get("paragraphs")
        if not isinstance(paragraphs, list) or not paragraphs:
            raise BuildError("article.paragraphs must contain at least one paragraph")
        for paragraph in paragraphs:
            if not isinstance(paragraph, str) or not paragraph.strip():
                raise BuildError("article.paragraphs entries must be text")

        links = product.get("affiliate_links", [])
        if not isinstance(links, list):
            raise BuildError("affiliate_links must be a list")
        for index, link in enumerate(links, start=1):
            if not isinstance(link, dict):
                raise BuildError(f"affiliate_links[{index}] must be an object")
            require_text(link, "label", f"affiliate_links[{index}].label")
            validated_url(
                require_text(link, "url", f"affiliate_links[{index}].url"),
                f"affiliate_links[{index}].url",
            )

        image = product.get("image", {})
        if not isinstance(image, dict):
            raise BuildError("image must be an object")
        if image.get("src"):
            validated_url(str(image["src"]), "image.src")

        compliance = product.get("compliance")
        if not isinstance(compliance, dict):
            raise BuildError("compliance must be an object")
    except BuildError as exc:
        raise BuildError(prefix + str(exc)) from exc


def publication_blockers(product: dict) -> list[str]:
    """Return reasons a product marked for publication must not be deployed."""
    if product.get("status") != "published":
        return []

    blockers: list[str] = []
    compliance = product.get("compliance", {})
    if compliance.get("facts_verified") is not True:
        blockers.append("facts_verified is not true")
    if compliance.get("editorial_reviewed") is not True:
        blockers.append("editorial_reviewed is not true")

    if product.get("affiliate_links") and not (
        str(compliance.get("ad_disclosure", "")).strip()
    ):
        blockers.append("affiliate links require compliance.ad_disclosure")

    image = product.get("image", {})
    if image.get("src"):
        if image.get("rights_verified") is not True:
            blockers.append("external image requires image.rights_verified")
        if not str(image.get("rights_basis", "")).strip():
            blockers.append("external image requires image.rights_basis")

    automation_policy_id = str(compliance.get("automation_policy", "")).strip()
    if automation_policy_id:
        blockers.extend(automated_publication_blockers(product, automation_policy_id))

    return blockers


def automated_publication_blockers(product: dict, automation_policy_id: str) -> list[str]:
    """Enforce the narrow conditions allowed for unattended Codex publication."""
    blockers: list[str] = []
    policy = load_json(AUTOMATION_POLICY_FILE)
    if policy.get("enabled") is not True or policy.get("auto_publish") is not True:
        blockers.append("automated publication is disabled by policy")
        return blockers
    if automation_policy_id != policy.get("policy_id"):
        blockers.append("unsupported automation_policy")
        return blockers

    source = product.get("source", {})
    source_id = str(source.get("id", "")).strip()
    permitted_source = next(
        (
            item
            for item in policy.get("permitted_sources", [])
            if item.get("id") == source_id
        ),
        None,
    )
    if permitted_source is None:
        blockers.append("automated publication source is not permitted")
    source_host = urlparse(str(source.get("url", ""))).hostname
    if permitted_source is None or source_host not in permitted_source.get("hosts", []):
        blockers.append("automated publication source host is not permitted")
    if source.get("allowed_for_automation") is not True:
        blockers.append("source.allowed_for_automation is not true")

    compliance = product.get("compliance", {})
    if not str(compliance.get("automation_verified_at", "")).strip():
        blockers.append("automation_verified_at is required for automated publication")
    if not str(compliance.get("review_actor", "")).strip():
        blockers.append("review_actor is required for automated publication")

    if policy.get("allow_affiliate_links") is not True and product.get("affiliate_links"):
        blockers.append("automated publication may not include affiliate links")
    if policy.get("allow_external_images") is not True and product.get("image", {}).get("src"):
        blockers.append("automated publication may not include external images")
    return blockers


def document_head(
    site: dict,
    title: str,
    description: str,
    stylesheet_path: str,
    *,
    noindex: bool,
    canonical_path: str = "",
    og_type: str = "website",
) -> str:
    robots = '<meta name="robots" content="noindex,nofollow">\n  ' if noindex else ""
    base_url = str(site.get("base_url", "")).rstrip("/")
    canonical = ""
    if base_url and canonical_path and not noindex:
        url = f"{base_url}/{canonical_path.lstrip('/')}"
        canonical = f'\n  <link rel="canonical" href="{escape(url)}">'
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {robots}<title>{escape(title)} | {escape(site["name"])}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:title" content="{escape(title)} | {escape(site["name"])}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="{escape(og_type)}">{canonical}
  <link rel="stylesheet" href="{escape(stylesheet_path)}">
</head>"""


def header(site: dict, prefix: str) -> str:
    return f"""<header class="site-header">
  <div class="shell header-row">
    <a class="brand" href="{prefix}index.html">GADGET <span>WIRE</span> JAPAN</a>
    <nav class="navigation" aria-label="メインナビゲーション">
      <ul>
        <li><a href="{prefix}index.html">新着</a></li>
        <li><a href="{prefix}about.html">このサイトについて</a></li>
        <li><a href="{prefix}privacy.html">広告・プライバシー</a></li>
        <li><a href="{prefix}contact.html">お問い合わせ</a></li>
      </ul>
    </nav>
  </div>
</header>"""


def footer(site: dict, prefix: str) -> str:
    year = datetime.now().year
    return f"""<footer class="site-footer">
  <div class="shell footer-row">
    <span>&copy; {year} {escape(site["name"])}</span>
    <span><a href="{prefix}privacy.html">広告掲載方針・プライバシーポリシー</a></span>
  </div>
</footer>"""


def article_image(product: dict, prefix: str) -> tuple[str, str]:
    image = product.get("image", {})
    if image.get("src") and image.get("rights_verified") is True and image.get("rights_basis"):
        return str(image["src"]), str(image.get("alt") or product["product_name"])
    return f"{prefix}assets/default-product.svg", f"{product['product_name']} の製品ニュース"


def disclosure_text(product: dict, site: dict) -> str:
    specified = str(product.get("compliance", {}).get("ad_disclosure", "")).strip()
    return specified or str(site["default_disclosure"])


def render_article(product: dict, site: dict, *, draft: bool) -> str:
    prefix = "../../"
    slug = product["slug"]
    image_src, image_alt = article_image(product, prefix)
    facts = product["facts"]
    source = product["source"]
    article = product["article"]
    description = article["lead"]
    canonical = f"articles/{slug}/" if not draft else ""
    head = document_head(
        site,
        product["title"],
        description,
        f"{prefix}assets/styles.css",
        noindex=draft,
        canonical_path=canonical,
        og_type="article",
    )

    warning = ""
    if draft:
        warning = (
            '    <p class="draft-warning">下書きプレビュー：事実確認・画像利用条件・'
            "リンク確認を終えるまで公開しないでください。</p>\n"
        )

    features = "\n".join(f"<li>{escape(item)}</li>" for item in facts["features"])
    paragraphs = "\n".join(f"<p>{escape(item)}</p>" for item in article["paragraphs"])
    note = ""
    if str(article.get("editorial_note", "")).strip():
        note = f'    <p class="editorial-note">{escape(article["editorial_note"])}</p>\n'

    links = product.get("affiliate_links", [])
    links_section = ""
    if links:
        links_html = "\n".join(
            f'<li><a href="{escape(item["url"])}" rel="sponsored nofollow noopener" '
            f'target="_blank">{escape(item["label"])}</a></li>'
            for item in links
        )
        links_section = f"""    <section class="links" aria-labelledby="buy-links">
          <h2 id="buy-links">販売ページ</h2>
          <ul class="affiliate-links">{links_html}</ul>
        </section>
"""

    rights_note = ""
    image = product.get("image", {})
    if image.get("src") and image.get("rights_verified") is True:
        rights_note = (
            f"      <p>画像利用根拠：{escape(image.get('rights_basis', '確認済み素材'))}</p>\n"
        )

    return f"""{head}
<body>
{header(site, prefix)}
<main class="article-page">
  <article class="shell article-width">
    <p class="breadcrumb"><a href="{prefix}index.html">ホーム</a> / {escape(product["category"])}</p>
{warning}    <header class="article-header">
      <p class="category">{escape(product["category"])}</p>
      <h1>{escape(product["title"])}</h1>
      <p class="meta"><span>公開日：{escape(product["published_at"])}</span><span>メーカー：{escape(product["manufacturer"])}</span><span>確認日：{escape(facts["checked_at"])}</span></p>
    </header>
    <p class="disclosure">{escape(disclosure_text(product, site))}</p>
    <figure class="product-visual">
      <img src="{escape(image_src)}" alt="{escape(image_alt)}" width="1200" height="675" fetchpriority="high" decoding="async">
    </figure>
    <div class="article-copy">
      <p class="lead">{escape(article["lead"])}</p>
      {paragraphs}
    </div>
    <section class="facts" aria-labelledby="fact-heading">
      <h2 id="fact-heading">製品情報</h2>
      <dl>
        <dt>製品名</dt><dd>{escape(product["product_name"])}</dd>
        <dt>発表日</dt><dd>{escape(facts["announcement_date"])}</dd>
        <dt>発売日</dt><dd>{escape(facts["release_date"])}</dd>
        <dt>価格</dt><dd>{escape(facts["price"])}</dd>
      </dl>
      <ul>{features}</ul>
    </section>
{note}{links_section}    <section class="sources" aria-labelledby="source-heading">
      <h2 id="source-heading">出典</h2>
      <p><a href="{escape(source["url"])}" target="_blank" rel="noopener">{escape(source["name"])}</a>（取得日：{escape(source["retrieved_at"])}）</p>
{rights_note}    </section>
  </article>
</main>
{footer(site, prefix)}
</body>
</html>
"""


def render_index(products: list[dict], site: dict, *, draft: bool) -> str:
    visible = products if draft else [p for p in products if p["status"] == "published"]
    visible = sorted(visible, key=lambda item: item["published_at"], reverse=True)
    description = site["description"]
    head = document_head(
        site,
        site["tagline"],
        description,
        "assets/styles.css",
        noindex=draft,
        canonical_path="/",
    )
    preview = (
        '      <p class="draft-warning">下書きプレビュー環境です。ここに表示される記事は未公開です。</p>\n'
        if draft
        else ""
    )
    cards: list[str] = []
    for product in visible:
        src, alt = article_image(product, "")
        cards.append(
            f"""<article class="card">
          <img src="{escape(src)}" alt="{escape(alt)}" width="1200" height="675" loading="lazy" decoding="async">
          <div class="card-content">
            <p class="category">{escape(product["category"])}</p>
            <h3><a href="articles/{escape(product["slug"])}/index.html">{escape(product["title"])}</a></h3>
            <p class="summary">{escape(product["article"]["lead"])}</p>
            <time class="date" datetime="{escape(product["published_at"])}">{escape(product["published_at"])}</time>
          </div>
        </article>"""
        )
    card_output = "\n".join(cards) or (
        '<p class="empty">公開準備中です。確認が完了した製品ニュースから順次掲載します。</p>'
    )
    return f"""{head}
<body>
{header(site, "")}
<main>
  <section class="hero">
    <div class="shell hero-grid">
      <div>
        <span class="eyebrow">PRODUCT NEWS</span>
        <h1>{escape(site["tagline"])}</h1>
        <p>{escape(site["description"])}</p>
      </div>
      <img src="assets/default-product.svg" alt="" width="1200" height="675" fetchpriority="high" decoding="async">
    </div>
  </section>
  <section class="news-section">
    <div class="shell">
{preview}      <h2 class="section-heading">新着記事</h2>
      <div class="article-grid">{card_output}</div>
    </div>
  </section>
</main>
{footer(site, "")}
</body>
</html>
"""


def render_basic_page(site: dict, slug: str, title: str, body: str, *, draft: bool) -> str:
    head = document_head(
        site,
        title,
        site["description"],
        "assets/styles.css",
        noindex=draft,
        canonical_path=f"{slug}.html",
    )
    return f"""{head}
<body>
{header(site, "")}
<main class="shell basic-page">
  <h1>{escape(title)}</h1>
  {body}
</main>
{footer(site, "")}
</body>
</html>
"""


def basic_pages(site: dict, *, draft: bool) -> dict[str, str]:
    email = str(site.get("contact_email", "")).strip()
    contact_line = (
        f'<p>お問い合わせ先：<a href="mailto:{escape(email)}">{escape(email)}</a></p>'
        if email
        else "<p>お問い合わせ窓口は公開前に設定します。</p>"
    )
    return {
        "about.html": render_basic_page(
            site,
            "about",
            "このサイトについて",
            """<p>Gadget Wire Japanは、Apple製品や周辺機器を中心に、メーカー発表と正規販売情報を確認して要点を短く伝える独立メディアです。</p>
  <p>発表内容を整理する記事では、価格・発売日・対応機種などの根拠となるページを出典として明記します。実機を確認していない製品について、使用レビューであるかのような表現は行いません。</p>""",
            draft=draft,
        ),
        "privacy.html": render_basic_page(
            site,
            "privacy",
            "広告掲載方針・プライバシーポリシー",
            f"""<h2>広告について</h2>
  <p>{escape(site["default_disclosure"])}</p>
  <p>広告リンクを含む記事では、記事冒頭にも広告を含む旨を表示します。</p>
  <h2>画像と出典について</h2>
  <p>製品画像は、利用条件を確認できた素材または当サイト所有の代替画像のみを掲載します。製品情報は各記事に記載する出典を基に確認します。</p>
  <h2>アクセス解析について</h2>
  <p>アクセス解析や広告配信サービスを導入する場合は、使用するサービスとデータ取り扱いを本ページに追記します。</p>""",
            draft=draft,
        ),
        "contact.html": render_basic_page(
            site,
            "contact",
            "お問い合わせ",
            f"""<p>掲載情報の訂正依頼、画像利用に関するご連絡、広告掲載に関するお問い合わせを受け付けます。</p>
  {contact_line}""",
            draft=draft,
        ),
        "404.html": render_basic_page(
            site,
            "404",
            "ページが見つかりません",
            """<p>お探しのページは公開されていないか、移動した可能性があります。</p>
  <p><a href="index.html">新着記事ページへ戻る</a></p>""",
            draft=True,
        ),
    }


def render_sitemap(site: dict, published: list[dict]) -> str:
    base_url = str(site["base_url"]).rstrip("/")
    urls = [
        f"{base_url}/",
        f"{base_url}/about.html",
        f"{base_url}/privacy.html",
        f"{base_url}/contact.html",
    ]
    urls.extend(f"{base_url}/articles/{item['slug']}/" for item in published)
    locations = "\n".join(f"  <url><loc>{escape(url)}</loc></url>" for url in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{locations}\n"
        "</urlset>\n"
    )


def copy_assets(destination: Path) -> None:
    source = ROOT / "static" / "assets"
    shutil.copytree(source, destination / "assets", dirs_exist_ok=True)


def write_document(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def build_site() -> tuple[int, int]:
    site = load_json(ROOT / "config" / "site.json")
    for key in ("name", "tagline", "description", "publisher", "default_disclosure"):
        require_text(site, key, f"site.{key}")
    if site.get("base_url"):
        validated_url(str(site["base_url"]), "site.base_url")
    custom_domain = str(site.get("custom_domain", "")).strip()
    if custom_domain and ("/" in custom_domain or ":" in custom_domain):
        raise BuildError("site.custom_domain must be a hostname only")

    product_files = sorted((ROOT / "content" / "products").glob("*.json"))
    products: list[dict] = []
    for path in product_files:
        product = load_json(path)
        validate_product(product, path)
        blockers = publication_blockers(product)
        if blockers:
            raise BuildError(f"{path}: publication blocked: {', '.join(blockers)}")
        products.append(product)

    public_dir = ROOT / "dist"
    drafts_dir = ROOT / "build" / "drafts"
    copy_assets(public_dir)
    copy_assets(drafts_dir)

    published = [item for item in products if item["status"] == "published"]
    drafts = [item for item in products if item["status"] == "draft"]

    write_document(public_dir / "index.html", render_index(products, site, draft=False))
    write_document(drafts_dir / "index.html", render_index(drafts, site, draft=True))
    for file_name, page in basic_pages(site, draft=False).items():
        write_document(public_dir / file_name, page)
    for file_name, page in basic_pages(site, draft=True).items():
        write_document(drafts_dir / file_name, page)

    for product in published:
        write_document(
            public_dir / "articles" / product["slug"] / "index.html",
            render_article(product, site, draft=False),
        )
    for product in drafts:
        write_document(
            drafts_dir / "articles" / product["slug"] / "index.html",
            render_article(product, site, draft=True),
        )

    robots = "User-agent: *\nAllow: /\nDisallow: /pipeline/\n"
    if site.get("base_url"):
        robots += f"Sitemap: {str(site['base_url']).rstrip('/')}/sitemap.xml\n"
        write_document(public_dir / "sitemap.xml", render_sitemap(site, published))
    if custom_domain:
        write_document(public_dir / "CNAME", custom_domain + "\n")
    write_document(public_dir / ".nojekyll", "")
    write_document(public_dir / "robots.txt", robots)
    write_document(
        public_dir / "build-manifest.json",
        json.dumps(
            {"published": [p["slug"] for p in published], "draft_count": len(drafts)},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    return len(published), len(drafts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Gadget Wire Japan static site.")
    parser.parse_args()
    try:
        published, drafts = build_site()
    except BuildError as exc:
        raise SystemExit(f"Build failed: {exc}") from exc
    print(f"Built site: {published} published article(s), {drafts} draft preview(s).")
    print("Public output: dist/")
    print("Review output: build/drafts/ (never deploy this directory)")


if __name__ == "__main__":
    main()
