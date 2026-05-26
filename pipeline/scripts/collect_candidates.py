#!/usr/bin/env python3
"""Collect headline-only article candidates from approved RSS/Atom sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "config" / "sources.json"
CANDIDATES_DIR = ROOT / "content" / "candidates"


def text(element: ElementTree.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def parse_entries(payload: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(payload)
    entries: list[dict[str, str]] = []
    if root.tag.endswith("rss") or root.find("channel") is not None:
        for item in root.findall("./channel/item"):
            entries.append(
                {
                    "title": text(item.find("title")),
                    "url": text(item.find("link")),
                    "published_at": text(item.find("pubDate")),
                }
            )
        return entries

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    for item in root.findall("atom:entry", namespace):
        link = item.find("atom:link", namespace)
        entries.append(
            {
                "title": text(item.find("atom:title", namespace)),
                "url": (link.get("href", "").strip() if link is not None else ""),
                "published_at": text(item.find("atom:updated", namespace)),
            }
        )
    return entries


def fetch_feed(url: str) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "GadgetWireCandidateCollector/0.1 (+headline-link-only)"},
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def candidate_id(source_id: str, url: str) -> str:
    digest = hashlib.sha256(f"{source_id}:{url}".encode("utf-8")).hexdigest()[:16]
    return f"{source_id}-{digest}"


def parsed_publication_date(value: str) -> date | None:
    if not value.strip():
        return None
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def meets_collection_start(entry: dict[str, str], source: dict) -> bool:
    cutoff = str(source.get("collect_on_or_after", "")).strip()
    if not cutoff:
        return True
    published = parsed_publication_date(entry.get("published_at", ""))
    try:
        first_date = date.fromisoformat(cutoff)
    except ValueError:
        return False
    return published is not None and published >= first_date


def matches_source(entry: dict[str, str], source: dict) -> bool:
    title = entry.get("title", "")
    keywords = source.get("keywords", [])
    required = source.get("required_phrases", [])
    excluded = source.get("excluded_phrases", [])
    folded_title = title.casefold()
    matches_keyword = not keywords or any(
        keyword.casefold() in folded_title for keyword in keywords
    )
    matches_release_phrase = not required or any(
        phrase.casefold() in folded_title for phrase in required
    )
    is_excluded = any(phrase.casefold() in folded_title for phrase in excluded)
    return (
        bool(entry.get("url"))
        and meets_collection_start(entry, source)
        and matches_keyword
        and matches_release_phrase
        and not is_excluded
    )


def collect(source: dict, payload: bytes) -> list[dict]:
    captured: list[dict] = []
    for entry in parse_entries(payload):
        if not matches_source(entry, source):
            continue
        captured.append(
            {
                "id": candidate_id(source["id"], entry["url"]),
                "state": "unreviewed",
                "headline": entry["title"],
                "url": entry["url"],
                "feed_published_at": entry["published_at"],
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "source": {
                    "id": source["id"],
                    "name": source["name"],
                    "feed_url": source["feed_url"],
                    "capture": source["capture"],
                    "automatic_article_policy": source.get("automatic_article_policy", ""),
                },
                "policy": {
                    "article_body_collected": False,
                    "image_collected": False,
                    "requires_fact_review": True,
                    "requires_image_rights_review": True,
                },
            }
        )
    return captured


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect product-news candidate links.")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without writing files.")
    args = parser.parse_args()

    config = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    written = 0
    found = 0
    for source in config.get("sources", []):
        if source.get("enabled") is not True:
            continue
        candidates = collect(source, fetch_feed(source["feed_url"]))
        found += len(candidates)
        for candidate in candidates:
            path = CANDIDATES_DIR / f"{candidate['id']}.json"
            if path.exists():
                continue
            if args.dry_run:
                print(json.dumps(candidate, ensure_ascii=False))
            else:
                CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                print(path)
            written += 1
    print(f"Candidate scan complete: {found} matched, {written} new.")


if __name__ == "__main__":
    main()
