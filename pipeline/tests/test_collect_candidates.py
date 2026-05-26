import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "collect_candidates", ROOT / "scripts" / "collect_candidates.py"
)
COLLECTOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(COLLECTOR)


RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item><title>Apple, new Mac product announced</title><link>https://example.test/mac</link><pubDate>Mon</pubDate></item>
  <item><title>Company environmental report</title><link>https://example.test/report</link><pubDate>Tue</pubDate></item>
</channel></rss>"""


class CandidateCollectorTests(unittest.TestCase):
    def test_collects_metadata_only_for_keyword_matches(self):
        source = {
            "id": "apple",
            "name": "Apple",
            "feed_url": "https://example.test/feed",
            "capture": "headline_link_date_only",
            "keywords": ["Mac"],
            "required_phrases": ["announced"],
            "excluded_phrases": ["environmental"],
        }
        candidates = COLLECTOR.collect(source, RSS)
        self.assertEqual(1, len(candidates))
        self.assertEqual("https://example.test/mac", candidates[0]["url"])
        self.assertFalse(candidates[0]["policy"]["article_body_collected"])
        self.assertFalse(candidates[0]["policy"]["image_collected"])

    def test_excludes_non_release_title_with_product_keyword(self):
        source = {
            "id": "apple",
            "name": "Apple",
            "feed_url": "https://example.test/feed",
            "capture": "headline_link_date_only",
            "keywords": ["Company"],
            "required_phrases": ["announced"],
            "excluded_phrases": ["environmental"],
        }
        self.assertEqual([], COLLECTOR.collect(source, RSS))

    def test_rss_parser_extracts_entries(self):
        entries = COLLECTOR.parse_entries(RSS)
        self.assertEqual(2, len(entries))
        self.assertEqual("Company environmental report", entries[1]["title"])


if __name__ == "__main__":
    unittest.main()
