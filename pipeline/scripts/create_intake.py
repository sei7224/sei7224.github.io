#!/usr/bin/env python3
"""Create a draft product-news input ready for factual completion."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("slug must include ASCII letters or numbers")
    return slug


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an article intake JSON draft.")
    parser.add_argument("--product", required=True, help="Product name")
    parser.add_argument("--manufacturer", required=True, help="Manufacturer")
    parser.add_argument("--source-url", required=True, help="Official announcement URL")
    parser.add_argument("--category", default="新製品", help="Article category")
    parser.add_argument("--slug", help="ASCII article slug")
    args = parser.parse_args()

    today = date.today().isoformat()
    slug = slugify(args.slug or f"{args.manufacturer}-{args.product}")
    payload = {
        "slug": slug,
        "status": "draft",
        "title": f"{args.product}が発表、製品情報を確認中",
        "manufacturer": args.manufacturer,
        "product_name": args.product,
        "category": args.category,
        "published_at": today,
        "facts": {
            "announcement_date": "確認中",
            "release_date": "確認中",
            "price": "確認中",
            "checked_at": today,
            "features": ["公式発表の確認後に特徴を記入"]
        },
        "source": {
            "name": f"{args.manufacturer} 公式発表",
            "url": args.source_url,
            "retrieved_at": today,
            "allowed_for_automation": False
        },
        "image": {
            "src": "",
            "alt": "",
            "rights_basis": "",
            "rights_verified": False
        },
        "article": {
            "lead": "公式発表を確認して記事本文を作成します。",
            "paragraphs": ["価格、発売日、対応機種などを検証後に追記します。"],
            "editorial_note": "下書きです。確認が完了するまで公開しません。"
        },
        "affiliate_links": [],
        "compliance": {
            "ad_disclosure": "",
            "facts_verified": False,
            "editorial_reviewed": False
        }
    }
    output = ROOT / "content" / "products" / f"{slug}.json"
    if output.exists():
        raise SystemExit(f"Already exists: {output}")
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
