#!/usr/bin/env python3
"""Sync generated public pages into a GitHub Pages branch root."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


GENERATED_FILES = (
    ".nojekyll",
    "404.html",
    "CNAME",
    "about.html",
    "build-manifest.json",
    "contact.html",
    "index.html",
    "privacy.html",
    "robots.txt",
    "sitemap.xml",
)
GENERATED_DIRS = ("assets",)


class SyncError(ValueError):
    """Raised when generated output cannot safely be synchronized."""


def load_published_slugs(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SyncError(f"{path}: invalid JSON: {exc}") from exc
    if "published" not in data:
        raise SyncError(f"{path}: published is required")
    published = data["published"]
    if not isinstance(published, list) or not all(
        isinstance(slug, str) and slug for slug in published
    ):
        raise SyncError(f"{path}: published must be a list of slugs")
    return set(published)


def sync_public_root(source: Path, destination: Path) -> list[str]:
    """Copy a rendered site into the Pages root and remove unpublished articles."""
    if not source.is_dir():
        raise SyncError(f"{source}: rendered output directory does not exist")

    destination.mkdir(parents=True, exist_ok=True)
    current = load_published_slugs(source / "build-manifest.json")
    previous = load_published_slugs(destination / "build-manifest.json")
    removed: list[str] = []

    for slug in sorted(previous - current):
        article_dir = destination / "articles" / slug
        if article_dir.is_dir():
            shutil.rmtree(article_dir)
            removed.append(slug)

    for name in GENERATED_FILES:
        source_file = source / name
        if source_file.exists():
            shutil.copy2(source_file, destination / name)

    for name in GENERATED_DIRS:
        source_dir = source / name
        if source_dir.exists():
            shutil.copytree(source_dir, destination / name, dirs_exist_ok=True)

    for slug in sorted(current):
        source_article = source / "articles" / slug
        if not source_article.is_dir():
            raise SyncError(f"{source_article}: published article output is missing")
        shutil.copytree(
            source_article,
            destination / "articles" / slug,
            dirs_exist_ok=True,
        )

    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync reviewed static output to the GitHub Pages branch root."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()

    removed = sync_public_root(args.source.resolve(), args.destination.resolve())
    if removed:
        print(f"Removed unpublished articles: {', '.join(removed)}")
    print(f"Synced public site from {args.source} to {args.destination}.")


if __name__ == "__main__":
    main()
